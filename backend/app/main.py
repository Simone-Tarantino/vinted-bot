import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deals import router as deals_router
from app.api.searches import get_session_factory, router as searches_router
from app.api.session import router as session_router
from app.config import get_settings
from app.schemas import HealthResponse
from app.services.scheduler import JobScheduler

logger = logging.getLogger(__name__)
job_scheduler: JobScheduler | None = None


@asynccontextmanager
async def lifespan(_: FastAPI):
    global job_scheduler
    settings = get_settings()
    session_factory = get_session_factory()
    job_scheduler = JobScheduler(session_factory=session_factory, settings=settings)
    if not settings.disable_scheduler:
        job_scheduler.start()
    logger.info("Application started")
    yield
    if job_scheduler:
        job_scheduler.shutdown()
    logger.info("Application stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Vinted Deal Agent", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(searches_router)
    app.include_router(deals_router)
    app.include_router(session_router)

    @app.get("/health", response_model=HealthResponse)
    def healthcheck() -> HealthResponse:
        gemini_ok = settings.gemini_configured()
        return HealthResponse(
            status="ok" if gemini_ok else "degraded",
            gemini_configured=gemini_ok,
            database="connected",
            timestamp=datetime.utcnow(),
        )

    @app.post("/scan/run")
    def run_scan_now() -> dict:
        if job_scheduler is None:
            return {"status": "scheduler_not_ready"}
        job_scheduler.run_now()
        return {"status": "triggered"}

    return app


app = create_app()
