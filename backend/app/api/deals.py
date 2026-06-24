from typing import Generator

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.api.searches import get_db
from app.db.models import DealSignal, JobRun, VintedListing
from app.schemas import DealResponse, JobRunResponse, ListingResponse

router = APIRouter(tags=["deals"])


@router.get("/deals", response_model=list[DealResponse])
def list_deals(db: Session = Depends(get_db)) -> list[DealSignal]:
    return (
        db.query(DealSignal)
        .options(joinedload(DealSignal.listing))
        .order_by(DealSignal.created_at.desc())
        .limit(100)
        .all()
    )


@router.get("/listings", response_model=list[ListingResponse])
def list_listings(db: Session = Depends(get_db)) -> list[VintedListing]:
    return (
        db.query(VintedListing)
        .order_by(VintedListing.last_seen_at.desc())
        .limit(100)
        .all()
    )


@router.get("/jobs", response_model=list[JobRunResponse])
def list_jobs(db: Session = Depends(get_db)) -> list[JobRun]:
    return db.query(JobRun).order_by(JobRun.started_at.desc()).limit(50).all()
