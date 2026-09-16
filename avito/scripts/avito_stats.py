#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Выгрузка статистики объявлений Avito через официальное API.

Требует платного тарифа на аккаунте Avito — без него раздела API в кабинете нет.
Если тарифа нет, цифры заносятся руками: см. manual_stats.py.

Что делает:
  1. получает токен по client_id / client_secret,
  2. забирает все объявления кабинета,
  3. тянет статистику (просмотры, контакты, избранное) за период,
  4. считает конверсию «просмотр → контакт» по каждому объявлению,
  5. складывает результат в avito/out/: CSV, сырой JSON и отчёт report.md.

Запуск:
    python3 avito/scripts/avito_stats.py
    python3 avito/scripts/avito_stats.py --days 90

Зависимости: только стандартная библиотека Python 3.8+.
"""

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import report  # noqa: E402

API = "https://api.avito.ru"
OUT = pathlib.Path(__file__).resolve().parent / "out"

# Avito ограничивает запрос статистики: не больше 200 объявлений и 270 дней за раз.
MAX_IDS_PER_REQUEST = 200
MAX_DAYS = 270


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

def _request(method, path, token=None, body=None, form=None, params=None):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)

    headers = {"Accept": "application/json"}
    data = None

    if form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif body is not None:
        data = json.dumps(body, ensure_ascii=False).encode()
        headers["Content-Type"] = "application/json"

    if token:
        headers["Authorization"] = "Bearer " + token

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        raise SystemExit(
            "Avito API ответило {} на {} {}\n{}".format(e.code, method, path, detail)
        )
    except urllib.error.URLError as e:
        raise SystemExit("Не удалось достучаться до Avito API: {}".format(e.reason))


# --------------------------------------------------------------------------
# Учётные данные
# --------------------------------------------------------------------------

def load_credentials():
    """Читает ключи из переменных окружения или из avito/scripts/.env (в git не попадает)."""
    env_file = pathlib.Path(__file__).resolve().parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

    client_id = os.environ.get("AVITO_CLIENT_ID")
    client_secret = os.environ.get("AVITO_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise SystemExit(
            "Не найдены ключи доступа.\n"
            "Создай файл avito/scripts/.env с двумя строками:\n"
            "  AVITO_CLIENT_ID=твой_client_id\n"
            "  AVITO_CLIENT_SECRET=твой_client_secret\n"
            "Где взять: avito.ru -> Профиль -> Настройки -> раздел API -> создать приложение."
        )
    return client_id, client_secret


def get_token(client_id, client_secret):
    data = _request("POST", "/token/", form={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    })
    token = data.get("access_token")
    if not token:
        raise SystemExit("Токен не получен. Ответ Avito: {}".format(data))
    return token


# --------------------------------------------------------------------------
# Данные
# --------------------------------------------------------------------------

def get_account(token):
    return _request("GET", "/core/v1/accounts/self", token=token)


def get_items(token):
    """Забирает все объявления постранично."""
    items, page = [], 1
    while True:
        data = _request("GET", "/core/v1/items", token=token,
                        params={"per_page": 100, "page": page})
        chunk = data.get("resources") or data.get("items") or []
        items.extend(chunk)
        meta = data.get("meta") or {}
        pages = meta.get("pages")
        if not chunk or (pages and page >= pages) or len(chunk) < 100:
            break
        page += 1
    return items


def get_stats(token, user_id, item_ids, date_from, date_to):
    """Статистика по объявлениям. Возвращает (сырой ответ, агрегат по item_id)."""
    raw, totals = [], {}
    for i in range(0, len(item_ids), MAX_IDS_PER_REQUEST):
        batch = item_ids[i:i + MAX_IDS_PER_REQUEST]
        data = _request(
            "POST", "/stats/v1/accounts/{}/items".format(user_id), token=token,
            body={
                "dateFrom": date_from,
                "dateTo": date_to,
                "fields": ["uniqViews", "uniqContacts", "uniqFavorites"],
                "itemIds": batch,
                "periodGrouping": "day",
            },
        )
        raw.append(data)
        result = data.get("result") or {}
        for entry in result.get("items", []):
            item_id = entry.get("itemId") or entry.get("item_id")
            agg = totals.setdefault(item_id, {"views": 0, "contacts": 0, "favorites": 0, "days": 0})
            for day in entry.get("stats", []):
                agg["views"] += day.get("uniqViews", day.get("uniq_views", 0)) or 0
                agg["contacts"] += day.get("uniqContacts", day.get("uniq_contacts", 0)) or 0
                agg["favorites"] += day.get("uniqFavorites", day.get("uniq_favorites", 0)) or 0
                agg["days"] += 1
    return raw, totals


# --------------------------------------------------------------------------
# Отчёт
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Выгрузка статистики объявлений Avito")
    parser.add_argument("--days", type=int, default=60,
                        help="за сколько дней тянуть статистику (по умолчанию 60, максимум 270)")
    args = parser.parse_args()

    days = min(max(args.days, 1), MAX_DAYS)
    date_to = dt.date.today()
    date_from = date_to - dt.timedelta(days=days)

    client_id, client_secret = load_credentials()

    print("Получаю токен...")
    token = get_token(client_id, client_secret)

    print("Читаю кабинет...")
    account = get_account(token)
    user_id = account.get("id")
    print("  кабинет: {} (id {})".format(account.get("name", "—"), user_id))

    print("Забираю объявления...")
    items = get_items(token)
    print("  найдено объявлений: {}".format(len(items)))
    if not items:
        raise SystemExit("В кабинете нет объявлений — или у ключа нет нужных прав.")

    titles = {}
    for it in items:
        item_id = it.get("id")
        titles[item_id] = it.get("title") or it.get("url") or str(item_id)

    print("Тяну статистику за {} дней...".format(days))
    raw, totals = get_stats(token, user_id, list(titles.keys()),
                            date_from.isoformat(), date_to.isoformat())

    raw_rows = [{
        "title": titles.get(item_id, str(item_id)),
        "views": agg["views"],
        "contacts": agg["contacts"],
        "favorites": agg["favorites"],
        "spend": 0,
    } for item_id, agg in totals.items()]

    rows = report.build_rows(raw_rows)
    stamp = date_to.isoformat()

    text = report.build_report(
        rows,
        title_line="**Кабинет:** {}".format(account.get("name") or account.get("id")),
        period_line="**Период:** {} — {}".format(date_from.isoformat(), date_to.isoformat()),
    )
    report_path, csv_path = report.write_outputs(OUT, stamp, rows, text)

    raw_path = OUT / "avito_raw_{}.json".format(stamp)
    raw_path.write_text(
        json.dumps({"account": account, "items": items, "stats": raw},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\nГотово. Файлы:")
    for p in (report_path, csv_path, raw_path):
        print("  {}".format(p))
    print("\nПришли мне report_*.md и avito_raw_*.json — разберу цифры и соберу план.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
