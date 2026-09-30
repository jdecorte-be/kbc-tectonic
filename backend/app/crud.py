"""SQL-backed access to validated, immutable synthetic banking datasets."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sqlalchemy import String, case, cast, func, insert, or_, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import Base, create_database_engine
from app.data_validation import customer_payload, integer_cents, validate_products, validate_profiles
from app.models import Account, Customer, DatasetMetadata, Product, Transaction

COUNTRIES = {"Belgique": "Belgium", "Pays-Bas": "Netherlands", "Allemagne": "Germany"}
CITIES = {"Bruxelles": "Brussels", "Anvers": "Antwerp", "Gand": "Ghent", "Bruges": "Bruges", "Louvain": "Leuven", "Liège": "Liège"}


class BankRepository:
    def __init__(self, database_url: str | None = None):
        default_path = Path(__file__).resolve().parents[2] / "data" / "bank.sqlite3"
        self.engine = create_database_engine(database_url or f"sqlite:///{default_path}")
        Base.metadata.create_all(self.engine)

    def close(self) -> None:
        self.engine.dispose()

    def check_health(self) -> bool:
        try:
            with self.engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            return False

    def counts(self) -> dict[str, int]:
        with Session(self.engine) as session:
            return {name: session.scalar(select(func.count()).select_from(model)) or 0
                    for name, model in (("clients", Customer), ("accounts", Account), ("transactions", Transaction), ("products", Product))}

    def is_seeded(self) -> bool:
        with Session(self.engine) as session:
            return session.get(DatasetMetadata, "fingerprint") is not None

    def seed(self, profiles: list[dict], products: list[dict]) -> bool:
        """Atomically initialize once; identical imports are a no-op.

        A different import needs a new database, so existing analysis evidence is
        never silently rebound to different records with the same customer IDs.
        """
        customers = validate_profiles(profiles)
        catalogue = validate_products(products)
        canonical = {"clients": [customer_payload(customer) for customer in customers],
                     "products": [product.model_dump() for product in catalogue]}
        fingerprint = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        mismatch = "This database contains a different synthetic dataset. Use a separate DATABASE_URL to import it."
        with Session(self.engine) as session:
            try:
                with session.begin():
                    existing = session.get(DatasetMetadata, "fingerprint")
                    if existing:
                        if existing.value != fingerprint:
                            raise ValueError(mismatch)
                        return False
                    # SQL INSERT batches avoid retaining hundreds of thousands of ORM objects.
                    session.execute(insert(Customer), [
                        {"id": item.client_id, "ordinal": ordinal, "name": item.prenom, "age": item.age,
                         "city": item.ville, "country": item.pays,
                         "personalization_allowed": item.preferences.personnalisation_commerciale}
                        for ordinal, item in enumerate(customers)
                    ])
                    session.execute(insert(Account), [
                        {"id": item.compte.compte_id, "client_id": item.client_id, "account_type": item.compte.type,
                         "currency": item.compte.devise, "observation_start": item.compte.debut_historique,
                         "observation_end": item.compte.fin_historique,
                         "initial_balance_cents": integer_cents(item.compte.solde_initial),
                         "balance_cents": integer_cents(item.compte.solde_final),
                         "total_credit_cents": integer_cents(item.compte.total_credits),
                         "total_debit_cents": integer_cents(item.compte.total_debits),
                         "transaction_count": len(item.compte.transactions)} for item in customers
                    ])
                    batch = []
                    for item in customers:
                        for ordinal, transaction in enumerate(item.compte.transactions):
                            batch.append({"id": transaction.transaction_id, "account_id": item.compte.compte_id,
                                          "ordinal": ordinal, "booked_date": transaction.date,
                                          "direction": transaction.sens, "amount_cents": integer_cents(transaction.montant),
                                          "currency": transaction.devise, "category": transaction.categorie,
                                          "merchant": transaction.contrepartie, "transaction_type": transaction.type,
                                          "description": transaction.libelle, "merchant_country": transaction.pays_contrepartie,
                                          "balance_after_cents": integer_cents(transaction.solde_apres),
                                          "status": transaction.statut, "debtor": transaction.debiteur,
                                          "creditor": transaction.crediteur,
                                          "original_transaction_id": transaction.transaction_origine_id})
                            if len(batch) == 5000:
                                session.execute(Transaction.__table__.insert(), batch)
                                batch = []
                    if batch:
                        session.execute(Transaction.__table__.insert(), batch)
                    session.execute(insert(Product), [{**product.model_dump(), "ordinal": ordinal}
                                                       for ordinal, product in enumerate(catalogue)])
                    session.add_all([DatasetMetadata(key="fingerprint", value=fingerprint),
                                     DatasetMetadata(key="schema_version", value="1")])
                return True
            except IntegrityError:
                # A concurrent startup can win the seed transaction. Reuse only identical data.
                session.rollback()
                existing = session.get(DatasetMetadata, "fingerprint")
                if existing and existing.value == fingerprint:
                    return False
                if existing:
                    raise ValueError(mismatch) from None
                raise

    def client_ids(self) -> list[str]:
        with Session(self.engine) as session:
            return list(session.scalars(select(Customer.id).order_by(Customer.ordinal)))

    def has_client(self, client_id: str) -> bool:
        with Session(self.engine) as session:
            return session.scalar(select(Customer.id).where(Customer.id == client_id)) is not None

    def get_products(self) -> list[dict]:
        with Session(self.engine) as session:
            return [{"id": item.id, "name": item.name, "description": item.description}
                    for item in session.scalars(select(Product).order_by(Product.ordinal))]

    def list_clients(self, query: str = "", limit: int = 50, offset: int = 0, opt_in_only: bool = False) -> dict:
        self._pagination(limit, offset)
        clauses = self._client_filters(query, opt_in_only)
        with Session(self.engine) as session:
            total = session.scalar(select(func.count()).select_from(Customer).where(*clauses)) or 0
            rows = session.execute(select(Customer, Account).join(Account, Account.client_id == Customer.id)
                                   .where(*clauses).order_by(Customer.ordinal).offset(offset).limit(limit))
            return {"items": [self._summary(client, account) for client, account in rows], "total": total}

    @staticmethod
    def _client_filters(query: str = "", opt_in_only: bool = False, client_id: str | None = None) -> list:
        clauses = []
        query = query.casefold().strip()
        if query:
            clauses.append(or_(*(func.lower(column).contains(query, autoescape=True) for column in (
                Customer.id, Customer.name, case(CITIES, value=Customer.city, else_=Customer.city),
                case(COUNTRIES, value=Customer.country, else_=Customer.country)))))
        if opt_in_only:
            clauses.append(Customer.personalization_allowed.is_(True))
        if client_id is not None:
            clauses.append(Customer.id == client_id)
        return clauses

    def dashboard_observations(self, query: str = "", opt_in_only: bool = False,
                               client_id: str | None = None) -> list[dict]:
        """Read the cohort and grouped facts in four queries, never full histories.

        All monetary sums stay in integer cents. The month expression works on
        SQLite and PostgreSQL; no per-customer ORM transaction loads are needed.
        """
        clauses = self._client_filters(query, opt_in_only, client_id)
        month = func.substr(cast(Transaction.booked_date, String), 1, 7)
        joined = lambda statement: statement.select_from(Transaction).join(
            Account, Account.id == Transaction.account_id).join(Customer, Customer.id == Account.client_id).where(*clauses)
        with Session(self.engine) as session:
            rows = session.execute(select(Customer, Account).join(Account, Account.client_id == Customer.id)
                                   .where(*clauses).order_by(Customer.ordinal))
            observations = {client.id: {"client": self._summary(client, account),
                                       "balance_cents": account.balance_cents,
                                       "observation_start": account.observation_start,
                                       "observation_end": account.observation_end,
                                       "categories": [], "monthly": [], "recurring_payment_count": 0}
                            for client, account in rows}
            if not observations:
                return []
            category_query = joined(select(
                Account.client_id, Transaction.category, Transaction.direction,
                func.count(), func.sum(Transaction.amount_cents), func.min(Transaction.id),
            )).group_by(Account.client_id, Transaction.category, Transaction.direction)
            for identifier, category, direction, count, amount, evidence in session.execute(category_query):
                observations[identifier]["categories"].append({"category": category, "direction": direction,
                                                              "count": count, "amount_cents": int(amount), "evidence": evidence})
            monthly_query = joined(select(
                Account.client_id, month.label("month"),
                func.sum(case((Transaction.direction == "credit", Transaction.amount_cents), else_=0)),
                func.sum(case((Transaction.direction == "debit", Transaction.amount_cents), else_=0)),
            )).group_by(Account.client_id, month).order_by(month)
            for identifier, value, credit, debit in session.execute(monthly_query):
                observations[identifier]["monthly"].append({"month": value, "credit_cents": int(credit), "debit_cents": int(debit)})
            recurring_query = joined(select(Account.client_id, Transaction.merchant, Transaction.category)).where(
                Transaction.direction == "debit",
            ).group_by(Account.client_id, Transaction.merchant, Transaction.category).having(
                func.count(func.distinct(month)) >= 2,
                func.max(case((Transaction.transaction_type.in_(["domiciliation", "ordre_permanent"]), 1), else_=0)) == 1,
            )
            for identifier, _merchant, _category in session.execute(recurring_query):
                observations[identifier]["recurring_payment_count"] += 1
            return list(observations.values())

    def get_client(self, client_id: str) -> dict:
        with Session(self.engine) as session:
            row = session.execute(select(Customer, Account).join(Account, Account.client_id == Customer.id)
                                  .where(Customer.id == client_id)).first()
            if row is None:
                raise KeyError(client_id)
            client, account = row
            transactions = list(session.scalars(select(Transaction).where(Transaction.account_id == account.id)
                                               .order_by(Transaction.ordinal)))
            return {"client_id": client.id, "synthetique": True, "prenom": client.name, "age": client.age,
                    "ville": client.city, "pays": client.country,
                    "preferences": {"personnalisation_commerciale": client.personalization_allowed},
                    "compte": {"compte_id": account.id, "type": account.account_type, "devise": account.currency,
                               "debut_historique": account.observation_start.isoformat(), "fin_historique": account.observation_end.isoformat(),
                               "solde_initial": account.initial_balance_cents / 100, "solde_final": account.balance_cents / 100,
                               "nombre_transactions": account.transaction_count, "total_credits": account.total_credit_cents / 100,
                               "total_debits": account.total_debit_cents / 100,
                               "transactions": [self._transaction(transaction) for transaction in transactions]}}

    def list_transactions(self, client_id: str, limit: int = 50, offset: int = 0) -> dict:
        self._pagination(limit, offset)
        with Session(self.engine) as session:
            account = session.scalar(select(Account).where(Account.client_id == client_id))
            if account is None:
                raise KeyError(client_id)
            rows = session.scalars(select(Transaction).where(Transaction.account_id == account.id)
                                   .order_by(Transaction.ordinal).offset(offset).limit(limit))
            return {"items": [self._transaction(transaction) for transaction in rows], "total": account.transaction_count}

    @staticmethod
    def _pagination(limit: int, offset: int) -> None:
        if type(limit) is not int or not 1 <= limit <= 1000 or type(offset) is not int or offset < 0:
            raise ValueError("Pagination requires a limit from 1 to 1000 and a nonnegative offset.")

    @staticmethod
    def _summary(client: Customer, account: Account) -> dict:
        return {"id": client.id, "name": client.name, "age": client.age,
                "city": CITIES.get(client.city, client.city), "country": COUNTRIES.get(client.country, client.country),
                "balance": account.balance_cents / 100, "transaction_count": account.transaction_count,
                "personalization_allowed": client.personalization_allowed}

    @staticmethod
    def _transaction(transaction: Transaction) -> dict:
        result = {"transaction_id": transaction.id, "date": transaction.booked_date.isoformat(),
                  "sens": transaction.direction, "montant": transaction.amount_cents / 100,
                  "devise": transaction.currency, "categorie": transaction.category,
                  "contrepartie": transaction.merchant, "type": transaction.transaction_type,
                  "solde_apres": transaction.balance_after_cents / 100}
        for key, value in (("libelle", transaction.description), ("pays_contrepartie", transaction.merchant_country),
                           ("statut", transaction.status), ("debiteur", transaction.debtor),
                           ("crediteur", transaction.creditor), ("transaction_origine_id", transaction.original_transaction_id)):
            if value is not None:
                result[key] = value
        return result
