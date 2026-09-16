#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Общая логика анализа статистики Avito.

Используется и avito_stats.py (выгрузка через API), и manual_stats.py
(цифры, занесённые руками из кабинета) — чтобы разбор был один и тот же
независимо от способа добычи данных.
"""

import csv
import pathlib

# Ниже этого числа просмотров любые выводы — гадание.
MIN_VIEWS_FOR_VERDICT = 30

# Ориентир для обучения и услуг: 3-8% контактов от просмотров.
CR_BAD = 2.0
CR_OK = 5.0


def diagnose(views, contacts, median_views):
    """Короткий вердикт по объявлению: где именно узкое место."""
    if views < MIN_VIEWS_FOR_VERDICT:
        return "Мало показов — не хватает данных, объявлению нужен трафик"
    cr = contacts / views * 100
    if cr < CR_BAD:
        return "Трафик есть, но не пишут — слабый заголовок / цена / первое фото"
    if cr < CR_OK:
        return "Средняя конверсия — текст рабочий, можно докрутить оффер"
    if views < median_views:
        return "ПОБЕДИТЕЛЬ с узким охватом — сюда стоит направить продвижение"
    return "ПОБЕДИТЕЛЬ — масштабировать: похожие объявления + продвижение"


def build_rows(raw_rows):
    """raw_rows: список словарей с title, views, contacts, favorites, spend.

    Возвращает список строк с посчитанной конверсией и вердиктом,
    отсортированный по просмотрам.
    """
    view_counts = sorted(r["views"] for r in raw_rows) or [0]
    median_views = view_counts[len(view_counts) // 2]

    rows = []
    for r in raw_rows:
        views = r["views"]
        contacts = r["contacts"]
        spend = r.get("spend") or 0
        rows.append({
            "title": r["title"],
            "views": views,
            "contacts": contacts,
            "favorites": r.get("favorites") or 0,
            "spend": spend,
            "cr": "{:.2f}%".format(contacts / views * 100) if views else "—",
            "cpl": "{:.0f} ₽".format(spend / contacts) if (spend and contacts) else "—",
            "verdict": diagnose(views, contacts, median_views),
        })
    rows.sort(key=lambda r: r["views"], reverse=True)
    return rows


def build_report(rows, title_line, period_line):
    total_views = sum(r["views"] for r in rows)
    total_contacts = sum(r["contacts"] for r in rows)
    total_favorites = sum(r["favorites"] for r in rows)
    total_spend = sum(r["spend"] for r in rows)
    cr = (total_contacts / total_views * 100) if total_views else 0

    lines = [
        "# Статистика Avito",
        "",
        title_line,
        period_line,
        "**Объявлений в разборе:** {}".format(len(rows)),
        "",
        "## Итого",
        "",
        "| Показатель | Значение |",
        "|---|---|",
        "| Просмотры | {} |".format(total_views),
        "| Контакты (написали/позвонили) | {} |".format(total_contacts),
        "| В избранном | {} |".format(total_favorites),
        "| Конверсия просмотр → контакт | {:.2f}% |".format(cr),
    ]
    if total_spend:
        lines.append("| Потрачено на продвижение | {:.0f} ₽ |".format(total_spend))
        if total_contacts:
            lines.append("| Стоимость обращения | {:.0f} ₽ |".format(total_spend / total_contacts))

    lines += [
        "",
        "> Ориентир для обучения и услуг: 3–8%. Ниже 2% — проблема в объявлении, "
        "а не в бюджете: поднимать показы бессмысленно, пока текст не конвертирует.",
        "",
        "## По объявлениям",
        "",
        "| Объявление | Просмотры | Контакты | CR | Избранное | Обращение | Вердикт |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for r in rows:
        lines.append("| {} | {} | {} | {} | {} | {} | {} |".format(
            r["title"][:70], r["views"], r["contacts"],
            r["cr"], r["favorites"], r["cpl"], r["verdict"]
        ))

    lines += [
        "",
        "## Как это читать",
        "",
        "- **Мало просмотров + высокая CR** — объявление хорошее, его просто не видят. "
        "Расширять: новые заголовки под соседние запросы, платное продвижение именно сюда.",
        "- **Много просмотров + низкая CR** — трафик тратится впустую. "
        "Менять заголовок, первое фото и первые три строки текста, проверить цену.",
        "- **Много контактов, но нет оплат** — вопрос не к объявлению, а к первому сообщению "
        "в переписке и квалификации.",
        "",
    ]
    return "\n".join(lines)


def write_outputs(out_dir, stamp, rows, report_text):
    """Кладёт CSV и отчёт в папку. Возвращает пути к файлам."""
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "avito_stats_{}.csv".format(stamp)
    fields = ["title", "views", "contacts", "cr", "favorites", "spend", "cpl", "verdict"]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    report_path = out_dir / "report_{}.md".format(stamp)
    report_path.write_text(report_text, encoding="utf-8")

    return report_path, csv_path
