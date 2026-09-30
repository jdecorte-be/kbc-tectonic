from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

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
