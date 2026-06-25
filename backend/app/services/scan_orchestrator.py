import json
import logging
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
    VintedListing,
)
from app.services.ai_matcher import AIMatcher
from app.services.deal_engine import is_deal
from app.services.ebay_comparator import EbayComparator
from app.services.gemini_client import GeminiClient, GeminiConfigurationError
from app.services.telegram_notifier import TelegramNotifier
from app.services.vinted_worker import (
    VintedSessionStore,
    VintedWorker,
    build_vinted_benchmark,
)

logger = logging.getLogger(__name__)


class ScanOrchestrator:
    def __init__(
        self,
        db: Session,
        settings: Optional[Settings] = None,
        vinted_worker: Optional[VintedWorker] = None,
        ebay_comparator: Optional[EbayComparator] = None,
        ai_matcher: Optional[AIMatcher] = None,
        telegram_notifier: Optional[TelegramNotifier] = None,
    ):
        self.db = db
        self.settings = settings or get_settings()

        session_store = VintedSessionStore(
            encryption_key=self.settings.vinted_session_encryption_key,
            session_file=self.settings.vinted_session_file,
        )
        self.vinted_worker = vinted_worker or VintedWorker(session_store=session_store)
        self.ebay_comparator = ebay_comparator or EbayComparator(
            enabled=self.settings.ebay_benchmark_enabled
        )

        if ai_matcher is not None:
            self.ai_matcher = ai_matcher
        else:
            gemini = GeminiClient(
                api_key=self.settings.gemini_api_key,
                model_name=self.settings.gemini_model,
            )
            self.ai_matcher = AIMatcher(gemini_client=gemini)

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
        # activity even if the benchmark or AI matching steps below fail.
        listing_models = [self._upsert_listing(search, data) for data in listings]
        self.db.commit()

        # Prefer an external eBay benchmark when enabled; otherwise use the robust
        # median of comparable Vinted asking prices (free, no browser). The Vinted
        # benchmark uses an unfiltered fetch so the median reflects the whole
        # market, not just the cheap end the user filters to.
        benchmark = self.ebay_comparator.fetch_benchmark(search.query, search.brand)
        if benchmark is None:
            broad_listings = (
                self.vinted_worker.search(query=search.query, brand=search.brand)
                if search.max_price is not None
                else listings
            )
            benchmark = build_vinted_benchmark(broad_listings)

        if benchmark is None:
            logger.info(
                "No benchmark for search id=%s; tracked %s listings without deal evaluation",
                search.id,
                len(listing_models),
            )
            return 0

        # Gate on the free price check first, then evaluate only the cheapest
        # candidates with the (slow, paid) AI matcher up to a hard cap.
        candidates = []
        for listing in listing_models:
            self._save_benchmark(listing, benchmark)
            price_deal, _ = is_deal(
                vinted_price=listing.price,
                benchmark_price=benchmark.median_price,
                discount_threshold_percent=search.discount_threshold_percent,
            )
            if price_deal:
                candidates.append(listing)

        candidates.sort(key=lambda item: item.price)
        capped = candidates[: self.settings.max_ai_evaluations_per_search]
        if len(candidates) > len(capped):
            logger.info(
                "search id=%s: %s price candidates, evaluating cheapest %s with AI",
                search.id,
                len(candidates),
                len(capped),
            )

        for listing in capped:
            try:
                is_match, discount_percent, confidence, _ = self.ai_matcher.evaluate(
                    vinted_title=listing.title,
                    vinted_price=listing.price,
                    vinted_condition=listing.condition,
                    benchmark_price=benchmark.median_price,
                    discount_threshold_percent=search.discount_threshold_percent,
                    reference_titles=benchmark.titles,
                )
            except Exception:  # noqa: BLE001 - isolate per-listing AI failures
                logger.exception("AI evaluation failed for listing id=%s", listing.id)
                continue

            if not is_match:
                continue

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
                benchmark_price=benchmark.median_price,
                discount_percent=discount_percent,
                match_confidence=confidence,
            )
            self.db.add(deal)
            self.db.flush()

            if self._notify_deal(deal, listing):
                deal.is_notified = True

            deals_found += 1

        self.db.commit()
        return deals_found

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

    def _save_benchmark(self, listing: VintedListing, benchmark) -> None:
        source = "ebay_sold" if type(benchmark).__name__ == "EbayBenchmark" else "vinted_median"
        record = PriceBenchmark(
            listing_id=listing.id,
            source=source,
            median_price=benchmark.median_price,
            sample_count=benchmark.sample_count,
            raw_prices=json.dumps(benchmark.prices),
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
