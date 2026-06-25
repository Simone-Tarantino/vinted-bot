import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.models import (
    DealSignal,
    JobRun,
    MonitoredSearch,
    NotificationLog,
    PriceBenchmark,
    ProductSignature,
    VintedListing,
)
from app.services.deal_engine import compute_robust_median, is_deal
from app.services.gemini_client import GeminiClient, GeminiConfigurationError
from app.services.telegram_notifier import TelegramNotifier
from app.services.vinted_worker import VintedListingData, VintedSessionStore, VintedWorker

logger = logging.getLogger(__name__)

SIGNATURE_BATCH_SIZE = 50


class ScanOrchestrator:
    def __init__(
        self,
        db: Session,
        settings: Optional[Settings] = None,
        vinted_worker: Optional[VintedWorker] = None,
        signature_classifier: Optional[GeminiClient] = None,
        telegram_notifier: Optional[TelegramNotifier] = None,
    ):
        self.db = db
        self.settings = settings or get_settings()

        session_store = VintedSessionStore(
            encryption_key=self.settings.vinted_session_encryption_key,
            session_file=self.settings.vinted_session_file,
        )
        self.vinted_worker = vinted_worker or VintedWorker(session_store=session_store)

        # Cheap model: product-signature classification is the only AI step.
        self.signature_classifier = signature_classifier or GeminiClient(
            api_key=self.settings.gemini_api_key,
            model_name=self.settings.gemini_signature_model,
        )

        self.telegram_notifier = telegram_notifier or TelegramNotifier(
            bot_token=self.settings.telegram_bot_token,
            chat_id=self.settings.telegram_chat_id,
            cooldown_hours=self.settings.notification_cooldown_hours,
        )

    def run_scan(self) -> JobRun:
        job = JobRun(job_name="scan_all_searches", status="running", started_at=datetime.utcnow())
        self.db.add(job)
        self.db.commit()

        processed = 0
        deals_found = 0

        try:
            if not self.settings.gemini_configured():
                raise GeminiConfigurationError("GEMINI_API_KEY is required")

            searches = (
                self.db.query(MonitoredSearch)
                .filter(MonitoredSearch.is_active.is_(True))
                .all()
            )

            failed_searches = 0
            for search in searches:
                processed += 1
                try:
                    deals_found += self._process_search(search)
                except Exception:  # noqa: BLE001 - isolate one search's failure
                    self.db.rollback()
                    failed_searches += 1
                    logger.exception("Failed to process search id=%s", search.id)

            job.status = "success"
            job.details = json.dumps(
                {
                    "searches_processed": processed,
                    "deals_found": deals_found,
                    "failed_searches": failed_searches,
                }
            )
        except Exception as exc:  # noqa: BLE001 - job failure capture
            logger.exception("Scan failed")
            job.status = "failed"
            job.details = str(exc)
        finally:
            job.finished_at = datetime.utcnow()
            self.db.commit()

        return job

    def _process_search(self, search: MonitoredSearch) -> int:
        deals_found = 0
        # Listings within the user's max_price: what we track and consider deals.
        listings = self.vinted_worker.search(
            query=search.query,
            brand=search.brand,
            max_price=search.max_price,
        )

        # Persist tracking first and commit, so the dashboard reflects monitoring
        # activity even if the benchmark/AI steps below fail.
        listing_models = [self._upsert_listing(search, data) for data in listings]
        self.db.commit()

        # Benchmark population: the full (unfiltered) result set, so per-product
        # medians reflect the whole market, not just the cheap end the user filters.
        broad = (
            self.vinted_worker.search(query=search.query, brand=search.brand)
            if search.max_price is not None
            else listings
        )
        population: dict[str, VintedListingData] = {}
        for data in list(broad) + list(listings):
            population.setdefault(data.vinted_item_id, data)

        # Assign each item a canonical product signature (cached across scans).
        signatures = self._signatures_for(list(population.values()))

        # Robust median price per real-product signature.
        prices_by_signature: dict[str, list[float]] = defaultdict(list)
        for item in population.values():
            sig = signatures.get(item.vinted_item_id, "other")
            if sig and sig != "other":
                prices_by_signature[sig].append(item.price)

        median_by_signature: dict[str, tuple[float, int]] = {}
        for sig, prices in prices_by_signature.items():
            median, count = compute_robust_median(
                prices, min_samples=self.settings.min_benchmark_samples
            )
            if median is not None:
                median_by_signature[sig] = (median, count)

        # A tracked listing is a deal if it sits well below the median of its OWN
        # product signature (same product+variant).
        for listing in listing_models:
            sig = signatures.get(listing.vinted_item_id)
            if not sig or sig == "other" or sig not in median_by_signature:
                continue

            median, sample_count = median_by_signature[sig]
            price_deal, discount_percent = is_deal(
                vinted_price=listing.price,
                benchmark_price=median,
                discount_threshold_percent=search.discount_threshold_percent,
            )
            if not price_deal:
                continue

            self._save_benchmark(listing, median, sample_count, sig)

            existing = (
                self.db.query(DealSignal)
                .filter(DealSignal.listing_id == listing.id)
                .first()
            )
            if existing:
                continue

            deal = DealSignal(
                listing_id=listing.id,
                vinted_price=listing.price,
                benchmark_price=median,
                discount_percent=discount_percent,
                match_confidence=1.0,
            )
            self.db.add(deal)
            self.db.flush()

            if self._notify_deal(deal, listing):
                deal.is_notified = True

            deals_found += 1

        self.db.commit()
        return deals_found

    def _signatures_for(self, items: list[VintedListingData]) -> dict[str, str]:
        """Return {vinted_item_id: signature}, classifying only uncached items."""
        item_ids = [item.vinted_item_id for item in items]
        cached: dict[str, str] = {
            row.vinted_item_id: row.signature
            for row in self.db.query(ProductSignature).filter(
                ProductSignature.vinted_item_id.in_(item_ids)
            )
        }

        missing = [item for item in items if item.vinted_item_id not in cached]
        if not missing:
            return cached

        known = sorted({sig for sig in cached.values() if sig != "other"})
        for start in range(0, len(missing), SIGNATURE_BATCH_SIZE):
            batch = missing[start : start + SIGNATURE_BATCH_SIZE]
            try:
                sigs = self.signature_classifier.classify_signatures(
                    [item.title for item in batch], known_signatures=known
                )
            except Exception:  # noqa: BLE001 - signatures are best-effort
                logger.exception("Signature classification failed for a batch")
                sigs = ["other"] * len(batch)

            for item, sig in zip(batch, sigs):
                cached[item.vinted_item_id] = sig
                self.db.add(
                    ProductSignature(
                        vinted_item_id=item.vinted_item_id,
                        signature=sig,
                        title=item.title,
                    )
                )
                if sig != "other" and sig not in known:
                    known.append(sig)

        self.db.commit()
        return cached

    def _upsert_listing(self, search: MonitoredSearch, listing_data) -> VintedListing:
        listing = (
            self.db.query(VintedListing)
            .filter(VintedListing.vinted_item_id == listing_data.vinted_item_id)
            .first()
        )
        now = datetime.utcnow()

        if listing:
            listing.search_id = search.id
            listing.title = listing_data.title
            listing.price = listing_data.price
            listing.url = listing_data.url
            listing.last_seen_at = now
            return listing

        listing = VintedListing(
            search_id=search.id,
            vinted_item_id=listing_data.vinted_item_id,
            title=listing_data.title,
            price=listing_data.price,
            currency=listing_data.currency,
            condition=listing_data.condition,
            url=listing_data.url,
            image_url=listing_data.image_url,
            first_seen_at=now,
            last_seen_at=now,
        )
        self.db.add(listing)
        self.db.flush()
        return listing

    def _save_benchmark(
        self, listing: VintedListing, median_price: float, sample_count: int, signature: str
    ) -> None:
        record = PriceBenchmark(
            listing_id=listing.id,
            source="vinted_signature",
            median_price=median_price,
            sample_count=sample_count,
            raw_prices=json.dumps({"signature": signature}),
        )
        self.db.add(record)

    def _notify_deal(self, deal: DealSignal, listing: VintedListing) -> bool:
        if not self.telegram_notifier.configured():
            return False

        message = self.telegram_notifier.format_deal_message(
            title=listing.title,
            vinted_price=deal.vinted_price,
            benchmark_price=deal.benchmark_price,
            discount_percent=deal.discount_percent,
            url=listing.url,
        )

        sent = self.telegram_notifier.send_message(message, item_key=listing.vinted_item_id)
        status = "sent" if sent else "skipped"
        self.db.add(
            NotificationLog(
                deal_signal_id=deal.id,
                channel="telegram",
                status=status,
                message=message.text,
            )
        )
        return sent
