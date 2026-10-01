"""Поиск ЛПР: директор/владелец по данным ЕГРЮЛ через DaData."""
import logging
import re

import requests

from .models import Lead

log = logging.getLogger(__name__)
BASE = "https://suggestions.dadata.ru/suggestions/api/4_1/rs"

# Код региона КЛАДР: DaData ищет юрлица только в нём, иначе в выдаче тонут одноимённые фирмы со всей страны
REGIONS = {"санкт-петербург": "78", "москва": "77", "казань": "16", "екатеринбург": "66",
           "краснодар": "23", "новосибирск": "54", "нижний новгород": "52", "самара": "63"}
# Первое слово, по которому нельзя искать отдельно: найдётся любая «Клиника» города
GENERIC = {"медицинский", "медицинская", "клиника", "центр", "салон", "студия", "автосервис",
           "сервис", "авто", "красоты", "дом", "клуб", "family", "the", "beauty", "studio"}
ADDRESS_STOP = {"санкт", "петербург", "москва", "улица", "проспект", "литера", "литер", "помещ",
                "помещение", "комната", "муниципальный", "округ", "город", "набережная", "переулок",
                "шоссе", "бульвар", "внутригородская", "территория", "этаж", "корпус", "строение",
                "федерального", "значения", "муниципального", "образования", "район", "область"}
LATIN = [("shch", "щ"), ("sch", "щ"), ("zh", "ж"), ("kh", "х"), ("ts", "ц"), ("ch", "ч"), ("sh", "ш"),
         ("yu", "ю"), ("ya", "я"), ("yo", "е"), ("ck", "к"), ("ph", "ф"), ("th", "т"), ("oo", "у"),
         ("ee", "и"), ("x", "кс"), ("w", "в"), ("q", "к"), ("a", "а"), ("b", "б"), ("c", "к"), ("d", "д"),
         ("e", "е"), ("f", "ф"), ("g", "г"), ("h", "х"), ("i", "и"), ("j", "дж"), ("k", "к"), ("l", "л"),
         ("m", "м"), ("n", "н"), ("o", "о"), ("p", "п"), ("r", "р"), ("s", "с"), ("t", "т"), ("u", "у"),
         ("v", "в"), ("y", "и"), ("z", "з")]


def find_lpr(lead: Lead, api_key: str, okved: tuple[str, ...] = ()) -> Lead:
    """Если на сайте нашёлся ИНН — ищем точно по нему. Иначе перебираем юрлица с похожим
    названием в регионе и выбираем то, у которого совпадает адрес и вид деятельности (ОКВЭД)."""
    headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
    try:
        if lead.inn:
            found = _post(f"{BASE}/findById/party", {"query": lead.inn}, headers)
            if found:
                _apply(lead, found[0]["data"], "точно (ИНН с сайта)")
                return lead
        region = REGIONS.get(lead.city.lower().strip())
        best = None
        for query, full in _queries(_brand(lead.name)):
            body = {"query": query, "count": 20, "status": ["ACTIVE"]}
            if region:
                body["locations"] = [{"kladr_id": region}]
            for s in _post(f"{BASE}/suggest/party", body, headers):
                score, by_address = _match(lead, s, query, full, okved)
                if score and (best is None or score > best[0]):
                    best = (score, s["data"], by_address)
        if best:
            _apply(lead, best[1], "вероятно (название и адрес)" if best[2]
                   else "предположительно (название и вид деятельности)")
    except requests.RequestException as e:
        log.warning("DaData недоступна для %s: %s", lead.name, e)
    return lead


def _brand(name: str) -> str:
    """'Династия, медицинский центр' -> 'Династия': в ЕГРЮЛ нет вида деятельности из 2ГИС."""
    return name.split(",")[0].strip()


def _queries(brand: str) -> list[tuple[str, bool]]:
    """Варианты запроса. Второе значение: True — это бренд целиком, False — только первое слово."""
    out = [(brand, True)]
    if re.search(r"[a-zA-Z]", brand):
        out.append((_cyr(brand), True))                # Cosmopro -> космопро (ООО «КОСМО-ПРО»)
    first = brand.split()[0] if len(brand.split()) > 1 else ""
    if len(_norm(first)) >= 4 and first.lower() not in GENERIC:
        out.append((first, False))                     # «Прагматика Купчино» -> «Прагматика»
        if re.search(r"[a-zA-Z]", first):
            out.append((_cyr(first), False))
    return list(dict.fromkeys(out))


def _match(lead: Lead, s: dict, query: str, full: bool, okved: tuple[str, ...]) -> tuple[int, bool]:
    """Оценка кандидата. 0 — не подходит. Частичное совпадение названия без адреса не принимаем:
    так «Клиника Пирогова» не привяжется к случайному ООО «Клиника»."""
    data = s["data"]
    address = ((data.get("address") or {}).get("value") or "")
    if _city_key(lead.city) not in _city_key(address):
        return 0, False
    legal, key = _norm((data.get("name") or {}).get("short") or s.get("value") or ""), _norm(query)
    name = 2 if legal == key else (1 if len(key) >= 4 and (key in legal or legal in key) else 0)
    by_kind = bool(okved) and (data.get("okved") or "").startswith(okved)
    by_address = _same_address(lead.address, address)
    if by_address and (name or by_kind):
        ok = True
    elif full and name == 2 and by_kind:
        ok = True
    else:
        ok = False
    return (name * 2 + by_kind * 2 + by_address * 3 + full) if ok else 0, by_address


def _same_address(a: str, b: str) -> bool:
    """Та же улица и тот же номер дома: 'улица Ленина, 5' и 'ул Ленина, д 5 литера б'."""
    words_a, nums_a = _address_parts(a)
    words_b, nums_b = _address_parts(b)
    return bool(words_a & words_b) and bool(nums_a) and nums_a[0] in nums_b


def _address_parts(text: str) -> tuple[set[str], list[str]]:
    text = text.lower().replace("ё", "е")
    words = {w for w in re.findall(r"[а-я]{4,}", text) if w not in ADDRESS_STOP}
    return words, re.findall(r"\b\d{1,3}\b", text)


def _cyr(text: str) -> str:
    text = text.lower()
    for lat, cyr in LATIN:
        text = text.replace(lat, cyr)
    return text


def _norm(text: str) -> str:
    return re.sub(r"[^0-9a-zа-я]", "", text.lower().replace("ё", "е"))


def _city_key(text: str) -> str:
    return text.lower().replace("ё", "е").replace("санкт-петербург", "петербург")


def _post(url: str, body: dict, headers: dict) -> list:
    resp = requests.post(url, json=body, headers=headers, timeout=15)
    if resp.status_code != 200:
        log.warning("DaData ответила %s: %s", resp.status_code, resp.text[:200])
        return []
    return resp.json().get("suggestions", [])


def _apply(lead: Lead, data: dict, confidence: str) -> None:
    lead.inn = data.get("inn") or lead.inn
    lead.legal_name = (data.get("name") or {}).get("short_with_opf") or ""
    mgmt = data.get("management") or {}
    if mgmt.get("name"):
        lead.lpr_name, lead.lpr_post = mgmt["name"], (mgmt.get("post") or "Руководитель").capitalize()
    elif data.get("type") == "INDIVIDUAL":
        fio = data.get("fio") or {}
        lead.lpr_name = " ".join(x for x in (fio.get("surname"), fio.get("name"), fio.get("patronymic")) if x)
        lead.lpr_post = "Индивидуальный предприниматель"
    lead.site_facts["lpr_confidence"] = confidence if lead.lpr_name else ""
