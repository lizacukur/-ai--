"""Запуск: python -m leadgen search   или   python -m leadgen csv мой_список.csv"""
import argparse
import datetime
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml
from dotenv import load_dotenv

from . import audit, enrich, export, messages, scoring, sources
from .models import Lead

ROOT = Path(__file__).resolve().parent.parent
log = logging.getLogger("leadgen")


def main() -> None:
    load_dotenv(ROOT / ".env")
    p = argparse.ArgumentParser(prog="leadgen", description="Поиск клиентов: компании → аудит сайта → ЛПР → сообщение")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="найти компании в 2ГИС / Яндексе")
    s.add_argument("--cities", nargs="+", help="города (по умолчанию все из config.yaml)")
    s.add_argument("--niches", nargs="+", help="коды ниш из config.yaml, например dental auto_service")
    s.add_argument("--limit", type=int, help="сколько компаний на один запрос")

    c = sub.add_parser("csv", help="проверить свой список компаний из CSV")
    c.add_argument("path")
    c.add_argument("--niche", default="", help="код ниши из config.yaml для всего списка")

    sub.add_parser("niches", help="показать коды ниш")
    for sp in (s, c):
        sp.add_argument("--all", action="store_true", help="не пропускать компании из прошлых запусков")
        sp.add_argument("--no-llm", action="store_true", help="сообщения по шаблону, без нейросети")
    args = p.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))

    if args.cmd == "niches":
        for code, n in cfg["niches"].items():
            print(f"{code:16} {n['name']}")
        return

    leads = collect(args, cfg)
    if not args.all:
        leads = drop_seen(leads)
    if not leads:
        log.info("Новых компаний не найдено.")
        return
    process(leads, cfg, use_llm=not args.no_llm)


def collect(args, cfg) -> list[Lead]:
    if args.cmd == "csv":
        leads = sources.load_csv(args.path)
        for lead in leads:
            lead.niche = lead.niche or args.niche
        return dedupe(leads)

    dgis, yandex = os.getenv("DGIS_API_KEY"), os.getenv("YANDEX_MAPS_API_KEY")
    if not (dgis or yandex):
        sys.exit("Нет ключей поиска. Впишите DGIS_API_KEY или YANDEX_MAPS_API_KEY в файл .env (см. README).")
    limit = args.limit or cfg["limits"]["per_query"]
    niches = args.niches or list(cfg["niches"])
    unknown = [n for n in niches if n not in cfg["niches"]]
    if unknown:
        sys.exit(f"Неизвестные ниши: {unknown}. Список: python -m leadgen niches")

    leads: list[Lead] = []
    for city in args.cities or cfg["cities"]:
        for code in niches:
            for query in cfg["niches"][code]["queries"]:
                log.info("Ищу «%s» в %s…", query, city)
                if dgis:
                    leads += sources.search_2gis(dgis, query, city, code, limit)
                if yandex:
                    leads += sources.search_yandex(yandex, query, city, code, limit)
    return dedupe(leads)


def dedupe(leads: list[Lead]) -> list[Lead]:
    """Одна компания может прийти из 2ГИС и Яндекса — склеиваем контакты."""
    by_key: dict[str, Lead] = {}
    for lead in leads:
        if not lead.name and not lead.website:
            continue
        old = by_key.get(lead.key())
        if old is None:
            by_key[lead.key()] = lead
            continue
        old.phones = list(dict.fromkeys(old.phones + lead.phones))
        old.emails = list(dict.fromkeys(old.emails + lead.emails))
        old.whatsapp = list(dict.fromkeys(old.whatsapp + lead.whatsapp))
        old.telegram = list(dict.fromkeys(old.telegram + lead.telegram))
        old.website = old.website or lead.website
        old.rating = old.rating or lead.rating
        old.reviews = old.reviews or lead.reviews
        if lead.source not in old.source:
            old.source += f", {lead.source}"
    return list(by_key.values())


def drop_seen(leads: list[Lead]) -> list[Lead]:
    seen_file = ROOT / "data" / "seen.txt"
    seen = set(seen_file.read_text(encoding="utf-8").split("\n")) if seen_file.exists() else set()
    fresh = [l for l in leads if l.key() not in seen]
    if len(fresh) < len(leads):
        log.info("Пропускаю %d компаний из прошлых запусков (флаг --all, чтобы взять всех).", len(leads) - len(fresh))
    return fresh


def remember(leads: list[Lead]) -> None:
    seen_file = ROOT / "data" / "seen.txt"
    seen_file.parent.mkdir(exist_ok=True)
    with seen_file.open("a", encoding="utf-8") as f:
        f.writelines(l.key() + "\n" for l in leads)


def process(leads: list[Lead], cfg: dict, use_llm: bool) -> None:
    timeout = cfg["limits"]["site_timeout_sec"]
    log.info("Проверяю сайты: %d компаний…", len(leads))
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda l: audit.audit_site(l, timeout), leads))

    dadata = os.getenv("DADATA_API_KEY")
    if dadata:
        log.info("Ищу ЛПР в ЕГРЮЛ (DaData)…")
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda l: enrich.find_lpr(l, dadata), leads))
    else:
        log.info("DADATA_API_KEY не задан — ЛПР не ищу.")

    for lead in leads:
        scoring.score(lead, cfg["niches"].get(lead.niche, {}))

    client = None
    if use_llm and cfg.get("llm", {}).get("enabled") and os.getenv("ANTHROPIC_API_KEY"):
        import anthropic
        client = anthropic.Anthropic()
        log.info("Пишу персональные сообщения через Claude…")
    for lead in leads:
        niche_cfg = cfg["niches"].get(lead.niche, {})
        lead.message = (messages.llm_message(lead, niche_cfg, cfg, client) if client
                        else messages.template_message(lead, niche_cfg, cfg))

    leads.sort(key=scoring.priority, reverse=True)
    out = ROOT / "output"
    out.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    xlsx, html = out / f"leads_{stamp}.xlsx", out / f"leads_{stamp}.html"
    export.to_excel(leads, xlsx)
    export.to_html(leads, html)
    remember(leads)

    with_lpr = sum(1 for l in leads if l.lpr_name)
    reach = sum(1 for l in leads if any(export.channels(l)))
    log.info("\nГотово: %d компаний, ЛПР найден у %d, писать в мессенджер можно %d.", len(leads), with_lpr, reach)
    log.info("Таблица: %s\nПанель отправки (откройте в браузере): %s", xlsx, html)


if __name__ == "__main__":
    main()
