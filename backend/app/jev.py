"""Async adapter for TypeSafe's typed decision API.

API contract: https://api.typesafe.ai/openapi.json (verified 2026-09-30).
Prices: https://typesafe.ai/blog/introducing-system-one-models-and-jev
($0.042 / million input tokens; output tokens free at verification time).

``JevClient().decide(state, questions)`` returns validated, unchanged answer
objects. Missing token usage is estimated using UTF-8 bytes / 4 and explicitly
labelled; provider counts remain separately available. Costs are estimates, never
a billing statement. Failed attempts have unknown billable usage, so their input
cost is conservatively estimated from request size and reported separately.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Annotated, Any, Literal
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError


DEFAULT_ENDPOINT = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-latest"
PRICING_SOURCE = "https://typesafe.ai/blog/introducing-system-one-models-and-jev"
DEFAULT_INPUT_USD_PER_MILLION = 0.042
DEFAULT_OUTPUT_USD_PER_MILLION = 0.0
RETRYABLE_STATUSES = {408, 429, 500, 502, 503, 504}
Probability = Annotated[float, Field(ge=0, le=1, strict=True, allow_inf_nan=False)]


class _NoulAnswer(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: Literal["noul"]
    noul: Probability


class _ChoiceAnswer(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: Literal["choice"]
    choice: str
    confidence: Probability
    probabilities: dict[str, Probability]


class _ScoreAnswer(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: Literal["score"]
    score: Annotated[float, Field(strict=True, allow_inf_nan=False)]
    confidence: Probability
    legend: dict[str, Any]
    probabilities: dict[str, Probability]


_ANSWER = TypeAdapter(
    Annotated[_NoulAnswer | _ChoiceAnswer | _ScoreAnswer, Field(discriminator="type")]
)


@dataclass(frozen=True)
class JevResult:
    """One successful decision, including retry time and cost accounting.

    ``input_tokens`` and ``output_tokens`` describe the successful response.
    Their values are estimated only when the corresponding provider count is
    absent. ``provider_*`` preserve absence as None. ``estimated_cost_usd`` also
    includes an estimate for requests retried without reported usage.
    """

    answers: dict[str, dict[str, Any]]
    model: str
    input_tokens: int
    output_tokens: int
    tokens_estimated: bool
    request_count: int
    retry_count: int
    duration_ms: float
    estimated_cost_usd: float
    provider_input_tokens: int | None = None
    provider_output_tokens: int | None = None
    estimated_retry_input_tokens: int = 0
    estimated_retry_cost_usd: float = 0.0
    cost_is_estimate: bool = True
    pricing: dict[str, Any] = field(default_factory=dict)


class JevError(Exception):
    """Safe public error: no request body, upstream response body or credentials."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "jev_error",
        request_count: int = 0,
        duration_ms: float = 0.0,
        estimated_cost_usd: float = 0.0,
        estimated_input_tokens: int = 0,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.request_count = request_count
        self.retry_count = max(0, request_count - 1)
        self.duration_ms = duration_ms
        self.estimated_cost_usd = estimated_cost_usd
        self.estimated_input_tokens = estimated_input_tokens
        self.tokens_estimated = request_count > 0


