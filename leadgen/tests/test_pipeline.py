"""Проверка без интернета: подменяем ответы 2ГИС, DaData и сайта."""
import json
from pathlib import Path

import yaml
from openpyxl import load_workbook

from leadgen import audit, contacts, enrich, export, messages, scoring, sources
from leadgen.models import Lead

CFG = yaml.safe_load((Path(__file__).parent.parent / "config.yaml").read_text(encoding="utf-8"))

OLD_SITE = """<html><head><title>Стоматология</title></head><body>
<p>Звоните: 8 (912) 345-67-89, почта info@smile-dent.ru</p>
<a href="https://wa.me/79123456789">WhatsApp</a> <a href="https://t.me/smiledent">TG</a>
<a href="https://t.me/+AbCdEf">группа</a>
<footer>© 2019 ООО «Смайл» ИНН 7701234567</footer></body></html>"""

GOOD_SITE = """<html><head><title>Стоматология «Улыбка» в Казани — лечение и имплантация</title>
<meta name="viewport" content="width=device-width"><meta name="description" content="Клиника">
<script src="https://mc.yandex.ru/metrika/tag.js"></script><script src="//w.yclients.com/widget.js"></script>
<script src="//code.jivo.ru/widget/x"></script></head><body><h1>Улыбка</h1>© 2026</body></html>"""


class FakeResp:
    def __init__(self, data, status=200):
        self._data, self.status_code = data, status
        self.text = json.dumps(data)

    def json(self):
        return self._data


def test_phone_normalization():
    assert contacts.normalize_phone("8 (912) 345-67-89") == "+79123456789"
    assert contacts.normalize_phone("+7 495 123 45 67") == "+74951234567"
    assert contacts.normalize_phone("123") == ""
    assert contacts.is_mobile("+79123456789") and not contacts.is_mobile("+74951234567")


def test_audit_old_site_finds_issues_and_contacts():
    lead = audit.analyze_html(Lead(name="Смайл", website="http://smile-dent.ru"), OLD_SITE,
                              final_url="http://smile-dent.ru", load_sec=5.2)
    text = " ".join(lead.site_issues)
    for expected in ("Нет HTTPS", "Медленно", "телефон", "© 2019", "онлайн-записи", "Метрики"):
        assert expected in text, expected
    assert lead.phones == ["+79123456789"]
    assert lead.emails == ["info@smile-dent.ru"]
    assert lead.whatsapp == ["+79123456789"]
    assert lead.telegram == ["@smiledent"]          # приглашение в группу не попало
    assert lead.inn == "7701234567"


def test_audit_good_site_is_clean():
    lead = audit.analyze_html(Lead(name="Улыбка", website="https://u.ru"), GOOD_SITE, final_url="https://u.ru")
    assert lead.site_issues == []
    assert lead.site_facts["booking"] and lead.site_facts["chat"] and lead.site_facts["metrika"]


def test_2gis_parsing(monkeypatch):
    item = {
        "name": "Смайл", "full_address_name": "Казань, ул. Баумана, 1", "org": {"branch_count": 3},
        "reviews": {"general_rating": 4.4, "general_review_count": 320},
        "contact_groups": [{"contacts": [
            {"type": "phone", "value": "+79123456789", "text": "+7 912 345-67-89"},
            {"type": "website", "value": "http://link.2gis.ru/abc", "text": "smile-dent.ru"},
            {"type": "telegram", "value": "https://t.me/smiledent", "text": "@smiledent"},
        ]}],
    }
    pages = [FakeResp({"meta": {"code": 200}, "result": {"items": [item]}}),
             FakeResp({"meta": {"code": 404}})]
    monkeypatch.setattr(sources.HTTP, "get", lambda *a, **k: pages.pop(0))
    [lead] = sources.search_2gis("key", "стоматология", "Казань", "dental", 50)
    assert lead.website == "http://smile-dent.ru"
    assert lead.phones == ["+79123456789"] and lead.telegram == ["@smiledent"]
    assert (lead.rating, lead.reviews, lead.branches) == (4.4, 320, 3)


def test_dadata_by_inn(monkeypatch):
    found = {"suggestions": [{"data": {
        "inn": "7701234567", "type": "LEGAL", "name": {"short_with_opf": "ООО «Смайл»"},
        "management": {"name": "Иванова Мария Петровна", "post": "ГЕНЕРАЛЬНЫЙ ДИРЕКТОР"}}}]}
    monkeypatch.setattr(enrich.requests, "post", lambda *a, **k: FakeResp(found))
    lead = enrich.find_lpr(Lead(name="Смайл", city="Казань", inn="7701234567"), "key")
    assert lead.lpr_name == "Иванова Мария Петровна"
    assert lead.lpr_post == "Генеральный директор"
    assert lead.site_facts["lpr_confidence"].startswith("точно")


def test_scoring_and_message_and_export(tmp_path):
    no_site = Lead(name="Ромашка", city="Москва", niche="beauty_salon", phones=["+79001112233"])
    audit.audit_site(no_site)
    clinic = audit.analyze_html(
        Lead(name="Смайл", city="Казань", niche="dental", website="http://smile-dent.ru",
             reviews=320, rating=4.4, lpr_name="Иванова Мария Петровна", lpr_post="Директор"),
        GOOD_SITE.replace("yclients", "").replace("jivo", ""), final_url="https://smile-dent.ru")

    scoring.score(no_site, CFG["niches"]["beauty_salon"])
    scoring.score(clinic, CFG["niches"]["dental"])
    assert no_site.offer == "site" and no_site.site_score >= 50
    assert clinic.offer == "ai" and clinic.ai_score >= 70

    for lead in (no_site, clinic):
        lead.message = messages.template_message(lead, CFG["niches"][lead.niche], CFG)
    assert clinic.message.startswith("Мария Петровна, здравствуйте!")
    assert "320 отзывов" in clinic.message and "20\u00a0000 ₽" in clinic.message
    assert "повторные визиты, а частая проблема" in clinic.message   # запятые на месте
    assert "(Москва)" in no_site.message and "Прислать пример" in no_site.message
    assert "нет своего сайта" in no_site.message and "80\u00a0000 ₽" in no_site.message

    wa, tg = export.channels(clinic)
    assert wa == "" and tg == ""                   # контактов нет — кнопок нет
    wa, tg = export.channels(no_site)
    assert wa.startswith("https://wa.me/79001112233?text=") and tg == "https://t.me/+79001112233"

    export.to_excel([clinic, no_site], tmp_path / "l.xlsx")
    export.to_html([clinic, no_site], tmp_path / "l.html")
    ws = load_workbook(tmp_path / "l.xlsx").active
    assert ws.max_row == 3 and ws.cell(2, 2).value == "Смайл"
    assert "Ромашка" in (tmp_path / "l.html").read_text(encoding="utf-8")


def test_llm_falls_back_to_template_on_error():
    class Broken:
        class beta:
            class messages:
                @staticmethod
                def create(**kw):
                    raise RuntimeError("нет сети")
    lead = Lead(name="X", city="Казань", niche="dental", offer="ai")
    text = messages.llm_message(lead, CFG["niches"]["dental"], CFG, Broken())
    assert text == messages.template_message(lead, CFG["niches"]["dental"], CFG)
