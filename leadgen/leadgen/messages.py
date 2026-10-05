"""Первое сообщение: кому пишем (ЛПР или администратор) и через что (мессенджер или почта).

Тексты утверждены Лизой:
- ЛПР в мессенджер: обращение по имени-отчеству, кто я и что даю, вопрос в конце.
- ЛПР на почту: тот же текст и подпись с телефоном и Telegram.
- Администратору: кто я и просьба передать сообщение руководителю (имя в дательном падеже).

Кому писать, решает audience(): ИП и небольшой бизнес, где директор и есть владелец, получают
текст для ЛПР; сети, крупные клиники, госучреждения и компании без найденного директора получают
текст для администратора. В панели выбор можно переключить.
"""
import logging
import re

from pytrovich.detector import PetrovichGenderDetector
from pytrovich.enums import Case, NamePart
from pytrovich.maker import PetrovichDeclinationMaker

from .models import Lead

log = logging.getLogger(__name__)

LPR_MESSENGER = (
    "Добрый день, {name}!\n\n"
    "Я {me}, помогаю {plural_dat} с помощью нейросетей сделать сервис для клиентов удобнее, чтобы они "
    "чаще возвращались, и забираю на нейросети рутину, благодаря которой у руководства и команды "
    "появляется больше времени на важные задачи.\n\n"
    "Какие задачи с клиентами или внутри команды сейчас отнимают у вас больше всего времени?"
)
LPR_EMAIL = LPR_MESSENGER + "\n\nС ув. {sign}\n{phone}\nTelegram: {telegram}"
ADMIN = (
    "Здравствуйте!\n\n"
    "Меня зовут {me}, я внедряю нейросети в работу {plural_gen}: помогаю улучшить обслуживание клиентов, "
    "чтобы они возвращались чаще, и снимаю рутинные процессы с руководства и администраторов.\n\n"
    "Большая просьба передать это {what} {whom}, а также мои контакты ниже. Заранее спасибо!\n\n"
    "Мой Telegram: {telegram}\n{phone}"
)

# Признаки того, что на номере администратор, а директор наёмный или далеко
BIG_FORMS = ("ФГБУ", "ГБУЗ", "ГБУ", "ЧУЗ", "ПАО", "АО ", "ФИЛИАЛ")
NOT_OWNER_NOTES = ("наёмный", "франшиз")

FORBIDDEN = ("привет", "приветствую", "запишитесь", "закажите", "оформите", "оставьте заявку",
             "не упустите", "в современном мире", "₽", "руб.")

_maker = PetrovichDeclinationMaker()
_gender = PetrovichGenderDetector()


def first_name(lpr_name: str) -> str:
    """'Иванова Мария Петровна' -> 'Мария Петровна'."""
    parts = lpr_name.split()
    return " ".join(parts[1:3]) if len(parts) >= 2 else ""


def name_dative(lpr_name: str) -> str:
    """'Магомедова Пасихат Батировна' -> 'Пасихат Батировне'. Без отчества склонение ненадёжно: имя как есть."""
    parts = lpr_name.split()
    if len(parts) < 3:
        return first_name(lpr_name)
    first, middle = parts[1], parts[2]
    try:
        gender = _gender.detect(firstname=first, middlename=middle)
        return (f"{_maker.make(NamePart.FIRSTNAME, gender, Case.DATIVE, first)} "
                f"{_maker.make(NamePart.MIDDLENAME, gender, Case.DATIVE, middle)}")
    except Exception:  # редкое имя: лучше без склонения, чем с ошибкой в программе
        return f"{first} {middle}"


def audience(lead: Lead) -> str:
    """'lpr' — пишем директору напрямую, 'admin' — просим администратора передать."""
    if not first_name(lead.lpr_name):
        return "admin"
    if any(w in lead.lpr_note.lower() for w in NOT_OWNER_NOTES):
        return "admin"
    if "предприниматель" in lead.lpr_post.lower():
        return "lpr"
    if lead.branches >= 3 or lead.legal_name.upper().startswith(BIG_FORMS):
        return "admin"
    return "lpr"


def build(lead: Lead, niche_cfg: dict, cfg: dict) -> dict:
    """Все четыре текста: ЛПР и администратору, в мессенджер и на почту."""
    m = cfg.get("messages", {})
    words = {
        "me": m.get("intro_name", "Елизавета"),
        "sign": m.get("sign", "Елизавета Удахина"),
        "phone": m.get("phone", ""),
        "telegram": m.get("telegram", "https://t.me/lizaai_consult"),
        "plural_dat": niche_cfg.get("plural_dat", "компаниям"),
        "plural_gen": niche_cfg.get("plural_gen", "компаний"),
        "name": first_name(lead.lpr_name),
        "whom": name_dative(lead.lpr_name) or f"руководителю {niche_cfg.get('single_gen', 'компании')}",
    }
    texts = {
        "admin_messenger": ADMIN.format(what="сообщение", **words),
        "admin_email": ADMIN.format(what="письмо", **words),
    }
    if words["name"]:
        texts["lpr_messenger"] = LPR_MESSENGER.format(**words)
        texts["lpr_email"] = LPR_EMAIL.format(**words)
    return {k: v.rstrip() for k, v in texts.items()}


def template_message(lead: Lead, niche_cfg: dict, cfg: dict, variant: int | None = None) -> str:
    """Текст для мессенджера тому, кому программа решила писать (variant оставлен для совместимости)."""
    return build(lead, niche_cfg, cfg)[f"{audience(lead)}_messenger"]


def check_message(text: str, kind: str = "lpr_messenger") -> list[str]:
    """Проверка по правилам рассылки. Пустой список — можно отправлять."""
    problems = []
    if "—" in text or "–" in text:
        problems.append("длинное тире")
    if not re.match(r"(Здравствуйте|Добрый день)[,!]", text):
        problems.append("приветствие не «Здравствуйте»/«Добрый день»")
    low = text.lower()
    problems += [f"запрещено: «{w}»" for w in FORBIDDEN if w in low]
    if re.search(r"[\U0001F300-\U0001FAFF]", text):
        problems.append("эмодзи")
    if kind.startswith("lpr"):
        body = text.split("\n\nС ув.")[0].rstrip()
        if body.count("?") != 1 or not body.endswith("?"):
            problems.append("нужен ровно один вопрос, последним перед подписью")
        if kind == "lpr_email" and "С ув." not in text:
            problems.append("нет подписи")
    elif "t.me/" not in text:
        problems.append("нет контакта для передачи")
    return problems
