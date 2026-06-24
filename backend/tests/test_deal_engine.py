import pytest

from app.services.deal_engine import compute_robust_median, is_deal, trim_outliers


def test_trim_outliers_removes_extreme_values():
    prices = [10, 11, 12, 13, 14, 15, 16, 200]
    trimmed = trim_outliers(prices)
    assert 200 not in trimmed
    assert len(trimmed) >= 5


def test_compute_robust_median_requires_min_samples():
    median, count = compute_robust_median([10, 12, 14], min_samples=5)
    assert median is None
    assert count == 3


def test_compute_robust_median_returns_median():
    prices = [10, 12, 14, 13, 11, 12, 15]
    median, count = compute_robust_median(prices, min_samples=5)
    assert median == 12
    assert count == 7


def test_is_deal_below_threshold():
    is_good_deal, discount = is_deal(
        vinted_price=40,
        benchmark_price=100,
        discount_threshold_percent=20,
    )
    assert is_good_deal is True
    assert discount == 60.0


def test_is_deal_above_threshold():
    is_good_deal, discount = is_deal(
        vinted_price=90,
        benchmark_price=100,
        discount_threshold_percent=20,
    )
    assert is_good_deal is False
    assert discount == 10.0
