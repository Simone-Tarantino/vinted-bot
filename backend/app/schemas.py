from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SearchCreate(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    brand: Optional[str] = None
    size: Optional[str] = None
    max_price: Optional[float] = Field(None, gt=0)
    discount_threshold_percent: float = Field(default=20.0, ge=0, le=90)


class SearchUpdate(BaseModel):
    query: Optional[str] = Field(None, min_length=1, max_length=500)
    brand: Optional[str] = None
    size: Optional[str] = None
    max_price: Optional[float] = Field(None, gt=0)
    discount_threshold_percent: Optional[float] = Field(None, ge=0, le=90)
    is_active: Optional[bool] = None


class SearchResponse(BaseModel):
    id: int
    query: str
    brand: Optional[str]
    size: Optional[str]
    max_price: Optional[float]
    discount_threshold_percent: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ListingResponse(BaseModel):
    id: int
    search_id: int
    vinted_item_id: str
    title: str
    price: float
    currency: str
    condition: Optional[str]
    url: str
    image_url: Optional[str]
    first_seen_at: datetime
    last_seen_at: datetime

    model_config = {"from_attributes": True}


class DealResponse(BaseModel):
    id: int
    listing_id: int
    vinted_price: float
    benchmark_price: float
    discount_percent: float
    match_confidence: float
    is_notified: bool
    created_at: datetime
    listing: Optional[ListingResponse] = None

    model_config = {"from_attributes": True}


class JobRunResponse(BaseModel):
    id: int
    job_name: str
    status: str
    details: Optional[str]
    started_at: datetime
    finished_at: Optional[datetime]

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status: str
    gemini_configured: bool
    database: str
    timestamp: datetime
