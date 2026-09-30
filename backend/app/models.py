"""Normalized synthetic banking records. Monetary values are integer cents."""
from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, Date, ForeignKey, Index, Integer, String, Text, UniqueConstraint

from app.database import Base


class DatasetMetadata(Base):
    __tablename__ = "bank_dataset_metadata"
    key = Column(String(40), primary_key=True)
    value = Column(Text, nullable=False)


class Customer(Base):
    __tablename__ = "bank_customers"
    id = Column(String(100), primary_key=True)
    ordinal = Column(Integer, nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)
    city = Column(String(150), nullable=False)
    country = Column(String(100), nullable=False)
    personalization_allowed = Column(Boolean, nullable=False)
    __table_args__ = (CheckConstraint("age IS NULL OR (age >= 0 AND age <= 120)", name="ck_customer_age"),)


class Account(Base):
    __tablename__ = "bank_accounts"
    id = Column(String(150), primary_key=True)
    client_id = Column(String(100), ForeignKey("bank_customers.id", ondelete="CASCADE"), nullable=False, unique=True)
    account_type = Column(String(100), nullable=False)
    currency = Column(String(3), nullable=False)
    observation_start = Column(Date, nullable=False)
    observation_end = Column(Date, nullable=False)
    initial_balance_cents = Column(BigInteger, nullable=False)
    balance_cents = Column(BigInteger, nullable=False)
    total_credit_cents = Column(BigInteger, nullable=False)
    total_debit_cents = Column(BigInteger, nullable=False)
    transaction_count = Column(Integer, nullable=False)
    __table_args__ = (
        CheckConstraint("currency = 'EUR'", name="ck_account_currency"),
        CheckConstraint("observation_end >= observation_start", name="ck_account_dates"),
        CheckConstraint("transaction_count >= 0", name="ck_account_count"),
        CheckConstraint("total_credit_cents >= 0 AND total_debit_cents >= 0", name="ck_account_totals"),
        CheckConstraint("balance_cents = initial_balance_cents + total_credit_cents - total_debit_cents", name="ck_account_balance"),
    )


class Transaction(Base):
    __tablename__ = "bank_transactions"
    id = Column(String(150), primary_key=True)
    account_id = Column(String(150), ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False)
    ordinal = Column(Integer, nullable=False)
    booked_date = Column(Date, nullable=False)
    direction = Column(String(6), nullable=False)
    amount_cents = Column(BigInteger, nullable=False)
    currency = Column(String(3), nullable=False)
    category = Column(String(150), nullable=False)
    merchant = Column(String(500), nullable=False)
    transaction_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    merchant_country = Column(String(100), nullable=True)
    balance_after_cents = Column(BigInteger, nullable=False)
    status = Column(String(50), nullable=True)
    debtor = Column(String(500), nullable=True)
    creditor = Column(String(500), nullable=True)
    original_transaction_id = Column(String(150), ForeignKey("bank_transactions.id"), nullable=True)
    __table_args__ = (
        CheckConstraint("direction IN ('credit', 'debit')", name="ck_transaction_direction"),
        CheckConstraint("amount_cents > 0", name="ck_transaction_amount"),
        CheckConstraint("currency = 'EUR'", name="ck_transaction_currency"),
        UniqueConstraint("account_id", "ordinal", name="uq_transaction_account_order"),
        Index("ix_transaction_account_date", "account_id", "booked_date", "ordinal"),
    )


class Product(Base):
    __tablename__ = "bank_products"
    id = Column(String(100), primary_key=True)
    ordinal = Column(Integer, nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
