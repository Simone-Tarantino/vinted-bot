import statistics
from typing import Iterable


def trim_outliers(prices: list[float], z_threshold: float = 2.0) -> list[float]:
    if len(prices) < 3:
        return prices

    mean = statistics.mean(prices)
    stdev = statistics.pstdev(prices)
    if stdev == 0:
        return prices

    return [price for price in prices if abs(price - mean) / stdev <= z_threshold]


def compute_robust_median(prices: Iterable[float], min_samples: int = 5) -> tuple[float | None, int]:
    values = [float(price) for price in prices if price is not None and price > 0]
    if len(values) < min_samples:
        return None, len(values)

    trimmed = trim_outliers(values)
    if not trimmed:
        return None, len(values)

    return statistics.median(trimmed), len(trimmed)


def is_deal(
    vinted_price: float,
    benchmark_price: float,
    discount_threshold_percent: float,
) -> tuple[bool, float]:
    if benchmark_price <= 0:
        return False, 0.0

    discount_percent = ((benchmark_price - vinted_price) / benchmark_price) * 100
    threshold = benchmark_price * (1 - discount_threshold_percent / 100)
    return vinted_price <= threshold, round(discount_percent, 2)
