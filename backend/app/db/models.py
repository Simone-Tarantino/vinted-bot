from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class MonitoredSearch(Base):
    __tablename__ = "monitored_searches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query: Mapped[str] = mapped_column(String(500), nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(200))
    size: Mapped[Optional[str]] = mapped_column(String(50))
    max_price: Mapped[Optional[float]] = mapped_column(Float)
    discount_threshold_percent: Mapped[float] = mapped_column(Float, default=20.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    listings: Mapped[list["VintedListing"]] = relationship(back_populates="search")


class VintedListing(Base):
    __tablename__ = "vinted_listings"
    __table_args__ = (UniqueConstraint("vinted_item_id", name="uq_vinted_item_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    search_id: Mapped[int] = mapped_column(ForeignKey("monitored_searches.id"), nullable=False)
    vinted_item_id: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="EUR")
    condition: Mapped[Optional[str]] = mapped_column(String(100))
    url: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(Text)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    search: Mapped["MonitoredSearch"] = relationship(back_populates="listings")
    benchmarks: Mapped[list["PriceBenchmark"]] = relationship(back_populates="listing")
    deal_signals: Mapped[list["DealSignal"]] = relationship(back_populates="listing")


class PriceBenchmark(Base):
    __tablename__ = "price_benchmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("vinted_listings.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="ebay_sold")
    median_price: Mapped[float] = mapped_column(Float, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_prices: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    listing: Mapped["VintedListing"] = relationship(back_populates="benchmarks")


class DealSignal(Base):
    __tablename__ = "deal_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("vinted_listings.id"), nullable=False)
    vinted_price: Mapped[float] = mapped_column(Float, nullable=False)
    benchmark_price: Mapped[float] = mapped_column(Float, nullable=False)
    discount_percent: Mapped[float] = mapped_column(Float, nullable=False)
    match_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    is_notified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    listing: Mapped["VintedListing"] = relationship(back_populates="deal_signals")
    notifications: Mapped[list["NotificationLog"]] = relationship(back_populates="deal_signal")


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deal_signal_id: Mapped[int] = mapped_column(ForeignKey("deal_signals.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), default="telegram")
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    deal_signal: Mapped["DealSignal"] = relationship(back_populates="notifications")


class JobRun(Base):
    __tablename__ = "job_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


def create_db_engine(database_url: str):
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        if database_url.endswith(":memory:") or database_url == "sqlite://":
            return create_engine(
                database_url,
                connect_args=connect_args,
                poolclass=StaticPool,
            )
        return create_engine(database_url, connect_args=connect_args)
    return create_engine(database_url)


def create_session_factory(database_url: str):
    engine = create_db_engine(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)
