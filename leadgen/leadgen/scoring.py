"""Оценки: насколько компании нужен новый сайт и насколько — ИИ-помощник."""
from .contacts import is_mobile
from .models import Lead

SITE_WEIGHTS = {
    "Нет сайта": 60,
    "Сайт не открывается": 55,
    "Сайт отвечает ошибкой": 45,
    "Не адаптирован под телефон": 25,
    "Нет HTTPS": 15,
    "Сайт давно не обновлялся": 15,
    "Медленно грузится": 10,
    "Нет описания для поисковиков": 10,
    "Пустой или короткий заголовок": 10,
    "Нет главного заголовка H1": 5,
    "Нет Яндекс Метрики": 10,
}


def score(lead: Lead, niche_cfg: dict) -> Lead:
    site = sum(w for prefix, w in SITE_WEIGHTS.items() if any(i.startswith(prefix) for i in lead.site_issues))
    lead.site_score = min(site, 100)

    f = lead.site_facts
    ai = (niche_cfg.get("ltv", 3)) * 10              # ниша, где решают повторные визиты: до 50
    if lead.reviews:                                  # много отзывов = много клиентов = есть что возвращать
        ai += 20 if lead.reviews >= 200 else 12 if lead.reviews >= 50 else 5
    if lead.rating is not None and lead.rating < 4.6:
        ai += 10                                      # проседает сервис — ИИ закрывает ответы и отзывы
    if lead.branches > 1:
        ai += 10
    if f.get("has_site") and not f.get("booking"):
        ai += 10
    if f.get("has_site") and not f.get("chat") and not f.get("messenger_links"):
        ai += 10
    lead.ai_score = min(ai, 100)

    main = niche_cfg.get("main_offer", "ai")
    if main == "leadgen":
        lead.offer = "leadgen"
    elif lead.site_score >= 50:
        lead.offer = "site"          # без нормального сайта ИИ не на что ставить
    else:
        lead.offer = "ai" if lead.ai_score >= lead.site_score else "site"
    return lead


def priority(lead: Lead) -> int:
    """Итоговый приоритет для сортировки таблицы (есть ли кому писать + горячесть)."""
    reach = 20 if (lead.whatsapp or lead.telegram or any(is_mobile(p) for p in lead.phones)) else 0
    lpr = 10 if lead.lpr_name else 0
    return max(lead.site_score, lead.ai_score) + reach + lpr

