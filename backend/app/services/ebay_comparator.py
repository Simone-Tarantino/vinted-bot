import logging
from dataclasses import dataclass
from typing import Callable, Optional
from urllib.parse import quote_plus

from app.services.deal_engine import compute_robust_median
from app.services.vinted_worker import CHROMIUM_ARGS, USER_AGENT, parse_price

logger = logging.getLogger(__name__)

# Structured entries extracted from the rendered eBay results page.
_EBAY_EXTRACT_JS = r"""
() => {
  const out = [];
  document.querySelectorAll('ul.srp-results > li.s-card, li.s-item').forEach(li => {
    const t = (li.querySelector('.s-card__title, .s-item__title') || {}).innerText || '';
    const p = (li.querySelector('.s-card__price, .s-item__price') || {}).innerText || '';
    if (t && p) out.push({ title: t.trim(), price: p.trim() });
  });
  return out;
}
"""


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
    EBAY_BASE = "https://www.ebay.it"
    EBAY_SOLD_URL = "https://www.ebay.it/sch/i.html"

    def __init__(
        self,
        headless: bool = True,
        enabled: bool = True,
        fetch_fn: Optional[Callable[[str], list[dict]]] = None,
    ):
        self._headless = headless
        self._enabled = enabled
        # Injectable for tests; otherwise a Playwright browser fetch is used.
        self._fetch_fn = fetch_fn

    def build_search_url(self, query: str, brand: Optional[str] = None) -> str:
        keywords = " ".join(part for part in [brand, query] if part)
        return (
            f"{self.EBAY_SOLD_URL}?_nkw={quote_plus(keywords)}"
            "&LH_Complete=1&LH_Sold=1&_sop=13"
        )

    def parse_entries(self, entries: list[dict]) -> list[EbaySoldItem]:
        items: list[EbaySoldItem] = []
        for entry in entries:
            title = " ".join((entry.get("title") or "").split())
            if not title or title.lower().startswith("shop on ebay"):
                continue
            price = parse_price(entry.get("price") or "")
            if price is None or price <= 0:
                continue
            items.append(EbaySoldItem(title=title, price=price, currency="EUR"))
        return items

    def _fetch_entries(self, url: str) -> list[dict]:
        from playwright.sync_api import sync_playwright
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self._headless, args=CHROMIUM_ARGS)
            context = browser.new_context(locale="it-IT", user_agent=USER_AGENT)
            try:
                page = context.new_page()
                # Drop images/media/fonts: we only need the result text, and this
                # keeps Chromium's memory footprint small on tiny hosts. Stylesheets
                # are kept because blocking them stops eBay rendering the results.
                page.route(
                    "**/*",
                    lambda route: (
                        route.abort()
                        if route.request.resource_type in {"image", "media", "font"}
                        else route.continue_()
                    ),
                )
                # Warm up cookies on the homepage first; hitting the search URL
                # cold gets a 403 from eBay's edge protection.
                page.goto(self.EBAY_BASE, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(1200)
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                try:
                    page.wait_for_selector("ul.srp-results li", timeout=15000)
                except PlaywrightTimeoutError:
                    logger.warning("No eBay sold results rendered for %s", url)
                return page.evaluate(_EBAY_EXTRACT_JS)
            finally:
                browser.close()

    def fetch_benchmark(self, query: str, brand: Optional[str] = None) -> Optional[EbayBenchmark]:
        if not self._enabled:
            return None
        url = self.build_search_url(query, brand)
        fetch = self._fetch_fn or self._fetch_entries
        try:
            entries = fetch(url)
        except Exception as exc:  # noqa: BLE001 - benchmark is best-effort, never fatal
            logger.warning("eBay benchmark fetch failed for query=%r: %s", query, exc)
            return None

        sold_items = self.parse_entries(entries)
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
