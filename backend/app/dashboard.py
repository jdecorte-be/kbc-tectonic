"""Observed customer context and saved recommendations, with no provider calls."""
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone

from app.banking import INCOME_CATEGORIES
from app.crud import BankRepository
from app.run_store import RunStore


SEGMENTS = [
    ("young_investor", "Young investor", "Age 18–30 with repeated salary credits and investment transfers; goals, holdings and risk tolerance are unknown."),
    ("investor", "Investor", "Repeated investment transfers are observed; holdings and investment suitability are unknown."),
    ("saver", "Saver", "Repeated savings transfers are observed; total savings and wealth are unknown."),
    ("student", "Student activity", "Repeated credits are explicitly categorized as student work; enrollment is not confirmed."),
    ("worker", "Salary income", "Repeated salary credits are observed; occupation and future income are unknown."),
    ("retired", "Pension income", "Repeated pension credits are observed; retirement status is not independently confirmed."),
    ("variable_income", "Business income", "Repeated business income credits are observed; exact employment status is unknown."),
    ("past_travel", "Past travel", "Past travel payments are observed; they do not imply an upcoming trip."),
    ("housing_payments", "Housing payments", "Repeated rent or mortgage payments are observed; future purchase plans are unknown."),
    ("public_transport", "Public transport", "Repeated public transport expenses are observed."),
]
SEGMENT_STATES = [
    ("no_evidence", "Not enough evidence", "No repeated transaction pattern meets the observed-segment rules."),
    ("opt_out", "Personalization off", "Personalization consent is off. No inferred segment or advertisement is shown."),
]
OUTCOMES = [
    ("not_analyzed", "Not analyzed"), ("recommended", "Ads selected"),
    ("insufficient_information", "Insufficient information"), ("no_match", "No product match"),
    ("opt_out", "Personalization off"), ("error", "Analysis error"),
]
CATEGORY_LABELS = {
    "salaire": "salary credits", "pension": "pension credits", "job_etudiant": "student-work credits",
    "revenu_activite": "business-income credits", "transfert_epargne": "savings transfers",
    "investissement": "investment transfers", "voyage_transport": "past travel payments",
    "hebergement_voyage": "travel accommodation payments", "loyer": "rent payments",
    "credit_logement": "mortgage payments", "transport_public": "public transport payments",
}


def _month_count(observation: dict) -> int:
    start, end = observation["observation_start"], observation["observation_end"]
    return (end.year - start.year) * 12 + end.month - start.month + 1


def _segments(observation: dict) -> list[dict]:
    client = observation["client"]
    if not client["personalization_allowed"]:
        return []
    rows = {(row["category"], row["direction"]): row for row in observation["categories"]}

    def count(names: list[str], direction: str = "debit") -> int:
        return sum(rows.get((name, direction), {}).get("count", 0) for name in names)

    income = count(["salaire"], "credit")
    investing = count(["investissement"])
    rules = {
        "young_investor": (client["age"] is not None and 18 <= client["age"] <= 30 and income >= 2 and investing >= 2,
                           [("salaire", "credit"), ("investissement", "debit")]),
        "investor": (investing >= 2, [("investissement", "debit")]),
        "saver": (count(["transfert_epargne"]) >= 2, [("transfert_epargne", "debit")]),
        "student": (count(["job_etudiant"], "credit") >= 2, [("job_etudiant", "credit")]),
        "worker": (income >= 2, [("salaire", "credit")]),
        "retired": (count(["pension"], "credit") >= 2, [("pension", "credit")]),
        "variable_income": (count(["revenu_activite"], "credit") >= 3, [("revenu_activite", "credit")]),
        "past_travel": (count(["voyage_transport", "hebergement_voyage"]) >= 1,
                        [("voyage_transport", "debit"), ("hebergement_voyage", "debit")]),
        "housing_payments": (count(["loyer", "credit_logement"]) >= 2,
                             [("loyer", "debit"), ("credit_logement", "debit")]),
        "public_transport": (count(["transport_public"]) >= 3, [("transport_public", "debit")]),
    }
    result = []
    for identifier, label, description in SEGMENTS:
        supported, categories = rules[identifier]
        if not supported:
            continue
        evidence = []
        if identifier == "young_investor":
            evidence.append(f"Recorded age: {client['age']}; age alone is not sufficient for this tag.")
        for key in categories:
            row = rows.get(key)
            if row:
                evidence.append(f"{row['count']} {CATEGORY_LABELS[key[0]]}, {row['amount_cents'] / 100:.2f} EUR in the observed period; example transaction {row['evidence']}.")
        result.append({"id": identifier, "label": label, "description": description, "evidence": evidence})
    return result


