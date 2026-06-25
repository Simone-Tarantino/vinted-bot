from pathlib import Path

from app.services.vinted_worker import (
    VintedListingData,
    VintedSessionStore,
    VintedWorker,
    build_vinted_benchmark,
    parse_listing_title,
    parse_price,
)


def _listing(item_id: str, price: float, title: str = "Pokemon serie 1") -> VintedListingData:
    return VintedListingData(
        vinted_item_id=item_id,
        title=title,
        price=price,
        currency="EUR",
        condition=None,
        url=f"https://www.vinted.it/items/{item_id}",
        image_url=None,
    )


def test_build_vinted_benchmark_uses_robust_median():
    listings = [_listing(str(i), price) for i, price in enumerate([10, 12, 14, 16, 18, 20])]
    benchmark = build_vinted_benchmark(listings)
    assert benchmark is not None
    assert benchmark.sample_count == 6
    assert 14 <= benchmark.median_price <= 16
    assert len(benchmark.titles) == 6


def test_build_vinted_benchmark_none_when_too_few_samples():
    assert build_vinted_benchmark([_listing("1", 10.0), _listing("2", 12.0)]) is None


# Mirrors Vinted's current catalog markup: each card is an <a> to /items/<id>
# whose `title` attribute carries title/brand/condition/price as accessible text.
SAMPLE_HTML = """
<a href="https://www.vinted.it/items/9251531435-primi-compagni?referrer=catalog"
   data-testid="product-item-id-9251531435--overlay-link"
   title="Primi compagni di avventura serie 1, brand: Pok&eacute;mon, condizioni: Nuovo senza cartellino, &euro;19.00, &euro;20.65 include la Protezione acquisti"></a>
<a href="https://www.vinted.it/items/9251531435-primi-compagni?referrer=catalog"
   title="Primi compagni di avventura serie 1, brand: Pok&eacute;mon, condizioni: Nuovo senza cartellino, &euro;19.00, &euro;20.65 include la Protezione acquisti"></a>
<a href="https://www.vinted.it/items/9247530516-altro?referrer=catalog"
   title="Compagni di avventura serie 1 e 2, brand: Pok&eacute;mon, condizioni: Discrete, &euro;1.00, &euro;1.75 include la Protezione acquisti"></a>
"""


def test_parse_price_handles_locales():
    assert parse_price("€30.00") == 30.0
    assert parse_price("19,90 €") == 19.9
    assert parse_price("EUR 1.234,56") == 1234.56
    assert parse_price("no price") is None


def test_parse_listing_title_extracts_fields():
    title, brand, condition, price = parse_listing_title(
        "Primi compagni di avventura serie 1, brand: Pokémon, "
        "condizioni: Nuovo senza cartellino, €19.00, €20.65 include la Protezione acquisti"
    )
    assert title == "Primi compagni di avventura serie 1"
    assert brand == "Pokémon"
    assert condition == "Nuovo senza cartellino"
    assert price == 19.0


def test_parse_listings_deduplicates_items(tmp_path: Path):
    store = VintedSessionStore(
        encryption_key="test-key-32-characters-long!!!",
        session_file=str(tmp_path / "session.enc"),
    )
    worker = VintedWorker(session_store=store)
    listings = worker.parse_listings_from_html(SAMPLE_HTML)
    assert len(listings) == 2
    assert listings[0].vinted_item_id == "9251531435"
    assert listings[0].price == 19.0
    assert listings[0].condition == "Nuovo senza cartellino"
    assert listings[0].url == "https://www.vinted.it/items/9251531435-primi-compagni"


def test_session_store_roundtrip(tmp_path: Path):
    store = VintedSessionStore(
        encryption_key="another-test-key-32-chars!!!!",
        session_file=str(tmp_path / "session.enc"),
    )
    cookies = [{"name": "session", "value": "abc", "domain": ".vinted.it", "path": "/"}]
    store.save_cookies(cookies)
    loaded = store.load_cookies()
    assert loaded == cookies
