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


class ObservedSegment(BaseModel):
    id: str
    label: str
    description: str
    evidence: list[str]


class CustomerContext(BaseModel):
    observation_days: int = Field(ge=0)
    monthly_income_cents: int = Field(ge=0)
    savings_cents: int = Field(ge=0)
    investment_cents: int = Field(ge=0)
    recurring_payment_count: int = Field(ge=0)
    summary: str


class DashboardAdvert(BaseModel):
    product_id: str
    product_name: str
    title: str
    reason: str
    confidence: float = Field(ge=0, le=1)


class DashboardCategory(BaseModel):
    id: str
    label: str


class DashboardAnalysis(BaseModel):
    status: Literal["not_analyzed", "recommended", "insufficient_information", "no_match", "opt_out", "error"]
    category: DashboardCategory | None
    summary: str
    created_at: str | None
    source: Literal["analysis", "benchmark"] | None
    id: str | None
    ads: list[DashboardAdvert]


class DashboardClient(BaseModel):
    client: ClientSummary
    segments: list[ObservedSegment]
    context: CustomerContext
    analysis: DashboardAnalysis


class DashboardClientPage(BaseModel):
    items: list[DashboardClient]
    total: int = Field(ge=0)


class DashboardSummary(BaseModel):
    total_clients: int
    opt_in_count: int
    opt_out_count: int
    analyzed_count: int
    recommended_count: int
    not_analyzed_count: int
    abstained_count: int
    error_count: int
    selected_ad_count: int
    total_balance_cents: int
    total_transactions: int


class SegmentCount(BaseModel):
    id: str
    label: str
    count: int
    description: str


class OutcomeCount(BaseModel):
    id: str
    label: str
    count: int


class ProductCount(BaseModel):
    id: str
    name: str
    count: int


class DashboardCashflow(BaseModel):
    month: str
    credit_cents: int
    debit_cents: int


class NetworkNode(BaseModel):
    id: str
    label: str
    kind: Literal["segment", "client", "product"]
    client_id: str | None = None
    count: int | None = None


class NetworkLink(BaseModel):
    source: str
    target: str
    kind: Literal["segment", "recommendation"]


class DashboardNetwork(BaseModel):
    nodes: list[NetworkNode]
    links: list[NetworkLink]
    shown_clients: int
    total_clients: int


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    segments: list[SegmentCount]
    outcomes: list[OutcomeCount]
    products: list[ProductCount]
    cashflow: list[DashboardCashflow]
    clients: DashboardClientPage
    network: DashboardNetwork
    generated_at: str
