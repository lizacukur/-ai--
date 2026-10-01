"""Проверка сайта компании: что с ним не так и какие контакты на нём есть."""
import datetime
import re
import time

import requests
from bs4 import BeautifulSoup

from .contacts import find_emails, find_phones, normalize_phone, unique
from .models import Lead

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}

BOOKING = ("yclients", "dikidi", "sonline", "medesk", "prodoctorov", "napopravku", "arnica",
           "booking", "онлайн-запис", "онлайн запис", "записаться онлайн", "1c-fitness", "mobifitness")
CHAT = ("jivo", "jivosite", "envybox", "callbackhunter", "b24-widget", "bitrix24", "chatra",
        "talk-me", "carrotquest", "livetex", "wazzup", "umnico", "re:plain", "replain")
BUILDERS = {"tilda": "Tilda", "wix.com": "Wix", "ukit": "uKit", "nethouse": "Nethouse",
            "flexbe": "Flexbe", "lpgenerator": "LPgenerator", "wordpress": "WordPress",
            "bitrix": "1С-Битрикс", "joomla": "Joomla"}
INN_RE = re.compile(r"ИНН(?:\s*/\s*КПП)?[\s:№]*?(\d{10}|\d{12})\b")
YEAR_RE = re.compile(r"(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–—]\s*)?(20\d{2})", re.I)


def audit_site(lead: Lead, timeout: int = 12) -> Lead:
    """Заполняет lead.site_issues / site_facts и дополняет контакты с сайта."""
    if not lead.website:
        lead.site_issues.append("Нет сайта")
        lead.site_facts["has_site"] = False
        return lead

    lead.site_facts["has_site"] = True
    started = time.monotonic()
    try:
        resp = requests.get(lead.website, headers=HEADERS, timeout=timeout, allow_redirects=True)
    except requests.RequestException:
        lead.site_issues.append("Сайт не открывается")
        lead.site_facts["reachable"] = False
        return lead
    elapsed = time.monotonic() - started
    lead.site_facts.update(reachable=resp.ok, load_sec=round(elapsed, 1), final_url=resp.url)
    if resp.status_code in (401, 403, 429):  # защита от ботов: сайт жив, просто не пустил программу
        lead.site_facts["checked"] = False
        lead.site_issues.append("Не удалось проверить сайт автоматически — посмотрите вручную")
        return lead
    if not resp.ok:
        lead.site_issues.append(f"Сайт отвечает ошибкой {resp.status_code}")
        return lead

    resp.encoding = resp.apparent_encoding or resp.encoding
    analyze_html(lead, resp.text, final_url=resp.url, load_sec=elapsed)
    return lead


def analyze_html(lead: Lead, html: str, final_url: str = "", load_sec: float = 0.0) -> Lead:
    """Разбор HTML отдельно от скачивания, чтобы можно было тестировать без интернета."""
    soup = BeautifulSoup(html, "html.parser")
    low = html.lower()
    text = soup.get_text(" ", strip=True)
    issues, facts = lead.site_issues, lead.site_facts

    if final_url.startswith("http://"):
        issues.append("Нет HTTPS: браузер пишет «Не защищено»")
    if load_sec > 4:
        issues.append(f"Медленно грузится ({load_sec:.1f} с)")
    if not soup.find("meta", attrs={"name": "viewport"}):
        issues.append("Не адаптирован под телефон")

    title = (soup.title.string or "").strip() if soup.title else ""
    desc = soup.find("meta", attrs={"name": "description"})
    facts["title"] = title
    if not title or len(title) < 15:
        issues.append("Пустой или короткий заголовок страницы (title) — плохо для SEO")
    if not desc or not (desc.get("content") or "").strip():
        issues.append("Нет описания для поисковиков (meta description)")
    if not soup.find("h1"):
        issues.append("Нет главного заголовка H1")

    years = [int(y) for y in YEAR_RE.findall(html)]
    this_year = datetime.date.today().year
    if years and max(years) <= this_year - 2:
        issues.append(f"Сайт давно не обновлялся (© {max(years)})")
        facts["copyright_year"] = max(years)

    facts["metrika"] = "mc.yandex.ru" in low or "ym(" in low
    if not facts["metrika"]:
        issues.append("Нет Яндекс Метрики: не считают заявки и рекламу")
    facts["booking"] = any(k in low for k in BOOKING)
    facts["chat"] = any(k in low for k in CHAT)
    facts["messenger_links"] = "wa.me" in low or "whatsapp" in low or "t.me/" in low or "max.ru/" in low
    facts["builder"] = next((v for k, v in BUILDERS.items() if k in low), "")
    if not facts["booking"]:
        issues.append("Нет онлайн-записи")
    if not facts["chat"] and not facts["messenger_links"]:
        issues.append("Нет чата или мессенджеров на сайте")

    # Контакты с сайта
    lead.phones = unique(lead.phones + find_phones(text))
    lead.emails = unique(lead.emails + find_emails(text) + [
        a["href"][7:].split("?")[0].lower() for a in soup.select('a[href^="mailto:"]')])
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "wa.me/" in href or "api.whatsapp.com" in href:
            phone = normalize_phone(re.sub(r"\D", "", href.split("wa.me/")[-1].split("phone=")[-1])[:11])
            if phone:
                lead.whatsapp = unique(lead.whatsapp + [phone])
        elif "t.me/" in href:
            handle = href.split("t.me/")[-1].split("?")[0].strip("/")
            if handle.startswith("+"):  # t.me/+79... — номер; t.me/+abc — приглашение в группу
                phone = normalize_phone(handle)
                if phone:
                    lead.telegram = unique(lead.telegram + [phone])
            elif handle and not handle.startswith(("share", "joinchat")) and "/" not in handle:
                lead.telegram = unique(lead.telegram + ["@" + handle])
        elif re.search(r"(?:^|//|\.)max\.ru/[^/?#\s]", href):  # max.ru/u/… или max.ru/имя — чат в MAX
            lead.max = unique(lead.max + [href.split("?")[0]])
        elif "vk.com/" in href and not lead.vk:
            lead.vk = href

    m = INN_RE.search(text)
    if m and not lead.inn:
        lead.inn = m.group(1)
    return lead