def _segment_ids(item: dict) -> set[str]:
    if not item["client"]["personalization_allowed"]:
        return {"opt_out"}
    return {segment["id"] for segment in item["segments"]} or {"no_evidence"}


class DashboardService:
    def __init__(self, repository: BankRepository, store: RunStore):
        self.repository = repository
        self.store = store

    def _client(self, observation: dict, saved: dict | None, products: dict[str, dict]) -> dict:
        client = observation["client"]
        allowed = client["personalization_allowed"]
        tags = _segments(observation)
        income = sum(row["amount_cents"] for row in observation["categories"]
                     if row["direction"] == "credit" and row["category"] in INCOME_CATEGORIES)
        savings = sum(row["amount_cents"] for row in observation["categories"]
                      if row["direction"] == "debit" and row["category"] == "transfert_epargne")
        investments = sum(row["amount_cents"] for row in observation["categories"]
                          if row["direction"] == "debit" and row["category"] == "investissement")
        days = (observation["observation_end"] - observation["observation_start"]).days + 1
        context_summary = f"{client['transaction_count']} transactions across {days} observed days. "
        if not allowed:
            context_summary += "Personalization is off; no profile is inferred and no advertisement is selected."
        elif tags:
            context_summary += "Observed patterns: " + ", ".join(tag["label"].lower() for tag in tags[:4]) + ". Goals and financial suitability are unknown."
        else:
            context_summary += "There is not enough repeated evidence to assign an observed segment."
        analysis = {"status": "not_analyzed", "category": None,
                    "summary": "No saved analysis. Run an analysis to select relevant advertisements.",
                    "created_at": None, "source": None, "id": None, "ads": []}
        if saved:
            result = saved["result"]
            category = result.get("category")
            if not isinstance(category, dict) or not category.get("id") or not category.get("label"):
                category = None
            else:
                category = {"id": category["id"], "label": category["label"]}
            status = result.get("status", "error")
            if status not in {identifier for identifier, _label in OUTCOMES}:
                status = "error"
            ads = []
            seen = set()
            if allowed and status == "recommended":
                for advert in result.get("ads", []):
                    product_id = advert.get("product_id")
                    if product_id in seen or product_id not in products:
                        continue
                    seen.add(product_id)
                    ads.append({"product_id": product_id, "product_name": products[product_id]["name"],
                                "title": advert.get("title", products[product_id]["name"]),
                                "reason": advert.get("reason", ""), "confidence": advert.get("confidence", 0)})
            analysis = {"status": status, "category": category, "summary": result.get("summary", ""),
                        "created_at": saved["created_at"], "source": saved["source"], "id": saved["id"], "ads": ads}
        if not allowed:
            analysis.update(status="opt_out", category=None, ads=[],
                            summary="Personalization is off. No inferred profile or advertisement is shown.")
        return {"client": client, "segments": tags,
                "context": {"observation_days": days, "monthly_income_cents": round(income / _month_count(observation)),
                            "savings_cents": savings, "investment_cents": investments,
                            "recurring_payment_count": observation["recurring_payment_count"], "summary": context_summary},
                "analysis": analysis}

    def client_context(self, client_id: str) -> dict:
        rows = self.repository.dashboard_observations(client_id=client_id)
        if not rows:
            raise KeyError(client_id)
        products = {product["id"]: product for product in self.repository.get_products()}
        latest = self.store.latest_client_results(client_id)
        return self._client(rows[0], latest.get(client_id), products)

    def snapshot(self, query: str = "", opt_in_only: bool = False, segment: str = "", outcome: str = "",
                 product: str = "", limit: int = 25, offset: int = 0) -> dict:
        self.repository._pagination(limit, offset)
        observations = self.repository.dashboard_observations(query, opt_in_only)
        products = {item["id"]: item for item in self.repository.get_products()}
        latest = self.store.latest_client_results()
        base = [self._client(row, latest.get(row["client"]["id"]), products) for row in observations]
        segment_counts = Counter(identifier for item in base for identifier in _segment_ids(item))
        selected = [item for item in base
                    if (not segment or segment in _segment_ids(item))
                    and (not outcome or item["analysis"]["status"] == outcome)
                    and (not product or any(ad["product_id"] == product for ad in item["analysis"]["ads"]))]
        selected_ids = {item["client"]["id"] for item in selected}
        outcome_counts = Counter(item["analysis"]["status"] for item in selected)
        product_counts = Counter(ad["product_id"] for item in selected for ad in item["analysis"]["ads"])
        cashflow = defaultdict(lambda: {"credit_cents": 0, "debit_cents": 0})
        balance = 0
        for row in observations:
            if row["client"]["id"] not in selected_ids:
                continue
            balance += row["balance_cents"]
            start = row["observation_start"]
            for shift in range(_month_count(row)):
                year = start.year + (start.month - 1 + shift) // 12
                month_number = (start.month - 1 + shift) % 12 + 1
                cashflow[f"{year:04d}-{month_number:02d}"]
            for month in row["monthly"]:
                cashflow[month["month"]]["credit_cents"] += month["credit_cents"]
                cashflow[month["month"]]["debit_cents"] += month["debit_cents"]
        opted_in = sum(item["client"]["personalization_allowed"] for item in selected)
        return {
            "summary": {"total_clients": len(selected), "opt_in_count": opted_in, "opt_out_count": len(selected) - opted_in,
                        "analyzed_count": sum(item["analysis"]["source"] is not None for item in selected),
                        "recommended_count": outcome_counts["recommended"], "not_analyzed_count": outcome_counts["not_analyzed"],
                        "abstained_count": outcome_counts["insufficient_information"] + outcome_counts["no_match"],
                        "error_count": outcome_counts["error"], "selected_ad_count": sum(product_counts.values()),
                        "total_balance_cents": balance, "total_transactions": sum(item["client"]["transaction_count"] for item in selected)},
            "segments": [{"id": identifier, "label": label, "description": description, "count": segment_counts[identifier]}
                         for identifier, label, description in SEGMENTS + SEGMENT_STATES],
            "outcomes": [{"id": identifier, "label": label, "count": outcome_counts[identifier]} for identifier, label in OUTCOMES],
            "products": [{"id": identifier, "name": item["name"], "count": product_counts[identifier]} for identifier, item in products.items()],
            "cashflow": [{"month": month, **values} for month, values in sorted(cashflow.items())],
            "clients": {"items": selected[offset:offset + limit], "total": len(selected)},
            "network": self._network(selected), "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def _network(clients: list[dict]) -> dict:
        # Prioritize actual saved recommendations to make available edges visible.
        # A deterministic, bounded sample is clearly reported in the API and UI.
        buckets = defaultdict(deque)
        for item in sorted(clients, key=lambda value: (not bool(value["analysis"]["ads"]), value["client"]["id"])):
            primary = item["segments"][0]["id"] if item["segments"] else next(iter(_segment_ids(item)))
            buckets[(bool(item["analysis"]["ads"]), primary, item["analysis"]["status"])].append(item)
        sampled = []
        while len(sampled) < min(36, len(clients)):
            for bucket in buckets.values():
                if bucket:
                    sampled.append(bucket.popleft())
                if len(sampled) == 36:
                    break
        nodes, links = {}, []
        definitions = {identifier: label for identifier, label, _description in SEGMENTS + SEGMENT_STATES}
        for item in sampled:
            client_id = item["client"]["id"]
            node_id = f"client:{client_id}"
            nodes[node_id] = {"id": node_id, "label": item["client"]["name"], "kind": "client", "client_id": client_id}
            for identifier in sorted(_segment_ids(item)):
                segment_id = f"segment:{identifier}"
                node = nodes.setdefault(segment_id, {"id": segment_id, "label": definitions[identifier], "kind": "segment", "count": 0})
                node["count"] += 1
                links.append({"source": segment_id, "target": node_id, "kind": "segment"})
            for advert in item["analysis"]["ads"]:
                product_id = f"product:{advert['product_id']}"
                node = nodes.setdefault(product_id, {"id": product_id, "label": advert["product_name"], "kind": "product", "count": 0})
                node["count"] += 1
                links.append({"source": node_id, "target": product_id, "kind": "recommendation"})
        return {"nodes": list(nodes.values()), "links": links, "shown_clients": len(sampled), "total_clients": len(clients)}
