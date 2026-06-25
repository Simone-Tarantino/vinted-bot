import base64
import html
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import httpx
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# Flags required so Chromium runs reliably inside small/locked-down containers
# (e.g. DigitalOcean App Platform): no sandbox and no reliance on the tiny
# default /dev/shm, which otherwise makes the browser crash mid-scan.
CHROMIUM_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-setuid-sandbox",
]

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


@dataclass
class VintedListingData:
    vinted_item_id: str
    title: str
    price: float
    currency: str
    condition: Optional[str]
    url: str
    image_url: Optional[str]


@dataclass
class VintedBenchmark:
    median_price: float
    sample_count: int
    prices: list[float]
    titles: list[str]


def build_vinted_benchmark(listings: list["VintedListingData"]) -> Optional[VintedBenchmark]:
    """Use the robust median of comparable Vinted asking prices as a benchmark.

    A listing priced well below the typical price of its peers for the same
    search is a candidate deal. Needs no external source or browser.
    """
    from app.services.deal_engine import compute_robust_median

    prices = [listing.price for listing in listings]
    median, sample_count = compute_robust_median(prices)
    if median is None:
        return None

    return VintedBenchmark(
        median_price=median,
        sample_count=sample_count,
        prices=sorted(prices)[:30],
        titles=[listing.title for listing in listings[:30]],
    )


class VintedSessionStore:
    def __init__(self, encryption_key: str, session_file: str):
        self.session_file = Path(session_file)
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        self._fernet = Fernet(self._derive_key(encryption_key))

    @staticmethod
    def _derive_key(raw_key: str) -> bytes:
        padded = raw_key.encode("utf-8")[:32].ljust(32, b"0")
        return base64.urlsafe_b64encode(padded)

    def save_cookies(self, cookies: list[dict[str, Any]]) -> None:
        payload = json.dumps(cookies).encode("utf-8")
        encrypted = self._fernet.encrypt(payload)
        self.session_file.write_bytes(encrypted)

    def load_cookies(self) -> Optional[list[dict[str, Any]]]:
        if not self.session_file.exists():
            return None
        try:
            decrypted = self._fernet.decrypt(self.session_file.read_bytes())
            return json.loads(decrypted.decode("utf-8"))
        except (InvalidToken, json.JSONDecodeError):
            return None


def parse_price(text: str) -> Optional[float]:
    """Parse a price from a free-form string, handling IT/EN decimal formats.

    Examples: "€30.00" -> 30.0, "EUR 1.234,56" -> 1234.56, "19,90 €" -> 19.9.
    """
    match = re.search(r"\d[\d.,]*", text)
    if not match:
        return None

    # Drop any separator the greedy match grabbed before/after the digits
    # (e.g. a trailing comma from "€19.00, €20.65").
    raw = match.group(0).strip(".,")
    if "," in raw and "." in raw:
        # The right-most separator is the decimal one.
        if raw.rfind(",") > raw.rfind("."):
            raw = raw.replace(".", "").replace(",", ".")
        else:
            raw = raw.replace(",", "")
    elif "," in raw:
        # Comma is a decimal separator only when followed by 1-2 digits.
        raw = raw.replace(",", ".") if re.search(r",\d{1,2}$", raw) else raw.replace(",", "")

    try:
        return float(raw)
    except ValueError:
        return None


def parse_listing_title(title_attr: str) -> tuple[str, Optional[str], Optional[str], Optional[float]]:
    """Parse Vinted's accessible ``title`` attribute into structured fields.

    Format: ``"<title>, brand: <brand>, condizioni: <condition>, €<price>, ..."``.
    """
    text = html.unescape(title_attr).strip()

    brand_match = re.search(r",\s*brand:\s*(.+?)\s*,\s*(?:condizion|tagli|€|$)", text, re.IGNORECASE)
    cond_match = re.search(r"condizion[ei]:\s*(.+?)\s*,\s*€", text, re.IGNORECASE)
    price_match = re.search(r"€\s*([\d.,]+)", text)

    if ", brand:" in text:
        listing_title = text.split(", brand:", 1)[0].strip()
    else:
        listing_title = re.split(r",?\s*€", text, 1)[0].strip()

    brand = brand_match.group(1).strip() if brand_match else None
    condition = cond_match.group(1).strip() if cond_match else None
    price = parse_price(price_match.group(1)) if price_match else None
    return listing_title, brand, condition, price


