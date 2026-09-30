"""Public API contracts. Source validation lives in data_validation.py."""
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_id: str = Field(min_length=1, max_length=100)


class BenchmarkRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    count: Literal[10, 100, 1000] = 10
    concurrency: int = Field(default=5, ge=1, le=10, strict=True)


class ClientSummary(BaseModel):
    id: str
    name: str
    age: int | None
    city: str
    country: str
    balance: float
    transaction_count: int = Field(ge=0)
    personalization_allowed: bool


class ClientPage(BaseModel):
    items: list[ClientSummary]
    total: int


class ClientDetail(BaseModel):
    client: ClientSummary
    facts: dict[str, Any]
    transactions: list[dict[str, Any]]


class TransactionPage(BaseModel):
    items: list[dict[str, Any]]
    total: int


class Product(BaseModel):
    id: str
    name: str
    description: str


class ProductPage(BaseModel):
    items: list[Product]


class Metrics(BaseModel):
    model_config = ConfigDict(extra="allow")
    duration_ms: float = Field(ge=0)
    api_calls: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0)
    usage_source: Literal["provider", "estimated", "none"]


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    client: ClientSummary
    status: Literal["recommended", "insufficient_information", "no_match", "opt_out", "error"]
    summary: str
    profiles: list[dict[str, Any]]
    facts: dict[str, Any]
    missing_information: list[str]
    category: dict[str, Any] | None = None
    ads: list[dict[str, Any]]
    products_evaluated: int
    metrics: Metrics
    stages: list[dict[str, Any]]
    error: str | None = None


class BenchmarkResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    status: Literal["running", "completed", "cancelled", "failed"]
    requested_count: int
    completed_count: int
    concurrency: int
    elapsed_ms: float
    results: list[AnalysisResponse]
    metrics: Metrics
    error: str | None = None


class HistoryPage(BaseModel):
    items: list[dict[str, Any]]
    total: int
