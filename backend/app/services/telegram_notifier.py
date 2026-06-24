from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import httpx


@dataclass
class TelegramMessage:
    text: str


class TelegramNotifier:
    API_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        client: Optional[httpx.Client] = None,
        cooldown_hours: int = 24,
    ):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.cooldown_hours = cooldown_hours
        self._client = client or httpx.Client(timeout=20.0)
        self._recent_notifications: dict[str, datetime] = {}

    def configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def should_notify(self, item_key: str, now: Optional[datetime] = None) -> bool:
        now = now or datetime.utcnow()
        last_sent = self._recent_notifications.get(item_key)
        if not last_sent:
            return True
        return now - last_sent >= timedelta(hours=self.cooldown_hours)

    def format_deal_message(
        self,
        title: str,
        vinted_price: float,
        benchmark_price: float,
        discount_percent: float,
        url: str,
    ) -> TelegramMessage:
        text = (
            "🔥 Offerta Vinted rilevata\n\n"
            f"*{title}*\n"
            f"Prezzo Vinted: €{vinted_price:.2f}\n"
            f"Benchmark eBay: €{benchmark_price:.2f}\n"
            f"Sconto stimato: {discount_percent:.1f}%\n\n"
            f"[Apri annuncio]({url})"
        )
        return TelegramMessage(text=text)

    def send_message(self, message: TelegramMessage, item_key: str) -> bool:
        if not self.configured():
            return False

        if not self.should_notify(item_key):
            return False

        url = self.API_URL.format(token=self.bot_token)
        response = self._client.post(
            url,
            json={
                "chat_id": self.chat_id,
                "text": message.text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False,
            },
        )
        response.raise_for_status()
        self._recent_notifications[item_key] = datetime.utcnow()
        return True
