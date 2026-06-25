import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Callable, Optional

import google.generativeai as genai

logger = logging.getLogger(__name__)


class GeminiConfigurationError(Exception):
    pass


class GeminiResponseError(Exception):
    pass


# Tried in order when the configured model is rejected by the API as missing or
# retired (e.g. a stale GEMINI_MODEL pointing at a decommissioned model).
FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-flash-latest"]


def _is_model_unavailable_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "no longer available" in message or "not found" in message or "404" in message


@dataclass
class MatchResult:
    is_match: bool
    confidence: float
    normalized_title: str
    reasoning: str


class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        generate_fn: Optional[Callable[..., Any]] = None,
        max_retries: int = 3,
        timeout_seconds: int = 30,
    ):
        if not api_key or not api_key.strip():
            raise GeminiConfigurationError("GEMINI_API_KEY is required")

        self.api_key = api_key.strip()
        self.model_name = model_name
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self._generate_fn = generate_fn

        genai.configure(api_key=self.api_key)
        self._model = genai.GenerativeModel(self.model_name)
        # Fallback models not equal to the configured one, tried if it is retired.
        self._fallback_models = [m for m in FALLBACK_MODELS if m != self.model_name]

    def _generate(self, prompt: str) -> Optional[str]:
        if self._generate_fn is not None:
            return self._generate_fn(prompt)
        response = self._model.generate_content(
            prompt,
            request_options={"timeout": self.timeout_seconds},
        )
        return getattr(response, "text", None)

    def _switch_to_fallback_model(self) -> bool:
        while self._fallback_models:
            candidate = self._fallback_models.pop(0)
            logger.warning(
                "Gemini model %r unavailable; falling back to %r", self.model_name, candidate
            )
            self.model_name = candidate
            self._model = genai.GenerativeModel(candidate)
            return True
        return False

    def _call_model(self, prompt: str) -> str:
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                text = self._generate(prompt)
                if not text:
                    raise GeminiResponseError("Empty response from Gemini")
                return text
            except Exception as exc:  # noqa: BLE001 - retry wrapper
                last_error = exc
                # A retired/missing model won't fix itself on retry: switch model.
                if _is_model_unavailable_error(exc) and self._switch_to_fallback_model():
                    continue
                if attempt == self.max_retries - 1:
                    raise GeminiResponseError(str(exc)) from exc
        raise GeminiResponseError(str(last_error))

    def match_listings(
        self,
        vinted_title: str,
        vinted_condition: Optional[str],
        reference_titles: list[str],
    ) -> MatchResult:
        prompt = (
            "You compare second-hand product listings. "
            "Return ONLY valid JSON with keys: is_match (bool), confidence (0-1 float), "
            "normalized_title (string), reasoning (short string).\n"
            f"Candidate listing: title='{vinted_title}', condition='{vinted_condition or 'unknown'}'\n"
            f"Comparable listing titles: {json.dumps(reference_titles[:10])}\n"
            "Decide if the candidate is the same product model/variant as the comparable "
            "listings (not an accessory, empty box, wanted/'cerco' ad, or different set)."
        )
        raw = self._call_model(prompt)
        return self._parse_match_result(raw)

    def classify_signatures(
        self, titles: list[str], known_signatures: Optional[list[str]] = None
    ) -> list[str]:
        """Assign each title a canonical product signature so identical
        products/variants group together. Returns one signature per title,
        in the same order. Falls back to 'other' on length mismatch.
        """
        if not titles:
            return []

        prompt = (
            "You normalize second-hand listing titles into canonical product "
            "signatures so that identical products group together for price "
            "comparison. A signature is a short lowercase string of the form "
            "'brand | product line | variant' identifying the exact product AND "
            "variant (e.g. 'pokemon | primi compagni avventura | serie 1 set completo' "
            "vs '... | serie 1 busta' vs '... | serie 1 carta singola'). "
            "Use exactly 'other' for wanted/'cerco' ads, swaps, accessories, empty "
            "boxes, or lots of mixed/unrelated items. Reuse a known signature "
            "verbatim whenever it fits instead of inventing a near-duplicate.\n"
            f"Known signatures: {json.dumps(known_signatures or [], ensure_ascii=False)}\n"
            f"Titles (in order): {json.dumps(titles, ensure_ascii=False)}\n"
            "Return ONLY a JSON array of strings, one signature per title, "
            "exactly same order and length as the titles."
        )
        raw = self._call_model(prompt)
        signatures = self._parse_signature_list(raw)
        if len(signatures) != len(titles):
            logger.warning(
                "Signature count mismatch (%s titles, %s signatures); using 'other'",
                len(titles),
                len(signatures),
            )
            return ["other"] * len(titles)
        return [s.strip().lower() or "other" for s in signatures]

    @staticmethod
    def _parse_signature_list(raw: str) -> list[str]:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise GeminiResponseError("Invalid JSON signature list from Gemini") from exc
        if not isinstance(payload, list):
            raise GeminiResponseError("Signature response is not a JSON array")
        return [str(item) for item in payload]

    @staticmethod
    def _parse_match_result(raw: str) -> MatchResult:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            payload = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise GeminiResponseError("Invalid JSON from Gemini") from exc

        return MatchResult(
            is_match=bool(payload.get("is_match", False)),
            confidence=float(payload.get("confidence", 0.0)),
            normalized_title=str(payload.get("normalized_title", "")),
            reasoning=str(payload.get("reasoning", "")),
        )
