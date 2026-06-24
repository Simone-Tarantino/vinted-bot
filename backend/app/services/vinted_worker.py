import base64
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from cryptography.fernet import Fernet, InvalidToken
from playwright.sync_api import Browser, Page, sync_playwright


@dataclass
class VintedListingData:
    vinted_item_id: str
    title: str
    price: float
    currency: str
    condition: Optional[str]
    url: str
    image_url: Optional[str]


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
        return f"{self.BASE_URL}/catalog?{params}"

    def parse_listings_from_html(self, html: str) -> list[VintedListingData]:
        pattern = re.compile(
            r'href="(/items/\d+[^"]*)"[^>]*>.*?'
            r'class="[^"]*web_ui__Text__text[^"]*"[^>]*>([^<]+)</p>.*?'
            r'class="[^"]*web_ui__Text__text[^"]*"[^>]*>([\d.,]+)\s*€',
            re.DOTALL,
        )

        listings: list[VintedListingData] = []
        seen_ids: set[str] = set()

        for relative_url, title, raw_price in pattern.findall(html):
            item_id_match = re.search(r"/items/(\d+)", relative_url)
            if not item_id_match:
                continue

            item_id = item_id_match.group(1)
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)

            price = float(raw_price.replace(",", "."))
            url = f"{self.BASE_URL}{relative_url.split('?')[0]}"
            listings.append(
                VintedListingData(
                    vinted_item_id=item_id,
                    title=title.strip(),
                    price=price,
                    currency="EUR",
                    condition=None,
                    url=url,
                    image_url=None,
                )
            )

        return listings

    def _apply_cookies(self, page: Page, cookies: list[dict[str, Any]]) -> None:
        page.context.add_cookies(cookies)

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
        cookies = self.session_store.load_cookies()

        with sync_playwright() as playwright:
            browser: Browser = playwright.chromium.launch(headless=self.headless)
            context = browser.new_context()
            page = context.new_page()

            if cookies:
                self._apply_cookies(page, cookies)

            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            html = page.content()

            if cookies:
                self.session_store.save_cookies(context.cookies())

            browser.close()

        return self.parse_listings_from_html(html)

    def import_session_cookies(self, cookies: list[dict[str, Any]]) -> None:
        self.session_store.save_cookies(cookies)

    def session_exists(self) -> bool:
        return self.session_store.load_cookies() is not None
