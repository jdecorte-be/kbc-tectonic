from typing import Optional, List, Dict, Literal, Tuple
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

class TransactionBase(BaseModel):
    amount: Decimal
    currency: str = "EUR"
    transaction_type: str
    status: str = "completed"
    description: Optional[str] = None

class TransactionCreate(TransactionBase):
    user_id: int

class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    name: str
    phone_number: str
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    is_active: bool = True

    # Profiling & Financial Demographics
    financial_situation: Optional[str] = "balanced"
    is_student: bool = False
    is_unemployed: bool = False
    is_high_income: bool = False
    discretionary_spender: Optional[str] = "moderate"
    main_transportation: Optional[str] = "car"
    children_count: int = 0
    in_couple: bool = False
    has_insurance: bool = True

    # Additional Profile Fields
    housing_status: Optional[str] = "renter"
    age_range: Optional[str] = "26-35"
    savings_goal: Optional[str] = "emergency_fund"
    risk_tolerance: Optional[str] = "medium"

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserDetailResponse(UserResponse):
    transactions: List[TransactionResponse] = []

    model_config = ConfigDict(from_attributes=True)

class HealthCheckResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime

# --- Dashboard (profiled demo clients) ---

class ProfileId(str, Enum):
    student = "student"
    young_investor = "young-investor"
    investor = "investor"
    holiday = "holiday"
    family = "family"
    homebuyer = "homebuyer"
    commuter = "commuter"
    freelancer = "freelancer"
    saver = "saver"
    financial_stress = "financial-stress"
    retiree = "retiree"
    big_event = "big-event"

class Habit(str, Enum):
    travel = "Travel"
    investing = "Investing"
    groceries = "Groceries"
    mobility = "Mobility"
    eating_out = "Eating out"

class ProfileDef(BaseModel):
    id: ProfileId
    label: str
    core: bool
    offer: str

class ProfileScore(BaseModel):
    id: ProfileId
    confidence: float

class Signal(BaseModel):
    text: str
    weight: float = Field(description="0..1 contribution to the profile confidence")

class ClientTransaction(BaseModel):
    date: str
    merchant: str
    category: str
    amount: float = Field(description="Negative = spend")

class HabitChange(BaseModel):
    habit: str
    text: str
    delta: float = Field(description="% vs the client's own baseline")
    severity: Literal["info", "watch", "alert"]

class Client(BaseModel):
    id: str
    name: str
    age: int
    profiles: List[ProfileScore] = Field(description="Highest confidence first")
    monthlySpend: List[float] = Field(description="Last 6 months")
    savingsRate: float
    recurringCount: int
    cashShare: float = Field(description="% of spend in cash")
    payday: int
    topHabit: str
    signals: List[Signal]
    change: Optional[HabitChange] = None
    transactions: List[ClientTransaction]
    lastScanned: datetime

class Relation(BaseModel):
    clientId: str
    kind: Literal["linked", "similar"]
    reason: str
    score: int

class Kpis(BaseModel):
    clientsTracked: int
    profilesDetected: int
    habitChanges: int
    openOpportunities: int

class Segment(BaseModel):
    id: ProfileId
    label: str
    count: int

class WeekPoint(BaseModel):
    date: datetime
    spend: float
    baseline: float

class WeekdaySpend(BaseModel):
    day: str
    spend: float

class JevUsage(BaseModel):
    requests: int
    clientsAnalysed: int
    inputTokens: int
    outputTokens: int
    costUsd: float

class Dashboard(BaseModel):
    kpis: Kpis
    segments: List[Segment]
    habitTrends: Dict[Habit, List[WeekPoint]]
    weekdayRhythm: List[WeekdaySpend]
    links: List[Tuple[str, str, str]] = Field(description="[clientA, clientB, reason]")
    jevUsage: Optional[JevUsage] = None

class JevResult(BaseModel):
    mainProfile: Optional[ProfileId] = None
    mainConfidence: Optional[float] = None
    trackers: List[ProfileScore] = []
    incomeRegularity: Optional[float] = None
    model: Optional[str] = None
    error: Optional[str] = None

class JevTrackers(BaseModel):
    analyzedAt: datetime
    clients: Dict[str, JevResult]
