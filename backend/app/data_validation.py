"""Validate synthetic imports completely before any database write.

Unknown fields are discarded, including generator scenarios and pre-labelled
financial profiles. Stored data is an explicit allowlist of observed records.
"""
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator, model_validator

Money = Annotated[Decimal, Field(max_digits=16, decimal_places=2, allow_inf_nan=False)]
Identifier = Annotated[str, Field(min_length=1, max_length=150, pattern=r"^\S+$")]


def integer_cents(value: Decimal) -> int:
    return int(value * 100)


class InputModel(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)


class SyntheticTransaction(InputModel):
    transaction_id: Identifier
    date: date
    sens: Literal["credit", "debit"]
    montant: Money = Field(gt=0)
    devise: Literal["EUR"] = "EUR"
    categorie: str = Field(min_length=1, max_length=150)
    contrepartie: str = Field(min_length=1, max_length=500)
    type: str = Field(min_length=1, max_length=100)
    libelle: str | None = Field(default=None, max_length=2000)
    pays_contrepartie: str | None = Field(default=None, max_length=100)
    solde_apres: Money
    statut: Literal["comptabilisee"] | None = None
    debiteur: str | None = Field(default=None, max_length=500)
    crediteur: str | None = Field(default=None, max_length=500)
    transaction_origine_id: Identifier | None = None

    @field_validator("date", mode="before")
    @classmethod
    def iso_date(cls, value):
        if isinstance(value, str):
            return date.fromisoformat(value)
        if type(value) is date:
            return value
        raise ValueError("Transaction dates must be ISO dates.")


class SyntheticAccount(InputModel):
    compte_id: Identifier | None = None
    type: str = Field(default="compte_courant_personnel", min_length=1, max_length=100)
    devise: Literal["EUR"] = "EUR"
    debut_historique: date
    fin_historique: date
    solde_initial: Money
    solde_final: Money
    nombre_transactions: int | None = Field(default=None, ge=0, strict=True)
    total_credits: Money | None = Field(default=None, ge=0)
    total_debits: Money | None = Field(default=None, ge=0)
    transactions: list[SyntheticTransaction]

    @field_validator("debut_historique", "fin_historique", mode="before")
    @classmethod
    def iso_date(cls, value):
        if isinstance(value, str):
            return date.fromisoformat(value)
        if type(value) is date:
            return value
        raise ValueError("History boundaries must be ISO dates.")

    @model_validator(mode="after")
    def reconcile(self):
        if self.fin_historique < self.debut_historique:
            raise ValueError("History must end on or after its start.")
        seen = set()
        balance = integer_cents(self.solde_initial)
        credits = debits = 0
        previous = self.debut_historique
        for transaction in self.transactions:
            if transaction.transaction_id in seen:
                raise ValueError("Transaction identifiers must be unique.")
            if not previous <= transaction.date <= self.fin_historique:
                raise ValueError("Transactions must be chronological and inside the observation period.")
            if transaction.transaction_origine_id and transaction.transaction_origine_id not in seen:
                raise ValueError("A linked transaction must refer to an earlier transaction in the same account.")
            seen.add(transaction.transaction_id)
            previous = transaction.date
            amount = integer_cents(transaction.montant)
            if transaction.sens == "credit":
                credits += amount
                balance += amount
            else:
                debits += amount
                balance -= amount
            if balance != integer_cents(transaction.solde_apres):
                raise ValueError("Transaction running balances do not reconcile.")
        if balance != integer_cents(self.solde_final):
            raise ValueError("The final account balance does not reconcile.")
        if self.nombre_transactions is not None and self.nombre_transactions != len(self.transactions):
            raise ValueError("The declared transaction count does not match the history.")
        if self.total_credits is not None and integer_cents(self.total_credits) != credits:
            raise ValueError("The declared credit total does not match the history.")
        if self.total_debits is not None and integer_cents(self.total_debits) != debits:
            raise ValueError("The declared debit total does not match the history.")
        self.nombre_transactions = len(self.transactions)
        self.total_credits = Decimal(credits) / 100
        self.total_debits = Decimal(debits) / 100
        return self


class Preferences(InputModel):
    personnalisation_commerciale: StrictBool = False


class SyntheticCustomer(InputModel):
    client_id: str = Field(min_length=1, max_length=100, pattern=r"^\S+$")
    synthetique: StrictBool
    prenom: str = Field(default="Synthetic customer", min_length=1, max_length=255)
    age: int | None = Field(default=None, ge=0, le=120, strict=True)
    ville: str = Field(default="Not provided", min_length=1, max_length=150)
    pays: str = Field(default="Not provided", min_length=1, max_length=100)
    preferences: Preferences = Field(default_factory=Preferences)
    compte: SyntheticAccount

    @model_validator(mode="after")
    def synthetic_only(self):
        if self.synthetique is not True:
            raise ValueError("Only data explicitly marked as synthetic is accepted.")
        if self.compte.compte_id is None:
            self.compte.compte_id = f"account-{self.client_id}"
        for transaction in self.compte.transactions:
            party = transaction.debiteur if transaction.sens == "debit" else transaction.crediteur
            if party is not None and party != self.client_id:
                raise ValueError("Transaction account holder does not match the client.")
        return self


class CatalogueProduct(InputModel):
    id: str = Field(min_length=1, max_length=100, pattern=r"^\S+$")
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=10000)


def validate_profiles(profiles) -> list[SyntheticCustomer]:
    if not isinstance(profiles, list) or not profiles:
        raise ValueError("Bank data must contain a non-empty list of synthetic customers.")
    parsed = [SyntheticCustomer.model_validate(profile) for profile in profiles]
    for values, name in (([item.client_id for item in parsed], "client"),
                         ([item.compte.compte_id for item in parsed], "account"),
                         ([tx.transaction_id for item in parsed for tx in item.compte.transactions], "transaction")):
        if len(values) != len(set(values)):
            raise ValueError(f"Duplicate synthetic {name} identifier.")
    return parsed


def validate_products(products) -> list[CatalogueProduct]:
    if not isinstance(products, list) or not products:
        raise ValueError("The catalogue must contain a non-empty product list.")
    parsed = [CatalogueProduct.model_validate({"id": f"product-{index:02d}", **product})
              for index, product in enumerate(products, 1)]
    if len({product.id for product in parsed}) != len(parsed):
        raise ValueError("Duplicate product identifier.")
    return parsed


def customer_payload(customer: SyntheticCustomer) -> dict:
    # Preserve the API's original French source keys and JSON number amounts.
    payload = customer.model_dump(mode="json", exclude_none=True)
    account = payload["compte"]
    for key in ("solde_initial", "solde_final", "total_credits", "total_debits"):
        account[key] = float(account[key])
    for transaction in account["transactions"]:
        for key in ("montant", "solde_apres"):
            transaction[key] = float(transaction[key])
    return payload
