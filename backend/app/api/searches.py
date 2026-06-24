from datetime import datetime
from typing import Generator

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import MonitoredSearch, create_session_factory
from app.config import get_settings
from app.schemas import SearchCreate, SearchResponse, SearchUpdate

router = APIRouter(prefix="/searches", tags=["searches"])

_session_factory = None


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        settings = get_settings()
        _session_factory = create_session_factory(settings.database_url)
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[SearchResponse])
def list_searches(db: Session = Depends(get_db)) -> list[MonitoredSearch]:
    return db.query(MonitoredSearch).order_by(MonitoredSearch.created_at.desc()).all()


@router.post("", response_model=SearchResponse, status_code=status.HTTP_201_CREATED)
def create_search(payload: SearchCreate, db: Session = Depends(get_db)) -> MonitoredSearch:
    search = MonitoredSearch(
        query=payload.query,
        brand=payload.brand,
        size=payload.size,
        max_price=payload.max_price,
        discount_threshold_percent=payload.discount_threshold_percent,
    )
    db.add(search)
    db.commit()
    db.refresh(search)
    return search


@router.get("/{search_id}", response_model=SearchResponse)
def get_search(search_id: int, db: Session = Depends(get_db)) -> MonitoredSearch:
    search = db.query(MonitoredSearch).filter(MonitoredSearch.id == search_id).first()
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")
    return search


@router.patch("/{search_id}", response_model=SearchResponse)
def update_search(
    search_id: int,
    payload: SearchUpdate,
    db: Session = Depends(get_db),
) -> MonitoredSearch:
    search = db.query(MonitoredSearch).filter(MonitoredSearch.id == search_id).first()
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(search, field, value)
    search.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(search)
    return search


@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_search(search_id: int, db: Session = Depends(get_db)) -> None:
    search = db.query(MonitoredSearch).filter(MonitoredSearch.id == search_id).first()
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")
    db.delete(search)
    db.commit()
