from dataclasses import dataclass, field


@dataclass
class Lead:
    """Одна найденная компания и всё, что мы о ней узнали."""

    name: str
    city: str = ""
    niche: str = ""
    address: str = ""
    source: str = ""
    website: str = ""
    phones: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    whatsapp: list[str] = field(default_factory=list)   # номера, найденные как WhatsApp
    telegram: list[str] = field(default_factory=list)   # @username или ссылки t.me
    max: list[str] = field(default_factory=list)        # ссылки на чат в мессенджере MAX (max.ru/…)
    vk: str = ""
    rating: float | None = None
    reviews: int | None = None
    branches: int = 1

    # Юрлицо и ЛПР (из DaData)
    inn: str = ""
    legal_name: str = ""
    lpr_name: str = ""
    lpr_post: str = ""
    lpr_profile: str = ""    # публичный рабочий профиль ЛПР (страница основателя, профессиональный аккаунт)
    lpr_note: str = ""       # как дойти до ЛПР: кто реально решает, что за ресурс

    # Аудит сайта и оценки
    site_issues: list[str] = field(default_factory=list)
    site_facts: dict = field(default_factory=dict)
    site_score: int = 0      # 0-100: насколько нужен новый сайт
    ai_score: int = 0        # 0-100: насколько нужен ИИ-помощник
    offer: str = ""          # site / ai / leadgen
    message: str = ""
    audience: str = ""       # lpr — пишем директору, admin — просим администратора передать
    texts: dict = field(default_factory=dict)   # тексты: lpr_messenger, lpr_email, admin_messenger, admin_email

    def key(self) -> str:
        """Ключ для удаления дублей: домен сайта, иначе первый телефон, иначе название."""
        if self.website:
            host = self.website.lower().split("//")[-1].split("/")[0]
            return host.removeprefix("www.")
        if self.phones:
            return self.phones[0]
        return f"{self.name.lower()}|{self.city.lower()}"
