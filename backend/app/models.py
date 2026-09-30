from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(50), nullable=False, index=True)
    email = Column(String(255), nullable=True, unique=True, index=True)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Profiling & Financial Demographics
    financial_situation = Column(String(50), nullable=True) # comfortable, balanced, tight, critical
    is_student = Column(Boolean, default=False, nullable=False)
    is_unemployed = Column(Boolean, default=False, nullable=False)
    is_high_income = Column(Boolean, default=False, nullable=False)
    discretionary_spender = Column(String(50), nullable=True) # frugal, moderate, impulsive
    main_transportation = Column(String(50), nullable=True) # car, public_transit, bicycle, walking, motorcycle, other
    children_count = Column(Integer, default=0, nullable=False)
    in_couple = Column(Boolean, default=False, nullable=False)
    has_insurance = Column(Boolean, default=True, nullable=False)

    # Additional Profile Fields
    housing_status = Column(String(50), nullable=True) # owner, renter, free_housing
    age_range = Column(String(20), nullable=True) # 18-25, 26-35, 36-50, 51-65, 65+
    savings_goal = Column(String(50), nullable=True) # real_estate, emergency_fund, travel, retirement, investment
    risk_tolerance = Column(String(20), nullable=True) # low, medium, high

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="EUR", nullable=False)
    transaction_type = Column(String(50), nullable=False) # e.g., deposit, withdrawal, payment, transfer
    status = Column(String(50), default="completed", nullable=False) # e.g., completed, pending, failed
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="transactions")
