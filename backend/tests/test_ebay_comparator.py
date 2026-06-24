from app.services.ebay_comparator import EbayComparator


SAMPLE_HTML = """
<div class="s-item">
  <span class="s-item__title">Nike Air Max 90 Bianche 42</span>
  <span class="s-item__price">89,00 EUR</span>
</div>
<div class="s-item">
  <span class="s-item__title">Nike Air Max 90 Nere 43</span>
  <span class="s-item__price">95,50 EUR</span>
</div>
<div class="s-item">
  <span class="s-item__title">Shop on eBay</span>
  <span class="s-item__price">1,00 EUR</span>
</div>
"""


def test_parse_prices_from_html():
    comparator = EbayComparator()
    items = comparator.parse_prices_from_html(SAMPLE_HTML)
    assert len(items) == 2
    assert items[0].title.startswith("Nike Air Max")
    assert items[0].price == 89.0


def test_build_search_url_contains_sold_filters():
    comparator = EbayComparator()
    url = comparator.build_search_url("nike air max", brand="Nike")
    assert "LH_Sold=1" in url
    assert "LH_Complete=1" in url
    assert "Nike" in url
