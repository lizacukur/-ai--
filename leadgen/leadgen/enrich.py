"""Поиск ЛПР: директор/владелец по данным ЕГРЮЛ через DaData."""
import logging
import re

import requests

from .models import Lead

log = logging.getLogger(__name__)
BASE = "https://suggestions.dadata.ru/suggestions/api/4_1/rs"


def find_lpr(lead: Lead, api_key: str) -> Lead:
    """Если на сайте нашёлся ИНН — ищем точно по нему, иначе по названию и городу."""
    headers = {"Authorization": f"Token {api_key}", "Content-Type": "application/json"}
    try:
        if lead.inn:
            found = _post(f"{BASE}/findById/party", {"query": lead.inn}, headers)
            if found:
                _apply(lead, found[0]["data"], "точно (ИНН с сайта)")
                return lead
        brand = _brand(lead.name)
        found = _post(f"{BASE}/suggest/party",
                      {"query": brand, "count": 10, "status": ["ACTIVE"]}, headers)
        city = _city_key(lead.city)
        key = _norm(brand)
        for s in found:
            address = _city_key((s["data"].get("address") or {}).get("value") or "")
            legal = _norm((s["data"].get("name") or {}).get("short") or s.get("value") or "")
            if city and city in address and key and (key in legal or legal in key):
                _apply(lead, s["data"], "предположительно (по названию)")
                break
    except requests.RequestException as e:
        log.warning("DaData недоступна для %s: %s", lead.name, e)
    return lead


def _brand(name: str) -> str:
    """'Династия, медицинский центр' -> 'Династия': в ЕГРЮЛ нет вида деятельности из 2ГИС."""
    return name.split(",")[0].strip()


def _norm(text: str) -> str:
    return re.sub(r"[^0-9a-zа-яё]", "", text.lower().replace("ё", "е"))


def _city_key(text: str) -> str:
    return text.lower().replace("санкт-петербург", "петербург")


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
