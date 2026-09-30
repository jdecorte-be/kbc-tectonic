"""Synthetic banking data and reproducible, integer-cent transaction facts."""

from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
INCOME_CATEGORIES = {"salaire", "pension", "revenu_activite", "job_etudiant", "aide_familiale"}
TRANSFER_CATEGORIES = {"transfert_epargne", "investissement", "virement_entre_proches"}


def cents(value: Any) -> int:
    return int((Decimal(str(value)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def sparse_client() -> dict:
    return {
        "client_id": "SYN-SPARSE", "synthetique": True, "prenom": "Alex (limited history)",
        "age": 29, "ville": "Bruxelles", "pays": "Belgique",
        "preferences": {"personnalisation_commerciale": True},
        "compte": {"debut_historique": "2026-09-29", "fin_historique": "2026-09-30",
                   "solde_initial": 250, "solde_final": 246.50, "transactions": [
                       {"transaction_id": "TX-SYN-SPARSE-001", "date": "2026-09-30",
                        "sens": "debit", "montant": 3.50, "devise": "EUR", "categorie": "cafe_boulangerie",
                        "contrepartie": "Fictional cafe", "type": "paiement_carte", "libelle": "Fictional cafe",
                        "pays_contrepartie": "Belgique", "solde_apres": 246.50}
                   ]},
    }


class BankData:
    def __init__(self, data_path: str = "", products_path: str = "", generated_count: int = 1000):
        if data_path:
            profiles = json.loads(Path(data_path).expanduser().read_text(encoding="utf-8"))
            if not isinstance(profiles, list) or not profiles:
                raise ValueError("BANK_DATA_PATH must contain a list of synthetic customers.")
        else:
            # Load the supplied generator without running its CLI or writing generated files.
            spec = importlib.util.spec_from_file_location("bank_profile_generator", ROOT / "generate_bank_profiles.py")
            if spec is None or spec.loader is None:
                raise ValueError("The synthetic profile generator could not be found.")
            generator = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(generator)
            profiles = [generator.profile(i) for i in range(1, generated_count + 1)]
        self.clients: dict[str, dict] = {}
        for profile in profiles:
            if profile.get("synthetique") is not True:
                raise ValueError("Only data explicitly marked as synthetic is accepted.")
            identifier = profile["client_id"]
            if identifier in self.clients:
                raise ValueError("Duplicate synthetic customer identifier.")
            # The simulator's hidden label must never enter inference, even accidentally.
            clean = {key: value for key, value in profile.items() if key != "scenario_simulation"}
            self.clients[identifier] = clean
        if "SYN-SPARSE" not in self.clients:
            self.clients["SYN-SPARSE"] = sparse_client()
        catalogue = json.loads(Path(products_path or ROOT / "products.json").read_text(encoding="utf-8"))
        self.products = [
            {"id": product.get("id", f"product-{index:02d}"), "name": product["name"], "description": product["description"]}
            for index, product in enumerate(catalogue, 1)
        ]
        self.summaries = [client_summary(client) for client in self.clients.values()]
        self._facts: dict[str, dict] = {}

    def get(self, client_id: str) -> dict:
        return self.clients[client_id]

    def facts(self, client_id: str) -> dict:
        if client_id not in self._facts:
            self._facts[client_id] = extract_facts(self.get(client_id))
        return self._facts[client_id]

    def list_clients(self, query: str = "", limit: int = 50, offset: int = 0) -> dict:
        query = query.casefold().strip()
        matching = [item for item in self.summaries if not query or query in " ".join(
            str(item[key]) for key in ("id", "name", "city", "country")
        ).casefold()]
        return {"items": matching[offset:offset + limit], "total": len(matching)}

    def benchmark_clients(self, count: int) -> list[str]:
        ids = list(self.clients)
        if count > len(ids):
            raise ValueError(f"The dataset contains only {len(ids)} customers.")
        if count == 1:
            return ids[:1]
        # Span the entire deterministic population, including the sparse example.
        return [ids[index * (len(ids) - 1) // (count - 1)] for index in range(count)]


def client_summary(client: dict) -> dict:
    account = client["compte"]
    countries = {"Belgique": "Belgium", "Pays-Bas": "Netherlands", "Allemagne": "Germany"}
    cities = {"Bruxelles": "Brussels", "Anvers": "Antwerp", "Gand": "Ghent", "Bruges": "Bruges", "Louvain": "Leuven", "Liège": "Liège"}
    return {
        "id": client["client_id"], "name": client.get("prenom", "Synthetic customer"),
        "age": client.get("age"), "city": cities.get(client.get("ville"), client.get("ville", "Not provided")),
        "country": countries.get(client.get("pays"), client.get("pays", "Not provided")), "balance": cents(account.get("solde_final", 0)) / 100,
        "transaction_count": len(account.get("transactions", [])),
        "personalization_allowed": client.get("preferences", {}).get("personnalisation_commerciale") is True,
    }


def extract_facts(client: dict) -> dict:
    account = client["compte"]
    transactions = sorted(account.get("transactions", []), key=lambda item: (item["date"], item["transaction_id"]))
    start = account.get("debut_historique") or (transactions[0]["date"] if transactions else "2026-09-30")
    end = account.get("fin_historique") or (transactions[-1]["date"] if transactions else start)
    observation_days = max(0, (date.fromisoformat(end) - date.fromisoformat(start)).days + 1)
    categories: dict[str, dict] = {}
    monthly: dict[str, dict] = {}
    month_cursor = date.fromisoformat(start).replace(day=1)
    end_date = date.fromisoformat(end)
    while month_cursor <= end_date:
        month = month_cursor.strftime("%Y-%m")
        monthly[month] = {"month": month, "income_cents": 0, "credit_cents": 0, "debit_cents": 0,
                          "net_cents": 0, "savings_cents": 0, "investment_cents": 0}
        month_cursor = date(month_cursor.year + (month_cursor.month == 12), month_cursor.month % 12 + 1, 1)
    grouped: dict[tuple[str, str], list] = defaultdict(list)
    consumption = 0
    balance_points = []
    cash_count = 0
    weekend_count = 0
    foreign = []
    category_months: dict[str, dict] = defaultdict(lambda: defaultdict(int))
    for tx in transactions:
        category = tx.get("categorie", "inconnue")
        amount = cents(tx["montant"])
        direction = tx["sens"]
        if direction not in {"credit", "debit"}:
            raise ValueError("Invalid transaction direction.")
        row = categories.setdefault(category, {"category": category, "count": 0, "credit_cents": 0, "debit_cents": 0, "evidence": []})
        row["count"] += 1
        row[f"{direction}_cents"] += amount
        if len(row["evidence"]) < 5:
            row["evidence"].append(tx["transaction_id"])
        month = tx["date"][:7]
        row_month = monthly.setdefault(month, {"month": month, "income_cents": 0, "credit_cents": 0, "debit_cents": 0, "net_cents": 0, "savings_cents": 0, "investment_cents": 0})
        row_month[f"{direction}_cents"] += amount
        row_month["net_cents"] += amount if direction == "credit" else -amount
        if direction == "credit" and category in INCOME_CATEGORIES:
            row_month["income_cents"] += amount
        if direction == "debit":
            grouped[(tx.get("contrepartie", "Unknown"), category)].append(tx)
            category_months[category][month] += amount
            consumption += amount if category not in TRANSFER_CATEGORIES else 0
            row_month["savings_cents"] += amount if category == "transfert_epargne" else 0
            row_month["investment_cents"] += amount if category == "investissement" else 0
            cash_count += category == "retrait_especes"
            weekend_count += date.fromisoformat(tx["date"]).weekday() >= 5
            if tx.get("pays_contrepartie") and tx["pays_contrepartie"] != client.get("pays"):
                foreign.append(tx["transaction_id"])
        if "solde_apres" in tx:
            balance_points.append(cents(tx["solde_apres"]))
    recurring = []
    for (merchant, category), rows in grouped.items():
        months = sorted({row["date"][:7] for row in rows})
        if len(months) < 2 or not any(row.get("type") in {"domiciliation", "ordre_permanent"} for row in rows):
            continue
        amounts = [cents(row["montant"]) for row in rows]
        recurring.append({"merchant": merchant, "category": category, "count": len(rows), "months": months,
                          "amount_cents": round(sum(amounts) / len(amounts)),
                          "evidence": [row["transaction_id"] for row in rows[:5]]})
    ordered_months = sorted(monthly)
    drift = []
    if len(ordered_months) >= 3:
        for category, values in category_months.items():
            baseline = sum(values.get(month, 0) for month in ordered_months[:-1]) / (len(ordered_months) - 1)
            latest = values.get(ordered_months[-1], 0)
            if baseline >= 5000 and latest >= baseline * 1.8:
                drift.append({"category": category, "baseline_monthly_cents": round(baseline), "latest_month_cents": latest,
                              "change_percent": round((latest / baseline - 1) * 100), "latest_month": ordered_months[-1]})
    missing = [
        "No order history or basket contents: transactions do not describe the items purchased.",
        "Total wealth, other accounts, stated goals, and risk tolerance are unknown.",
        "No future purchase or travel intention has been confirmed.",
    ]
    if len(transactions) < 8 or observation_days < 30:
        missing.insert(0, "The history is too short or contains too few transactions to establish reliable habits.")
    return {
        "currency": "EUR", "observation_start": start, "observation_end": end, "observation_days": observation_days,
        "transaction_count": len(transactions), "balance_cents": cents(account.get("solde_final", 0)),
        "total_credit_cents": sum(row["credit_cents"] for row in categories.values()),
        "total_debit_cents": sum(row["debit_cents"] for row in categories.values()), "consumption_debit_cents": consumption,
        "monthly_cashflow": [monthly[month] for month in ordered_months],
        "categories": sorted(categories.values(), key=lambda row: row["debit_cents"] + row["credit_cents"], reverse=True),
        "existing_insurance": sorted(category for category in categories if category.startswith("assurance_") and categories[category]["debit_cents"] > 0),
        "savings_transfer_count": categories.get("transfert_epargne", {}).get("count", 0),
        "investment_transfer_count": categories.get("investissement", {}).get("count", 0),
        "recurring_payments": recurring,
        "habits": {"cash_withdrawal_count": cash_count, "weekend_debit_count": weekend_count,
                   "foreign_transaction_count": len(foreign), "foreign_evidence": foreign[:5], "category_increases": drift,
                   "negative_balance_observation_count": sum(value < 0 for value in balance_points),
                   "minimum_observed_balance_cents": min(balance_points) if balance_points else None},
        "missing_information": missing,
        "limitations": ["The current account balance does not establish total wealth or an available spending budget.",
                        "An absent insurance payment does not prove that the customer has no coverage.",
                        "Travel transactions describe the past and do not confirm an upcoming trip."],
    }
