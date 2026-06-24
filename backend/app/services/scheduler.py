import logging
from typing import Callable, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings, get_settings
from app.services.scan_orchestrator import ScanOrchestrator

logger = logging.getLogger(__name__)


class JobScheduler:
    def __init__(
        self,
        session_factory: sessionmaker,
        settings: Optional[Settings] = None,
        scan_runner: Optional[Callable[[], None]] = None,
    ):
        self.session_factory = session_factory
        self.settings = settings or get_settings()
        self._scan_runner = scan_runner or self._default_scan_runner
        self.scheduler = BackgroundScheduler()

    def _default_scan_runner(self) -> None:
        db: Session = self.session_factory()
        try:
            orchestrator = ScanOrchestrator(db=db, settings=self.settings)
            job = orchestrator.run_scan()
            logger.info("Scan completed with status=%s details=%s", job.status, job.details)
        finally:
            db.close()

    def start(self) -> None:
        if self.scheduler.running:
            return

        self.scheduler.add_job(
            self._scan_runner,
            trigger=IntervalTrigger(minutes=self.settings.scan_interval_minutes),
            id="scan_all_searches",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        self.scheduler.start()
        logger.info(
            "Scheduler started with interval=%s minutes",
            self.settings.scan_interval_minutes,
        )

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def run_now(self) -> None:
        self._scan_runner()
