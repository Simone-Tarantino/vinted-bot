import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Optional

import google.generativeai as genai


class GeminiConfigurationError(Exception):
    pass


class GeminiResponseError(Exception):
    pass


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
        model_name: str = "gemini-2.0-flash",
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

    def _call_model(self, prompt: str) -> str:
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                if self._generate_fn is not None:
                    text = self._generate_fn(prompt)
                else:
                    response = self._model.generate_content(
                        prompt,
                        request_options={"timeout": self.timeout_seconds},
                    )
                    text = getattr(response, "text", None)

                if not text:
                    raise GeminiResponseError("Empty response from Gemini")
                return text
            except Exception as exc:  # noqa: BLE001 - retry wrapper
                last_error = exc
                if attempt == self.max_retries - 1:
                    raise GeminiResponseError(str(exc)) from exc
        raise GeminiResponseError(str(last_error))

    def match_listings(
        self,
        vinted_title: str,
        vinted_condition: Optional[str],
        ebay_titles: list[str],
    ) -> MatchResult:
        prompt = (
            "You compare second-hand product listings. "
            "Return ONLY valid JSON with keys: is_match (bool), confidence (0-1 float), "
            "normalized_title (string), reasoning (short string).\n"
            f"Vinted listing: title='{vinted_title}', condition='{vinted_condition or 'unknown'}'\n"
            f"eBay sold titles: {json.dumps(ebay_titles[:10])}\n"
            "Decide if eBay titles refer to the same product model/variant."
        )
        raw = self._call_model(prompt)
        return self._parse_match_result(raw)

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
