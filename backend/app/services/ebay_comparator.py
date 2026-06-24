import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus

import httpx

from app.services.deal_engine import compute_robust_median


@dataclass
class EbaySoldItem:
    title: str
    price: float
    currency: str


@dataclass
class EbayBenchmark:
    median_price: float
    sample_count: int
    prices: list[float]
    titles: list[str]


class EbayComparator:
    EBAY_SOLD_URL = "https://www.ebay.it/sch/i.html"

    def __init__(self, client: Optional[httpx.Client] = None):
        self._client = client or httpx.Client(timeout=30.0, follow_redirects=True)

    def build_search_url(self, query: str, brand: Optional[str] = None) -> str:
        keywords = " ".join(part for part in [brand, query] if part)
        return (
            f"{self.EBAY_SOLD_URL}?_nkw={quote_plus(keywords)}"
            "&LH_Complete=1&LH_Sold=1&_sop=13"
        )

    def parse_prices_from_html(self, html: str) -> list[EbaySoldItem]:
        price_pattern = re.compile(
            r's-item__title[^>]*>([^<]+)</span>.*?s-item__price[^>]*>([^<]+)</span>',
            re.DOTALL,
        )
        items: list[EbaySoldItem] = []

        for title, raw_price in price_pattern.findall(html):
            title = re.sub(r"\s+", " ", title).strip()
            if not title or title.lower().startswith("shop on ebay"):
                continue

            price_match = re.search(r"([\d.,]+)", raw_price.replace("\xa0", " "))
            if not price_match:
                continue

            price_text = price_match.group(1).replace(".", "").replace(",", ".")
            try:
                price = float(price_text)
            except ValueError:
                continue

            items.append(EbaySoldItem(title=title, price=price, currency="EUR"))

        return items

    def fetch_benchmark(self, query: str, brand: Optional[str] = None) -> Optional[EbayBenchmark]:
        url = self.build_search_url(query, brand)
        response = self._client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()

        sold_items = self.parse_prices_from_html(response.text)
        prices = [item.price for item in sold_items]
        median, sample_count = compute_robust_median(prices)

        if median is None:
            return None

        return EbayBenchmark(
            median_price=median,
            sample_count=sample_count,
            prices=prices[:20],
            titles=[item.title for item in sold_items[:20]],
        )