class JevClient:
    """Reusable client owned by application lifespan; call ``await close()``.

    Environment: JEV_API (secret), JEV_API_URL (full endpoint or base URL),
    JEV_MODEL, JEV_TIMEOUT_SECONDS, JEV_MAX_RETRIES,
    JEV_INPUT_USD_PER_MILLION, JEV_OUTPUT_USD_PER_MILLION.
    No network request occurs during construction. An injected httpx client is
    useful for tests and remains owned by its caller.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        endpoint: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        input_usd_per_million: float | None = None,
        output_usd_per_million: float | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = (os.getenv("JEV_API", "") if api_key is None else api_key).strip()
        self.endpoint = (endpoint or os.getenv("JEV_API_URL") or DEFAULT_ENDPOINT).rstrip("/")
        parsed = urlsplit(self.endpoint)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
            raise JevError("JEV_API_URL must be a valid HTTP(S) URL.", code="configuration")
        if parsed.path in {"", "/"}:
            self.endpoint += "/v1/systemone"
        elif parsed.path == "/v1":
            self.endpoint += "/systemone"
        self.model = model or os.getenv("JEV_MODEL") or DEFAULT_MODEL
        try:
            self.timeout_seconds = float(timeout_seconds if timeout_seconds is not None else os.getenv("JEV_TIMEOUT_SECONDS", "20"))
            self.max_retries = int(max_retries if max_retries is not None else os.getenv("JEV_MAX_RETRIES", "2"))
            self.input_usd_per_million = float(input_usd_per_million if input_usd_per_million is not None else os.getenv("JEV_INPUT_USD_PER_MILLION", str(DEFAULT_INPUT_USD_PER_MILLION)))
            self.output_usd_per_million = float(output_usd_per_million if output_usd_per_million is not None else os.getenv("JEV_OUTPUT_USD_PER_MILLION", str(DEFAULT_OUTPUT_USD_PER_MILLION)))
        except (TypeError, ValueError):
            raise JevError("Invalid numeric Jev configuration.", code="configuration") from None
        if not math.isfinite(self.timeout_seconds) or not 0 < self.timeout_seconds <= 120:
            raise JevError("JEV_TIMEOUT_SECONDS must be greater than 0 and at most 120 seconds.", code="configuration")
        if not 0 <= self.max_retries <= 5:
            raise JevError("JEV_MAX_RETRIES must be between 0 and 5.", code="configuration")
        if any(not math.isfinite(price) or price < 0 for price in (self.input_usd_per_million, self.output_usd_per_million)):
            raise JevError("Jev prices must be non-negative.", code="configuration")
        self._client = client
        self._owns_client = client is None

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    @property
    def pricing_info(self) -> dict[str, Any]:
        return {
            "input_usd_per_million": self.input_usd_per_million,
            "output_usd_per_million": self.output_usd_per_million,
            "currency": "USD",
            "source_url": PRICING_SOURCE,
            "verified_on": "2026-09-30",
            "cost_is_estimate": True,
            "custom_rates": (self.input_usd_per_million != DEFAULT_INPUT_USD_PER_MILLION or self.output_usd_per_million != DEFAULT_OUTPUT_USD_PER_MILLION),
            "retry_cost_basis": "Estimated request input tokens; provider billing for failed attempts is unknown.",
        }

    async def close(self) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None

    async def aclose(self) -> None:
        await self.close()

    async def __aenter__(self) -> JevClient:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    def _http_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_seconds),
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=30),
                follow_redirects=False,
            )
        return self._client

    async def decide(self, state: str, questions: dict[str, Any]) -> JevResult:
        if not self.configured:
            raise JevError("JEV_API is not configured on the server.", code="missing_api_key")
        if not isinstance(state, str) or not state.strip() or not isinstance(questions, dict) or not questions:
            raise JevError("Jev requires a text state and at least one question.", code="invalid_request")
        for question in questions.values():
            if not isinstance(question, dict) or question.get("type") not in {"noul", "choice", "score"}:
                raise JevError("Invalid Jev question type.", code="invalid_request")
            if question["type"] == "choice" and (not isinstance(question.get("criteria"), dict) or not question["criteria"]):
                raise JevError("A choice question requires named criteria.", code="invalid_request")
            if question["type"] == "score" and (not isinstance(question.get("criteria"), list) or not question["criteria"]):
                raise JevError("A score question requires a list of levels.", code="invalid_request")
        payload = {"model": self.model, "state": state, "questions": questions}
        try:
            encoded_payload = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        except (TypeError, ValueError):
            raise JevError("The Jev request must contain valid JSON data.", code="invalid_request") from None
        estimated_input = max(1, math.ceil(len(encoded_payload) / 4))
        estimated_attempt_cost = estimated_input * self.input_usd_per_million / 1_000_000
        started = time.perf_counter()
        request_count = 0
        while True:
            request_count += 1
            response = None
            try:
                # Explicitly disable redirects even for an externally supplied client:
                # credentials must not be forwarded to a location returned upstream.
                response = await self._http_client().post(
                    self.endpoint,
                    headers={"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"},
                    content=encoded_payload,
                    timeout=self.timeout_seconds,
                    follow_redirects=False,
                )
            except httpx.TimeoutException:
                error_code, error_message = "timeout", "The Jev request timed out."
            except httpx.TransportError:
                error_code, error_message = "connection", "Could not connect to Jev."
            else:
                if response.is_success:
                    try:
                        body = response.json()
                        answers, provider_input, provider_output, response_model = self._validate_response(body, questions)
                    except (ValueError, TypeError, ValidationError, KeyError):
                        raise JevError(
                            "Jev returned an invalid structured response.",
                            code="invalid_response", request_count=request_count,
                            duration_ms=(time.perf_counter() - started) * 1000,
                            estimated_cost_usd=estimated_attempt_cost * request_count,
                            estimated_input_tokens=estimated_input * request_count,
                        ) from None
                    input_tokens = provider_input if provider_input is not None else estimated_input
                    output_tokens = provider_output if provider_output is not None else max(1, math.ceil(len(json.dumps(answers).encode("utf-8")) / 4))
                    retry_cost = estimated_attempt_cost * (request_count - 1)
                    return JevResult(
                        answers=answers, model=response_model,
                        input_tokens=input_tokens, output_tokens=output_tokens,
                        tokens_estimated=provider_input is None or provider_output is None,
                        request_count=request_count, retry_count=request_count - 1,
                        duration_ms=(time.perf_counter() - started) * 1000,
                        estimated_cost_usd=(input_tokens * self.input_usd_per_million + output_tokens * self.output_usd_per_million) / 1_000_000 + retry_cost,
                        provider_input_tokens=provider_input, provider_output_tokens=provider_output,
                        estimated_retry_input_tokens=estimated_input * (request_count - 1),
                        estimated_retry_cost_usd=retry_cost, pricing=self.pricing_info,
                    )
                error_code, error_message = self._http_error(response.status_code)
                if response.status_code not in RETRYABLE_STATUSES:
                    raise JevError(error_message, code=error_code, request_count=request_count,
                                   duration_ms=(time.perf_counter() - started) * 1000,
                                   estimated_cost_usd=estimated_attempt_cost * request_count,
                                   estimated_input_tokens=estimated_input * request_count) from None
            if request_count > self.max_retries:
                raise JevError(
                    error_message, code=error_code, request_count=request_count,
                    duration_ms=(time.perf_counter() - started) * 1000,
                    estimated_cost_usd=estimated_attempt_cost * request_count,
                    estimated_input_tokens=estimated_input * request_count,
                ) from None
            await asyncio.sleep(self._retry_delay(response, request_count))

    @staticmethod
    def _http_error(status: int) -> tuple[str, str]:
        if status in {401, 403}:
            return "authentication", "Jev rejected the API key or access to the model."
        if status == 429:
            return "rate_limit", "Jev rate limit reached. Please try again later."
        if status == 402:
            return "credits", "The Jev account has insufficient credits."
        return f"http_{status}", f"Jev returned HTTP status {status}."

    @staticmethod
    def _retry_delay(response: httpx.Response | None, attempt: int) -> float:
        delay = min(0.5 * (2 ** (attempt - 1)), 4.0)
        retry_after = response.headers.get("Retry-After") if response is not None else None
        if retry_after:
            try:
                delay = float(retry_after)
            except ValueError:
                try:
                    parsed = parsedate_to_datetime(retry_after)
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    delay = (parsed - datetime.now(timezone.utc)).total_seconds()
                except (ValueError, TypeError, OverflowError):
                    pass
        return min(10.0, max(0.0, delay)) if math.isfinite(delay) else 1.0

    @staticmethod
    def _validate_response(body: Any, questions: dict[str, Any]) -> tuple[dict, int | None, int | None, str]:
        if not isinstance(body, dict) or not isinstance(body.get("model"), str) or not body["model"]:
            raise ValueError("Invalid model")
        answers = body.get("answers")
        if not isinstance(answers, dict) or set(answers) != set(questions):
            raise ValueError("Missing or unexpected answer keys")
        for key, answer in answers.items():
            parsed = _ANSWER.validate_python(answer)
            question = questions[key]
            if parsed.type != question["type"]:
                raise ValueError("Answer type mismatch")
            if isinstance(parsed, (_ChoiceAnswer, _ScoreAnswer)):
                expected = set(question["criteria"]) if parsed.type == "choice" else {str(i) for i in range(len(question["criteria"]))}
                if set(parsed.probabilities) != expected or not math.isclose(sum(parsed.probabilities.values()), 1.0, abs_tol=0.02):
                    raise ValueError("Invalid probability distribution")
                if isinstance(parsed, _ChoiceAnswer) and parsed.choice not in expected:
                    raise ValueError("Unknown choice")
                if isinstance(parsed, _ScoreAnswer) and (set(parsed.legend) != expected or not 0 <= parsed.score <= len(expected) - 1):
                    raise ValueError("Invalid score")
        usage = body.get("usage")
        if usage is None:
            usage = {}
        if not isinstance(usage, dict):
            raise ValueError("Invalid usage")
        counts = []
        for name in ("input_tokens", "output_tokens"):
            count = usage.get(name)
            if count is not None and (type(count) is not int or count < 0):
                raise ValueError("Invalid usage count")
            counts.append(count)
        return answers, counts[0], counts[1], body["model"]
