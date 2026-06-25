from app.services.ebay_comparator import EbayComparator


SAMPLE_ENTRIES = [
    {"title": "Nike Air Max 90 Bianche 42", "price": "EUR 89,00"},
    {"title": "Nike Air Max 90 Nere 43", "price": "EUR 95,50"},
    {"title": "Shop on eBay", "price": "EUR 1,00"},
    {"title": "Senza prezzo", "price": ""},
]


def test_parse_entries_filters_junk():
    comparator = EbayComparator()
    items = comparator.parse_entries(SAMPLE_ENTRIES)
    assert len(items) == 2
    assert items[0].title.startswith("Nike Air Max")
    assert items[0].price == 89.0


def test_fetch_benchmark_uses_injected_fetcher():
    entries = [
        {"title": f"Nike Air Max 90 #{i}", "price": f"EUR {80 + i},00"} for i in range(6)
    ]
    comparator = EbayComparator(fetch_fn=lambda url: entries)
    benchmark = comparator.fetch_benchmark("nike air max", brand="Nike")
    assert benchmark is not None
    assert benchmark.sample_count == 6
    assert 80 <= benchmark.median_price <= 85


def test_fetch_benchmark_returns_none_on_fetch_error():
    def boom(url):
        raise RuntimeError("403 Forbidden")

    comparator = EbayComparator(fetch_fn=boom)
    assert comparator.fetch_benchmark("nike air max") is None


def test_build_search_url_contains_sold_filters():
    comparator = EbayComparator()
    url = comparator.build_search_url("nike air max", brand="Nike")
    assert "LH_Sold=1" in url
    assert "LH_Complete=1" in url
    assert "Nike" in url