class VintedWorker:
    BASE_URL = "https://www.vinted.it"

    def __init__(self, session_store: VintedSessionStore, headless: bool = True):
        self.session_store = session_store
        self.headless = headless

    def build_search_url(
        self,
        query: str,
        brand: Optional[str] = None,
        max_price: Optional[float] = None,
    ) -> str:
        search_text = " ".join(part for part in [brand, query] if part)
        params = f"search_text={search_text.replace(' ', '%20')}"
        if max_price:
            params += f"&price_to={int(max_price)}"
        params += "&order=newest_first"
        return f"{self.BASE_URL}/catalog?{params}"

    def parse_listings_from_html(self, html_content: str) -> list[VintedListingData]:
        """Extract listings from a rendered catalog page.

        Each product card is an ``<a>`` linking to ``/items/<id>`` whose ``title``
        attribute carries title/brand/condition/price as accessible text.
        """
        anchor_pattern = re.compile(
            r'<a\b([^>]*\bhref="[^"]*?/items/\d+[^"]*"[^>]*)>',
            re.IGNORECASE,
        )

        listings: list[VintedListingData] = []
        seen_ids: set[str] = set()

        for attrs in anchor_pattern.findall(html_content):
            href_match = re.search(r'href="([^"]*?/items/(\d+)[^"]*)"', attrs)
            title_match = re.search(r'title="([^"]*)"', attrs)
            if not href_match or not title_match:
                continue

            item_id = href_match.group(2)
            if item_id in seen_ids:
                continue

            listing_title, brand, condition, price = parse_listing_title(title_match.group(1))
            if price is None:
                continue
            seen_ids.add(item_id)

            href = href_match.group(1).split("?")[0]
            url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
            listings.append(
                VintedListingData(
                    vinted_item_id=item_id,
                    title=listing_title or title_match.group(1),
                    price=price,
                    currency="EUR",
                    condition=condition,
                    url=url,
                    image_url=None,
                )
            )

        return listings

    def search(
        self,
        query: str,
        brand: Optional[str] = None,
        max_price: Optional[float] = None,
        html_override: Optional[str] = None,
    ) -> list[VintedListingData]:
        if html_override is not None:
            return self.parse_listings_from_html(html_override)

        url = self.build_search_url(query, brand, max_price)

        # Vinted server-renders the catalog, so a plain HTTP GET returns the
        # listings (each as an <a> with a descriptive `title`). This avoids
        # launching Chromium, whose memory use crashed the container mid-scan.
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "it-IT,it;q=0.9",
        }
        cookie_jar = self._cookie_dict()

        with httpx.Client(timeout=30.0, follow_redirects=True, headers=headers) as client:
            response = client.get(url, cookies=cookie_jar)
            response.raise_for_status()
            html_content = response.text

        listings = self.parse_listings_from_html(html_content)
        if not listings:
            logger.warning(
                "No Vinted listings parsed for query=%r (status=%s, %s bytes)",
                query,
                response.status_code,
                len(html_content),
            )
        return listings

    def _cookie_dict(self) -> dict[str, str]:
        cookies = self.session_store.load_cookies() or []
        return {c["name"]: c["value"] for c in cookies if "name" in c and "value" in c}

    def import_session_cookies(self, cookies: list[dict[str, Any]]) -> None:
        self.session_store.save_cookies(cookies)

    def session_exists(self) -> bool:
        return self.session_store.load_cookies() is not None
