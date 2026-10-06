"""Скачивает чаты Avito за 90 дней и сохраняет их в JSON-файл данных панели.

Запуск: python3 refresh_inbox.py <куда-сохранить.json>
Ключи берутся из AVITO_CLIENT_ID и AVITO_CLIENT_SECRET. Только чтение: сообщения не отправляются.
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

WINDOW_DAYS = 90
MAX_PAGES = 20


def call(req, timeout=60):
    last = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:300]
            if e.code == 429:
                time.sleep(4 * (attempt + 1))
                last = f"429 {body}"
                continue
            raise SystemExit(f"Avito ответил {e.code}: {body}")
        except Exception as e:
            last = str(e)
            time.sleep(2 * (attempt + 1))
    raise SystemExit(f"Нет связи с Avito: {last}")


def get_token():
    cid = os.environ.get("AVITO_CLIENT_ID")
    sec = os.environ.get("AVITO_CLIENT_SECRET")
    if not cid or not sec:
        raise SystemExit("Не заданы AVITO_CLIENT_ID и AVITO_CLIENT_SECRET в окружении")
    data = urllib.parse.urlencode(
        {"grant_type": "client_credentials", "client_id": cid, "client_secret": sec}
    ).encode()
    req = urllib.request.Request(
        "https://api.avito.ru/token/", data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    res = call(req, 40)
    if "access_token" not in res:
        raise SystemExit(f"Токен не получен: {res}")
    return res["access_token"]


def main():
    out = sys.argv[1]
    headers = {"Authorization": "Bearer " + get_token()}

    def get(url):
        return call(urllib.request.Request(url, headers=headers))

    uid = get("https://api.avito.ru/core/v1/accounts/self")["id"]
    now = int(time.time())
    cutoff = now - WINDOW_DAYS * 86400

    items, offset = [], 0
    for _ in range(MAX_PAGES):
        page = get(f"https://api.avito.ru/messenger/v2/accounts/{uid}/chats?limit=100&offset={offset}")
        chats = page.get("chats") or []
        if not chats:
            break
        fresh = 0
        for c in chats:
            lm = c.get("last_message") or {}
            ts = lm.get("created")
            if not ts or ts < cutoff:
                continue
            fresh += 1
            ctx = (c.get("context") or {}).get("value") or {}
            text = ((lm.get("content") or {}).get("text") or "").replace("\n", " ").strip()
            if not text:
                text = "[" + str(lm.get("type")) + "]"
            direction = lm.get("direction")
            buyer = next((u.get("name") for u in c.get("users", []) if u.get("id") != uid), "") or "—"
            items.append({
                "id": c["id"],
                "ts": int(ts),
                "buyer": buyer[:40],
                "city": ((ctx.get("location") or {}).get("title") or "—")[:30],
                "item": (ctx.get("title") or "—")[:55],
                "text": text[:180],
                "dir": direction,
                "readByMe": bool(lm.get("read")) if direction == "in" else None,
                "readByThem": bool(lm.get("read")) if direction == "out" else None,
                "url": ctx.get("url", ""),
            })
        offset += len(chats)
        if not (page.get("meta") or {}).get("has_more") or fresh == 0:
            break
        time.sleep(1.5)

    items.sort(key=lambda x: -x["ts"])
    seed = {"items": items, "syncedAt": now}
    open(out, "w", encoding="utf-8").write(json.dumps(seed, ensure_ascii=False, separators=(",", ":")))

    unread = sum(1 for i in items if i["dir"] == "in" and not i["readByMe"])
    noreply = sum(1 for i in items if i["dir"] == "in" and i["readByMe"])
    print(f"OK: чатов {len(items)}, не открыто вами {unread}, без ответа {noreply}, размер файла {os.path.getsize(out)} байт")


main()
