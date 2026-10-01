"""Поиск ЛПР: директор/владелец по данным ЕГРЮЛ через DaData."""
import logging

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
        found = _post(f"{BASE}/suggest/party",
                      {"query": lead.name, "count": 10, "status": ["ACTIVE"]}, headers)
        city = lead.city.lower()
        for s in found:
            address = ((s["data"].get("address") or {}).get("value") or "").lower()
            if city and city.replace("санкт-петербург", "петербург") in address.replace("санкт-петербург", "петербург"):
                _apply(lead, s["data"], "предположительно (по названию)")
                break
    except requests.RequestException as e:
        log.warning("DaData недоступна для %s: %s", lead.name, e)
    return lead


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
