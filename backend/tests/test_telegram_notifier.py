from datetime import datetime, timedelta

import httpx
import pytest

from app.services.telegram_notifier import TelegramNotifier


def test_should_notify_first_time():
    notifier = TelegramNotifier(bot_token="token", chat_id="123")
    assert notifier.should_notify("item-1") is True


def test_should_not_notify_within_cooldown():
    notifier = TelegramNotifier(bot_token="token", chat_id="123", cooldown_hours=24)
    now = datetime.utcnow()
    notifier._recent_notifications["item-1"] = now - timedelta(hours=1)
    assert notifier.should_notify("item-1", now=now) is False


def test_format_deal_message_contains_key_fields():
    notifier = TelegramNotifier(bot_token="token", chat_id="123")
    message = notifier.format_deal_message(
        title="Nike Air Max",
        vinted_price=45.0,
        benchmark_price=90.0,
        discount_percent=50.0,
        url="https://www.vinted.it/items/1",
    )
    assert "Nike Air Max" in message.text
    assert "45.00" in message.text
    assert "90.00" in message.text


def test_send_message_skips_when_not_configured():
    notifier = TelegramNotifier(bot_token="", chat_id="")
    sent = notifier.send_message(
        notifier.format_deal_message("x", 1, 2, 3, "http://x"),
        item_key="item-1",
    )
    assert sent is False


def test_send_message_posts_to_telegram(monkeypatch):
    calls = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

    def fake_post(url, json):
        calls["url"] = url
        calls["json"] = json
        return FakeResponse()

    client = httpx.Client()
    client.post = fake_post  # type: ignore[method-assign]

    notifier = TelegramNotifier(bot_token="abc", chat_id="999", client=client)
    sent = notifier.send_message(
        notifier.format_deal_message("Shoe", 30, 60, 50, "https://vinted.it/1"),
        item_key="item-99",
    )
    assert sent is True
    assert "abc" in calls["url"]
    assert calls["json"]["chat_id"] == "999"
