from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings
from app.services.vinted_worker import VintedSessionStore, VintedWorker

router = APIRouter(prefix="/session", tags=["session"])


class SessionImportRequest(BaseModel):
    cookies: list[dict[str, Any]]


@router.post("/vinted/import")
def import_vinted_session(payload: SessionImportRequest) -> dict:
    settings = get_settings()
    store = VintedSessionStore(
        encryption_key=settings.vinted_session_encryption_key,
        session_file=settings.vinted_session_file,
    )
    worker = VintedWorker(session_store=store)
    worker.import_session_cookies(payload.cookies)
    return {"status": "saved", "cookie_count": len(payload.cookies)}


@router.get("/vinted/status")
def vinted_session_status() -> dict:
    settings = get_settings()
    store = VintedSessionStore(
        encryption_key=settings.vinted_session_encryption_key,
        session_file=settings.vinted_session_file,
    )
    worker = VintedWorker(session_store=store)
    return {"session_exists": worker.session_exists()}
