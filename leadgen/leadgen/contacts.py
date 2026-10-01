"""Телефоны, почты и ссылки на мессенджеры."""
import re
from urllib.parse import quote

PHONE_RE = re.compile(r"(?:\+7|8)[\s\-\(]*\d{3}[\s\-\)]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
MOBILE_CODES = tuple(str(c) for c in range(900, 1000))


def normalize_phone(raw: str) -> str:
    """'8 (912) 345-67-89' -> '+79123456789'. Возвращает '' для не-российских/битых номеров."""
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 11 and digits[0] in "78":
        return "+7" + digits[1:]
    if len(digits) == 10:
        return "+7" + digits
    return ""


def is_mobile(phone: str) -> bool:
    """Мобильный номер (+79...). Только на мобильных бывают WhatsApp и Telegram."""
    return phone.startswith("+7") and phone[2:5] in MOBILE_CODES


def find_phones(text: str) -> list[str]:
    return unique(normalize_phone(m) for m in PHONE_RE.findall(text or ""))


def find_emails(text: str) -> list[str]:
    bad = (".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif")
    return unique(e.lower() for e in EMAIL_RE.findall(text or "") if not e.lower().endswith(bad))


def whatsapp_link(phone: str, text: str = "") -> str:
    link = f"https://wa.me/{phone.lstrip('+')}"
    return f"{link}?text={quote(text)}" if text else link


def telegram_link(phone_or_user: str) -> str:
    """Для номера — t.me/+7..., откроется, если человек разрешил поиск по номеру."""
    v = phone_or_user.strip()
    if v.startswith("http"):
        return v
    if v.startswith("+"):
        return f"https://t.me/{v}"
    return f"https://t.me/{v.lstrip('@')}"


def unique(items) -> list:
    seen, out = set(), []
    for x in items:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out
