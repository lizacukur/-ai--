#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Разбор статистики Avito по цифрам, занесённым руками.

Путь без API: цифры берутся в кабинете (Аналитика → по каждому объявлению),
переносятся в таблицу, скрипт считает конверсию, стоимость обращения
и выдаёт вердикт по каждому объявлению.

Запуск:
    python3 avito/manual_stats.py
    python3 avito/manual_stats.py путь/к/своей/таблице.csv

Таблица — avito/my_stats.csv. Открывается и правится в Excel,
Google Таблицах или в любом текстовом редакторе.
Колонки: объявление, просмотры, контакты, избранное, расход.
Последние две можно оставить пустыми.
"""

import csv
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import report  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_TABLE = HERE / "my_stats.csv"
OUT = HERE / "out"

# Как могут называться колонки — чтобы таблица не ломалась от формулировки.
ALIASES = {
    "title": ["объявление", "заголовок", "название", "title"],
    "views": ["просмотры", "показы", "views"],
    "contacts": ["контакты", "обращения", "написали", "contacts"],
    "favorites": ["избранное", "лайки", "favorites"],
    "spend": ["расход", "потрачено", "продвижение", "spend"],
}


def detect_delimiter(sample):
    """Excel в русской локали сохраняет CSV через точку с запятой."""
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,\t").delimiter
    except csv.Error:
        return ";" if sample.count(";") > sample.count(",") else ","


def map_columns(fieldnames):
    """Сопоставляет заголовки таблицы с нужными полями."""
    found = {}
    for name in fieldnames or []:
        key = (name or "").strip().lower().lstrip("﻿")
        for field, variants in ALIASES.items():
            if key in variants and field not in found:
                found[field] = name
    return found


def to_number(value):
    """'1 240', '1240,5', '' -> число. Пустое и мусор -> 0."""
    if value is None:
        return 0
    cleaned = str(value).replace(" ", "").replace(" ", "").replace(",", ".").strip()
    if not cleaned:
        return 0
    try:
        return int(float(cleaned))
    except ValueError:
        return 0


def read_table(path):
    text = path.read_text(encoding="utf-8-sig")
    if not text.strip():
        raise SystemExit("Таблица {} пустая — заполни её и запусти снова.".format(path))

    delimiter = detect_delimiter(text[:2048])
    reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
    columns = map_columns(reader.fieldnames)

    missing = [f for f in ("title", "views", "contacts") if f not in columns]
    if missing:
        raise SystemExit(
            "В таблице не хватает обязательных колонок: {}.\n"
            "Нужны как минимум: объявление, просмотры, контакты.\n"
            "Сейчас в файле: {}".format(", ".join(missing), reader.fieldnames)
        )

    rows, skipped = [], 0
    for record in reader:
        title = (record.get(columns["title"]) or "").strip()
        if not title:
            skipped += 1
            continue
        rows.append({
            "title": title,
            "views": to_number(record.get(columns["views"])),
            "contacts": to_number(record.get(columns["contacts"])),
            "favorites": to_number(record.get(columns.get("favorites", ""))),
            "spend": to_number(record.get(columns.get("spend", ""))),
        })

    if not rows:
        raise SystemExit("В таблице нет ни одной заполненной строки.")
    if skipped:
        print("  пропущено пустых строк: {}".format(skipped))
    return rows


def main():
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TABLE
    if not path.exists():
        raise SystemExit(
            "Не нашёл таблицу {}.\n"
            "Возьми шаблон avito/my_stats.csv, впиши свои цифры из кабинета "
            "и запусти снова.".format(path)
        )

    print("Читаю {}...".format(path.name))
    raw_rows = read_table(path)
    print("  объявлений в таблице: {}".format(len(raw_rows)))

    rows = report.build_rows(raw_rows)
    stamp = dt.date.today().isoformat()
    text = report.build_report(
        rows,
        title_line="**Источник:** цифры из кабинета, занесены вручную",
        period_line="**Собрано:** {}".format(stamp),
    )
    report_path, csv_path = report.write_outputs(OUT, stamp, rows, text)

    print("\nГотово. Файлы:")
    for p in (report_path, csv_path):
        print("  {}".format(p))
    print("\nПришли мне report_*.md — разберу цифры и соберу план.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
