from typing import Optional

from app.services.deal_engine import is_deal
from app.services.gemini_client import GeminiClient, MatchResult


class AIMatcher:
    def __init__(self, gemini_client: GeminiClient, min_confidence: float = 0.7):
        self.gemini_client = gemini_client
        self.min_confidence = min_confidence

    def evaluate(
        self,
        vinted_title: str,
        vinted_price: float,
        vinted_condition: Optional[str],
        benchmark_price: float,
        discount_threshold_percent: float,
        reference_titles: list[str],
    ) -> tuple[bool, float, float, MatchResult]:
        deal, discount_percent = is_deal(
            vinted_price=vinted_price,
            benchmark_price=benchmark_price,
            discount_threshold_percent=discount_threshold_percent,
        )

        # Only spend a Gemini call on listings cheap enough to be a candidate deal;
        # the price gate is free and filters out the vast majority of listings.
        if not deal:
            return False, discount_percent, 0.0, MatchResult(
                is_match=False,
                confidence=0.0,
                normalized_title="",
                reasoning="price above discount threshold",
            )

        match_result = self.gemini_client.match_listings(
            vinted_title=vinted_title,
            vinted_condition=vinted_condition,
            reference_titles=reference_titles,
        )

        is_valid = match_result.is_match and match_result.confidence >= self.min_confidence
        return is_valid, discount_percent, match_result.confidence, match_result
