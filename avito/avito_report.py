#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Разбор объявлений Avito — один файл, ничего ставить не нужно.

Запуск:
    python3 avito_report.py

Спросит ключи (кабинет Avito -> Настройки -> Avito API), сходит за статистикой
и напечатает разбор. Он же сохранится рядом в файл avito_otchet.txt —
этот файл можно целиком отправить в чат.

Проверить, как выглядит отчёт, без обращения к Avito:
    python3 avito_report.py --demo
"""

import datetime as dt
import getpass
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.avito.ru"
MIN_VIEWS = 30
OUT_FILE = "avito_otchet.txt"


def http(method, path, token=None, body=None, form=None, params=None):
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
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        if e.code == 403:
            raise SystemExit(
                "Avito отказал в доступе (403).\n"
                "Обычно это значит, что у ключа нет прав или на аккаунте нет платного тарифа.\n"
                "Ответ: " + detail
            )
        if e.code == 401:
            raise SystemExit("Ключи не подошли (401). Проверь client_id и client_secret.\n" + detail)
        raise SystemExit("Avito ответил {} на {}\n{}".format(e.code, path, detail))
    except urllib.error.URLError as e:
        raise SystemExit("Не получилось связаться с Avito: {}".format(e.reason))


def verdict(views, contacts, median_views):
    if views < MIN_VIEWS:
        return "мало показов — данных не хватает, выводы делать рано"
    cr = contacts / views * 100
    if cr < 2:
        return "ТРАФИК ЕСТЬ, НО НЕ ПИШУТ — переписать заголовок, первое фото и первые строки"
    if cr < 5:
        return "середина — текст рабочий, оффер можно докрутить"
    if views < median_views:
        return "ПОБЕДИТЕЛЬ, но его мало видят — сюда продвижение в первую очередь"
    return "ПОБЕДИТЕЛЬ — масштабировать: похожие объявления и продвижение"


def make_report(account, rows, date_from, date_to):
    views = sum(r["views"] for r in rows)
    contacts = sum(r["contacts"] for r in rows)
    favs = sum(r["favorites"] for r in rows)
    cr = contacts / views * 100 if views else 0

    L = []
    add = L.append
    add("=" * 64)
    add("РАЗБОР ОБЪЯВЛЕНИЙ AVITO")
    add("=" * 64)
    add("Кабинет: {}".format(account.get("name") or account.get("id")))
    add("Период:  {} — {}".format(date_from, date_to))
    add("")
    add("ИТОГО")
    add("  просмотров            {}".format(views))
    add("  обращений             {}".format(contacts))
    add("  в избранном           {}".format(favs))
    add("  конверсия в обращение {:.2f}%   (норма для обучения 3-8%)".format(cr))
    add("")
    add("ПО ОБЪЯВЛЕНИЯМ (от большего числа просмотров)")
    add("-" * 64)
    for r in rows:
        crs = "{:.2f}%".format(r["contacts"] / r["views"] * 100) if r["views"] else "—"
        add("")
        add("  {}".format(r["title"]))
        add("    просмотры {:<7} обращения {:<6} конверсия {:<8} избранное {}".format(
            r["views"], r["contacts"], crs, r["favorites"]))
        add("    -> {}".format(r["verdict"]))
    add("")
    add("-" * 64)
    add("Отправь этот файл в чат — разберём, что менять.")
    return "\n".join(L)


DEMO = {
    "account": {"id": 123456, "name": "Демо-кабинет"},
    "items": [
        (1, "Обучение ChatGPT с нуля — практика на задачах", 890, 48, 61),
        (2, "Нейросети для бизнеса — обучение под ваши задачи", 1240, 15, 22),
        (3, "Нейрофото и нейровидео — научу делать самой", 430, 9, 18),
        (4, "Автоматизация бизнеса с ИИ — обучение команды", 95, 7, 4),
        (5, "Обучение AI-контенту: Reels, фото, видео", 12, 1, 0),
    ],
}


def main():
    demo = "--demo" in sys.argv
    date_to = dt.date.today()
    date_from = date_to - dt.timedelta(days=60)

    if demo:
        account = DEMO["account"]
        raw = [{"title": t, "views": v, "contacts": c, "favorites": f}
               for _, t, v, c, f in DEMO["items"]]
    else:
        cid = os.environ.get("AVITO_CLIENT_ID") or input("client_id: ").strip()
        secret = os.environ.get("AVITO_CLIENT_SECRET") or getpass.getpass("client_secret (не отображается): ").strip()
        if not cid or not secret:
            raise SystemExit("Без ключей не получится.")

        print("\nПолучаю доступ...")
        token = http("POST", "/token/", form={
            "grant_type": "client_credentials", "client_id": cid, "client_secret": secret,
        }).get("access_token")
        if not token:
            raise SystemExit("Токен не пришёл. Проверь ключи.")

        account = http("GET", "/core/v1/accounts/self", token=token)
        user_id = account.get("id")
        print("Кабинет: {}".format(account.get("name") or user_id))

        print("Забираю объявления...")
        items, page = [], 1
        while True:
            d = http("GET", "/core/v1/items", token=token, params={"per_page": 100, "page": page})
            chunk = d.get("resources") or d.get("items") or []
            items += chunk
            if len(chunk) < 100:
                break
            page += 1
        print("  найдено: {}".format(len(items)))
        if not items:
            raise SystemExit("В кабинете нет объявлений, либо у ключа нет к ним доступа.")

        titles = {i.get("id"): (i.get("title") or str(i.get("id"))) for i in items}
        ids = list(titles)

        print("Считаю статистику за 60 дней...")
        totals = {}
        for i in range(0, len(ids), 200):
            d = http("POST", "/stats/v1/accounts/{}/items".format(user_id), token=token, body={
                "dateFrom": date_from.isoformat(), "dateTo": date_to.isoformat(),
                "fields": ["uniqViews", "uniqContacts", "uniqFavorites"],
                "itemIds": ids[i:i + 200], "periodGrouping": "day",
            })
            for e in (d.get("result") or {}).get("items", []):
                iid = e.get("itemId") or e.get("item_id")
                a = totals.setdefault(iid, [0, 0, 0])
                for day in e.get("stats", []):
                    a[0] += day.get("uniqViews", 0) or 0
                    a[1] += day.get("uniqContacts", 0) or 0
                    a[2] += day.get("uniqFavorites", 0) or 0

        raw = [{"title": titles.get(k, str(k)), "views": v[0], "contacts": v[1], "favorites": v[2]}
               for k, v in totals.items()]

    if not raw:
        raise SystemExit("Статистика пустая — возможно, объявления слишком новые.")

    counts = sorted(r["views"] for r in raw)
    median = counts[len(counts) // 2]
    for r in raw:
        r["verdict"] = verdict(r["views"], r["contacts"], median)
    raw.sort(key=lambda r: r["views"], reverse=True)

    text = make_report(account, raw, date_from.isoformat(), date_to.isoformat())
    print("\n" + text)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(text)
    print("\nСохранено в файл: {}".format(os.path.abspath(OUT_FILE)))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
