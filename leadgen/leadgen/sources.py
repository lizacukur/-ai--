"""Откуда берём компании: 2ГИС, Яндекс Карты или ваш собственный CSV-файл."""
import csv
import logging

import requests

from .contacts import normalize_phone, unique
from .models import Lead

log = logging.getLogger(__name__)
HTTP = requests.Session()
HTTP.headers["User-Agent"] = "Mozilla/5.0 (leadgen)"


def search_2gis(api_key: str, query: str, city: str, niche: str, limit: int) -> list[Lead]:
    """2ГИС Places API (catalog.api.2gis.com). Даёт телефоны, сайты, мессенджеры, рейтинг."""
    leads: list[Lead] = []
    page = 1
    while len(leads) < limit:
        resp = HTTP.get(
            "https://catalog.api.2gis.com/3.0/items",
            params={
                "key": api_key,
                "q": f"{query} {city}",
                "type": "branch",
                "page": page,
                "page_size": 10,
                "locale": "ru_RU",
                "fields": "items.contact_groups,items.reviews,items.org,items.full_address_name",
            },
            timeout=20,
        )
        data = resp.json()
        code = data.get("meta", {}).get("code")
        if code != 200:
            if code != 404:  # 404 = результатов больше нет
                log.warning("2ГИС ответил %s: %s", code, data.get("meta", {}).get("error"))
            break
        items = data.get("result", {}).get("items", [])
        if not items:
            break
        leads += [_lead_from_2gis(it, city, niche) for it in items]
        page += 1
    return leads[:limit]


def _lead_from_2gis(item: dict, city: str, niche: str) -> Lead:
    lead = Lead(
        name=item.get("name", ""),
        city=city,
        niche=niche,
        address=item.get("full_address_name") or item.get("address_name", ""),
        source="2ГИС",
        branches=(item.get("org") or {}).get("branch_count") or 1,
    )
    reviews = item.get("reviews") or {}
    if reviews.get("general_rating"):
        lead.rating = float(reviews["general_rating"])
    lead.reviews = reviews.get("general_review_count")

    for group in item.get("contact_groups") or []:
        for c in group.get("contacts") or []:
            kind, value = c.get("type"), c.get("value") or ""
            text, url = c.get("text") or "", c.get("url") or ""
            if kind == "phone":
                lead.phones.append(normalize_phone(value))
            elif kind == "email":
                lead.emails.append(value.lower())
            elif kind == "website" and not lead.website:
                # 2ГИС оборачивает ссылки в link.2gis.ru, настоящий адрес лежит в text
                site = text if "2gis" in (url or value) else (url or value or text)
                lead.website = site if site.startswith("http") else f"http://{site}"
            elif kind == "whatsapp":
                lead.whatsapp.append(normalize_phone(value) or normalize_phone(text))
            elif kind == "telegram":
                lead.telegram.append(text or value)
            elif kind == "vkontakte" and not lead.vk:
                lead.vk = text or value
    lead.phones = unique(lead.phones)
    lead.whatsapp = unique(lead.whatsapp)
    lead.telegram = unique(lead.telegram)
    return lead


def search_yandex(api_key: str, query: str, city: str, niche: str, limit: int) -> list[Lead]:
    """Яндекс «API Поиска по организациям» (search-maps.yandex.ru). Даёт телефоны и сайт."""
    leads: list[Lead] = []
    skip = 0
    while len(leads) < limit:
        resp = HTTP.get(
            "https://search-maps.yandex.ru/v1/",
            params={
                "apikey": api_key,
                "text": f"{query} {city}",
                "type": "biz",
                "lang": "ru_RU",
                "results": min(50, limit - len(leads)),
                "skip": skip,
            },
            timeout=20,
        )
        if resp.status_code != 200:
            log.warning("Яндекс ответил %s: %s", resp.status_code, resp.text[:200])
            break
        features = resp.json().get("features", [])
        if not features:
            break
        for f in features:
            meta = f.get("properties", {}).get("CompanyMetaData", {})
            site = meta.get("url", "")
            leads.append(Lead(
                name=meta.get("name", ""),
                city=city,
                niche=niche,
                address=meta.get("address", ""),
                source="Яндекс",
                website=site if not site or site.startswith("http") else f"http://{site}",
                phones=unique(normalize_phone(p.get("formatted", "")) for p in meta.get("Phones", [])),
            ))
        skip += len(features)
    return leads[:limit]


def load_csv(path: str) -> list[Lead]:
    """Свой список. Колонки (любые из): name, city, niche, website, phone, email."""
    leads = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            row = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
            site = row.get("website") or row.get("сайт", "")
            if site and not site.startswith("http"):
                site = "http://" + site
            phone = normalize_phone(row.get("phone") or row.get("телефон", ""))
            leads.append(Lead(
                name=row.get("name") or row.get("название") or site,
                city=row.get("city") or row.get("город", ""),
                niche=row.get("niche") or row.get("ниша", ""),
                website=site,
                phones=[phone] if phone else [],
                emails=[row["email"]] if row.get("email") else [],
                source="CSV",
            ))
    return leads
