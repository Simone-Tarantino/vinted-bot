from pathlib import Path

from app.services.vinted_worker import VintedSessionStore, VintedWorker


SAMPLE_HTML = """
<a href="/items/1234567890-test-item">
  <p class="web_ui__Text__text web_ui__Text__title">Nike Air Max 90</p>
  <p class="web_ui__Text__text web_ui__Text__subtitle">45,00 €</p>
</a>
<a href="/items/1234567890-test-item">
  <p class="web_ui__Text__text web_ui__Text__title">Nike Air Max 90</p>
  <p class="web_ui__Text__text web_ui__Text__subtitle">45,00 €</p>
</a>
<a href="/items/9876543210-other">
  <p class="web_ui__Text__text web_ui__Text__title">Adidas Samba</p>
  <p class="web_ui__Text__text web_ui__Text__subtitle">30,00 €</p>
</a>
"""


def test_parse_listings_deduplicates_items(tmp_path: Path):
    store = VintedSessionStore(
        encryption_key="test-key-32-characters-long!!!",
        session_file=str(tmp_path / "session.enc"),
    )
    worker = VintedWorker(session_store=store)
    listings = worker.parse_listings_from_html(SAMPLE_HTML)
    assert len(listings) == 2
    assert listings[0].vinted_item_id == "1234567890"
    assert listings[0].price == 45.0


def test_session_store_roundtrip(tmp_path: Path):
    store = VintedSessionStore(
        encryption_key="another-test-key-32-chars!!!!",
        session_file=str(tmp_path / "session.enc"),
    )
    cookies = [{"name": "session", "value": "abc", "domain": ".vinted.it", "path": "/"}]
    store.save_cookies(cookies)
    loaded = store.load_cookies()
    assert loaded == cookies
