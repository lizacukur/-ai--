"""Поиск сайта компании, когда карты его не отдали (например, на демо-ключе 2ГИС).

Перебираем вероятные адреса по названию (dinastiya-spb.ru, takihodi.ru…) и принимаем сайт,
только если на нём та же улица, что в карточке на карте: иначе легко попасть на одноимённую
фирму из другого города. Заодно забираем ИНН со страницы контактов — по нему ЛПР находится точно.
"""
import re

import requests

from .audit import HEADERS, INN_RE
from .enrich import _address_parts, _brand
from .models import Lead

CYR = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
               ["a", "b", "v", "g", "d", "e", "e", "zh", "z", "i", "y", "k", "l", "m", "n", "o", "p", "r",
                "s", "t", "u", "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "ya"]))
# Домен города: dinastiya-spb.ru, osnova.spb.ru
CITY_SUFFIX = {"санкт-петербург": "spb", "москва": "msk", "казань": "kzn", "екатеринбург": "ekb",
               "краснодар": "krd", "новосибирск": "nsk"}
CONTACT_PAGES = ("", "/contacts", "/contacts/", "/kontakty", "/kontakty/", "/contact")
# Где обычно лежат реквизиты: у клиник они обязательны рядом с лицензией
REQUISITE_PAGES = ("/rekvizity", "/requisites", "/about", "/o-nas", "/o-klinike", "/license",
                   "/licenzii", "/documents", "/dokumenty", "/svedeniya", "/info", "/legal")


def find_site(lead: Lead, timeout: int = 8) -> Lead:
    if lead.website:
        return lead
    street = _street_words(lead.address)
    if not street:
        return lead
    for domain in candidates(_brand(lead.name), lead.city):
        url = f"https://{domain}"
        home = _get(url, timeout)
        if home is None or _norm(_latin(_brand(lead.name)))[:5] not in _norm(_latin(home)):
            continue
        for page in CONTACT_PAGES:
            text = home if page == "" else _get(url + page, timeout)
            if text and street & _address_parts(text)[0]:
                lead.website = url
                lead.site_facts["site_found_by"] = "подобран по названию, адрес совпал"
                if not lead.inn:
                    lead.inn = find_inn(url, [home, text], timeout)
                return lead
    return lead


def find_inn(url: str, pages: list[str], timeout: int = 8) -> str:
    """ИНН с уже скачанных страниц, иначе со страниц реквизитов и лицензий."""
    for text in pages:
        m = INN_RE.search(text or "")
        if m:
            return m.group(1)
    for page in REQUISITE_PAGES:
        m = INN_RE.search(_get(url + page, timeout) or "")
        if m:
            return m.group(1)
    return ""


def candidates(brand: str, city: str) -> list[str]:
    """'Так и ходи' -> takihodi.ru, tak-i-hodi.ru, takihodi-spb.ru…"""
    lat = _latin(brand)
    words = re.findall(r"[a-z0-9]+", lat)
    if not words:
        return []
    bases = ["".join(words), "-".join(words)]
    if len(words) > 1 and len(words[0]) >= 4:
        bases.append(words[0])
    suffix = CITY_SUFFIX.get(city.lower().strip(), "")
    out = []
    for b in dict.fromkeys(bases):
        if len(b) < 4:  # aaa.ru, m3.ru — почти всегда чужие
            continue
        out += [f"{b}.ru", f"{b}.com"]
        if suffix:
            out += [f"{b}-{suffix}.ru", f"{b}{suffix}.ru", f"{b}.{suffix}.ru"]
    return out


def _street_words(address: str) -> set[str]:
    """Только название улицы: город в адресе есть на любом сайте этого города."""
    parts = [p for p in address.split(",")[1:] if re.search(r"[а-яА-Я]{4,}", p)]
    return _address_parts(parts[0])[0] if parts else set()


def _get(url: str, timeout: int) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
    except requests.RequestException:
        return None
    if not resp.ok:
        return None
    resp.encoding = resp.apparent_encoding or resp.encoding
    return resp.text


def _latin(text: str) -> str:
    return "".join(CYR.get(c, c) for c in text.lower())


def _norm(text: str) -> str:
    return re.sub(r"[^0-9a-z]", "", text.lower())
