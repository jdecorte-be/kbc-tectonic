"""Explainable two-stage Jev decisions, with explicit abstention and factual ads."""

import asyncio
import json
import math
import time
from typing import Any

from app.banking import BankData, cents, client_summary
from app.jev import JevClient, JevError


PROFILE_THRESHOLD = 0.65
PRODUCT_THRESHOLD = 0.72
CATEGORY_LABELS = {
    "salaire": "Salary", "pension": "Pension income", "job_etudiant": "Student job income",
    "revenu_activite": "Earned business income", "transfert_epargne": "Savings transfers",
    "investissement": "Investment transfers", "carburant": "Fuel", "transport_public": "Public transport",
    "voyage_transport": "Past travel bookings", "hebergement_voyage": "Travel accommodation",
    "loyer": "Rent", "credit_logement": "Mortgage payments",
}


def _signal(identifier: str, label: str, description: str, category_rows: list[dict]) -> dict:
    evidence = []
    for row in category_rows:
        amount = row["debit_cents"] or row["credit_cents"]
        label = CATEGORY_LABELS.get(row["category"], row["category"].replace("_", " "))
        evidence.append(f"{label}: {row['count']} transaction(s), {amount / 100:.2f} EUR; " + ", ".join(row["evidence"][:3]))
    return {"id": identifier, "label": label, "description": description, "evidence": evidence}


def supported_signals(facts: dict) -> list[dict]:
    """Only create hypotheses that have direct supporting transaction categories."""
    categories = {row["category"]: row for row in facts["categories"]}
    signals = []
    definitions = [
        ("regular_income", "Observed recurring income", "Salary or pension payments recur; no profession or future stability is inferred.", ["salaire", "pension"], 2),
        ("student_activity", "Observed student activity", "Payments explicitly categorized as student work are present; age alone is insufficient.", ["job_etudiant"], 2),
        ("variable_income", "Variable earned income", "Service payments are present; the precise employment status is unknown.", ["revenu_activite"], 3),
        ("saver", "Saving habit", "Repeated savings transfers are observed; total wealth is unknown.", ["transfert_epargne"], 2),
        ("investor", "Observed regular investing", "Repeated transfers to an investment account are present; assets and risk tolerance are unknown.", ["investissement"], 2),
        ("car_mobility", "Observed car-related mobility", "Recurring fuel expenses are present; they do not establish car ownership.", ["carburant"], 3),
        ("public_transport", "Public transport usage", "Repeated public transport expenses are observed.", ["transport_public"], 3),
        ("past_travel", "Observed past travel", "Past bookings or accommodation are observed; no upcoming trip is confirmed.", ["voyage_transport", "hebergement_voyage"], 1),
        ("housing_payments", "Housing payments", "Rent or mortgage payments are present; they do not establish a future purchase plan.", ["loyer", "credit_logement"], 2),
    ]
    for identifier, label, description, names, minimum in definitions:
        rows = [categories[name] for name in names if name in categories]
        if sum(row["count"] for row in rows) >= minimum:
            signals.append(_signal(identifier, label, description, rows))
    return signals


def candidate_products(products: list[dict], profiles: list[dict], facts: dict, category: dict | None = None) -> list[dict]:
    if category is not None and (category.get("id", "").upper() == "UNKNOWN" or category.get("label", "").upper() == "UNKNOWN"):
        return []
    accepted = {profile["id"]: profile for profile in profiles}
    monthly = facts["monthly_cashflow"]
    # An observed overdraft or repeated negative cash flow precludes promotional offers.
    # This is a demo guardrail, not a creditworthiness or suitability calculation.
    if facts["habits"]["negative_balance_observation_count"] or sum(row["net_cents"] < 0 for row in monthly) >= 2:
        return []
    supported = []
    for product in products:
        name = product["name"].casefold()
        signal_ids = []
        reason = ""
        title = ""
        if "start2save" in name and "saver" in accepted:
            signal_ids = ["saver"]
            title = "Explore monthly saving"
            reason = "Savings transfers already exist. This product may be worth reviewing to compare automatic saving options."
        elif "investment plan" in name and "investor" in accepted:
            signal_ids = ["investor"]
            title = "Explore regular investing"
            reason = "Regular investments are observed. This supports an informational review of an investment plan; risk suitability has not been assessed."
        elif "spare change" in name and "investor" in accepted:
            signal_ids = ["investor"]
            title = "Explore investing spare change"
            reason = "The history already shows investment transfers. The rounding service is presented for information."
        elif "car insurance" in name and "car_mobility" in accepted and "assurance_auto" not in facts["existing_insurance"]:
            signal_ids = ["car_mobility"]
            title = "Explore car insurance coverage"
            reason = "Repeated fuel expenses suggest car usage. Existing coverage and vehicle ownership still need confirmation."
        elif "home insurance" in name and "housing_payments" in accepted and "assurance_habitation" not in facts["existing_insurance"]:
            signal_ids = ["housing_payments"]
            title = "Explore home insurance coverage"
            reason = "Housing payments are observed. Current coverage is unknown and needs checking."
        # Loans, retirement objectives and future travel require intent not present
        # in this dataset. Past purchases must not be turned into invented plans.
        if signal_ids:
            evidence = list(dict.fromkeys(line for signal_id in signal_ids for line in accepted[signal_id]["evidence"]))
            supported.append({**product, "title": title, "reason": reason, "evidence": evidence, "supporting_profiles": signal_ids})
    return supported


class Workflow:
    def __init__(self, data: BankData, jev: JevClient, max_api_concurrency: int = 10, category_service: Any = None):
        self.data = data
        self.jev = jev
        self.api_slots = asyncio.Semaphore(max_api_concurrency)
        if category_service is None:
            from app.categories import CategoryService
            category_service = CategoryService(jev)
        self.category_service = category_service

    async def _decide(self, state: dict, questions: dict) -> Any:
        async with self.api_slots:
            return await self.jev.decide(json.dumps(state, ensure_ascii=False, separators=(",", ":")), questions)

    async def analyse(self, client_id: str) -> dict:
        started = time.perf_counter()
        client = self.data.get(client_id)
        facts = self.data.facts(client_id)
        result = {
            "client": client_summary(client), "status": "insufficient_information", "summary": "",
            "profiles": [], "facts": facts, "missing_information": list(facts["missing_information"]),
            "category": None,
            "ads": [], "products_evaluated": 0,
            "metrics": {"duration_ms": 0.0, "api_calls": 0, "input_tokens": 0, "output_tokens": 0,
                        "estimated_cost_usd": 0.0, "usage_source": "none", "openai_calls": 0, "providers": {}},
            "stages": [], "error": None,
        }
        metrics = result["metrics"]
        active_stage = "Consent check"
        active_started = time.perf_counter()

        def stage(name: str, status: str, detail: str, duration: float = 0.0) -> None:
            result["stages"].append({"name": name, "status": status, "duration_ms": round(duration, 2), "detail": detail})

        def account(response: Any) -> None:
            metrics["api_calls"] += response.request_count
            retry_input = getattr(response, "estimated_retry_input_tokens", 0)
            metrics["input_tokens"] += response.input_tokens + retry_input
            metrics["output_tokens"] += response.output_tokens
            metrics["estimated_cost_usd"] += response.estimated_cost_usd
            estimated = response.tokens_estimated or response.retry_count > 0
            metrics["usage_source"] = "estimated" if estimated or metrics["usage_source"] == "estimated" else "provider"
            provider = metrics["providers"].setdefault("jev", {"api_calls": 0, "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0})
            provider["api_calls"] += response.request_count
            provider["input_tokens"] += response.input_tokens + retry_input
            provider["output_tokens"] += response.output_tokens
            provider["estimated_cost_usd"] += response.estimated_cost_usd
            provider["duration_ms"] = provider.get("duration_ms", 0.0) + response.duration_ms
            provider["tokens_estimated"] = provider.get("tokens_estimated", False) or estimated
            provider["usage_source"] = "estimated" if provider["tokens_estimated"] else "provider"

        def finish(status: str, summary: str) -> dict:
            result["status"] = status
            result["summary"] = summary
            if status != "recommended":
                result["ads"] = []
            metrics["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
            metrics["estimated_cost_usd"] = round(metrics["estimated_cost_usd"], 10)
            return result

        if not result["client"]["personalization_allowed"]:
            stage(active_stage, "skipped", "Commercial personalization is disabled: no AI requests and no advertisements.")
            return finish("opt_out", "This client has not consented to commercial personalization.")
        stage(active_stage, "completed", "Commercial consent is present in the synthetic data.")
        stage("Transaction aggregation", "completed", f"{facts['transaction_count']} transactions across {facts['observation_days']} days; amounts calculated in integer cents.")
        if facts["transaction_count"] < 8 or facts["observation_days"] < 30:
            stage("Information quality", "skipped", "Fewer than 8 transactions or 30 history days: abstain before any billable request.")
            return finish("insufficient_information", "Not enough information to identify a reliable habit. No advertisement proposed.")
        hypotheses = supported_signals(facts)
        if not hypotheses:
            stage("Information quality", "skipped", "No sufficiently repeated signal to submit to Jev.")
            return finish("insufficient_information", "The history does not provide a sufficiently specific signal to personalize an offer.")
        if not self.jev.configured:
            result["error"] = "JEV_API is not configured on the server."
            stage("Jev behavioral profiling", "error", result["error"])
            return finish("error", "The Jev analysis could not run.")
        try:
            active_stage = "Customer category"
            active_started = time.perf_counter()
            evidence_ids = {identifier for row in facts["categories"] for identifier in row["evidence"]}
            evidence = [
                {"id": tx["transaction_id"], "category": tx["categorie"], "direction": tx["sens"],
                 "date": tx["date"], "amount_cents": cents(tx["montant"])}
                for tx in client["compte"]["transactions"] if tx["transaction_id"] in evidence_ids
            ]
            category_state = json.dumps({"evidence": evidence, "monthly_cashflow": facts["monthly_cashflow"],
                                         "limitations": facts["limitations"] + facts["missing_information"]}, ensure_ascii=False)
            async with self.api_slots:
                classification = await self.category_service.classify(client_id, category_state, sorted(evidence_ids))
            result["category"] = classification["category"]
            category_metrics = classification["metrics"]
            for key in ("api_calls", "input_tokens", "output_tokens", "estimated_cost_usd", "openai_calls"):
                metrics[key] += category_metrics.get(key, 0)
            metrics["providers"] = {name: dict(values) for name, values in category_metrics.get("providers", {}).items()}
            if category_metrics.get("api_calls", 0):
                metrics["usage_source"] = "estimated" if category_metrics.get("tokens_estimated") else "provider"
            for item in classification.get("stages", []):
                stage(item.get("name", item.get("label", "Customer category")), item["status"],
                      item.get("detail", item.get("details", "")), item.get("duration_ms", 0))
            if classification.get("error"):
                error = classification["error"]
                result["error"] = error.get("message", "Customer categorization could not complete.")
                return finish("error", "The customer category could not be verified. No advertisement proposed.")
            category = classification["category"]
            if category.get("id", "").upper() == "UNKNOWN" or category.get("label", "").upper() == "UNKNOWN":
                return finish("insufficient_information", "The customer remains UNKNOWN because the available evidence is insufficient. No advertisement proposed.")
            active_stage = "Jev behavioral profiling"
            active_started = time.perf_counter()
            profile_questions = {
                item["id"]: {"type": "noul", "instructions": f"How strongly does the observed evidence support this behavioral hypothesis: {item['description']}? Return support from 0 (insufficient or contradicted) to 1 (direct repeated evidence). Do not infer intentions, demographics or purchases not explicitly observed."}
                for item in hypotheses
            }
            response = await self._decide({
                "task": "Validate behavioral hypotheses for a fictional banking customer using only the supplied observed facts. These are interest signals, not financial advice or eligibility decisions.",
                "as_of": facts["observation_end"], "currency": "EUR", "amount_unit": "integer cents",
                "customer_category": result["category"],
                "monthly_cashflow": facts["monthly_cashflow"], "hypotheses": hypotheses,
                "existing_insurance": facts["existing_insurance"], "limitations": facts["limitations"] + facts["missing_information"],
            }, profile_questions)
            account(response)
            for hypothesis in hypotheses:
                confidence = _confidence(response.answers, hypothesis["id"])
                if confidence >= PROFILE_THRESHOLD:
                    result["profiles"].append({"id": hypothesis["id"], "label": hypothesis["label"],
                                               "confidence": confidence, "evidence": hypothesis["evidence"]})
            stage(active_stage, "completed", f"{len(result['profiles'])} hypotheses retained out of {len(hypotheses)} ; support threshold {PROFILE_THRESHOLD:.0%}.", (time.perf_counter() - active_started) * 1000)
            if not result["profiles"]:
                return finish("insufficient_information", "Jev did not retain any profile with sufficient confidence. No advertisement proposed.")
            candidates = candidate_products(self.data.products, result["profiles"], facts, result["category"])
            stage("Catalogue filtering", "completed", f"{len(candidates)} candidate products out of {len(self.data.products)} ; observed insurance coverage and unconfirmed intentions considered.")
            if not candidates:
                if facts["habits"]["negative_balance_observation_count"] or sum(row["net_cents"] < 0 for row in facts["monthly_cashflow"]) >= 2:
                    result["missing_information"].append("Observed cash flows do not justify a commercial offer: budget and needs require clarification.")
                return finish("no_match", "Habits are observed, but no catalogue product has enough supporting evidence for an offer.")
            active_stage = "Jev product relevance"
            active_started = time.perf_counter()
            product_questions = {
                product["id"]: {"type": "noul", "instructions": f"How strongly is showing an informational advert for {product['name']} relevant to the observed habits? Use only its exact description and supporting evidence. Return 0 if evidence is insufficient, an observed insurance duplicates this offer, or it needs an unconfirmed future intention. Return 1 only for a directly supported interest. An advert never establishes financial suitability."}
                for product in candidates
            }
            response = await self._decide({
                "task": "Narrow an already filtered product catalogue for a fictional customer. Abstain whenever relevance is uncertain. Do not generate claims about product prices, rates, returns or suitability.",
                "profiles": result["profiles"], "candidates": candidates,
                "customer_category": result["category"],
                "monthly_cashflow": facts["monthly_cashflow"], "existing_insurance": facts["existing_insurance"],
                "limitations": facts["limitations"] + facts["missing_information"],
            }, product_questions)
            account(response)
            result["products_evaluated"] = len(candidates)
            for candidate in candidates:
                confidence = _confidence(response.answers, candidate["id"])
                if confidence >= PRODUCT_THRESHOLD:
                    result["ads"].append({"product_id": candidate["id"], "product_name": candidate["name"],
                                          "title": candidate["title"], "body": candidate["description"],
                                          "reason": candidate["reason"], "confidence": confidence, "evidence": candidate["evidence"]})
            result["ads"] = sorted(result["ads"], key=lambda item: item["confidence"], reverse=True)[:3]
            stage(active_stage, "completed", f"{len(result['ads'])} advertisements retained; relevance threshold {PRODUCT_THRESHOLD:.0%}.", (time.perf_counter() - active_started) * 1000)
            if result["ads"]:
                return finish("recommended", f"{len(result['profiles'])} habits supported by transactions ; {len(result['ads'])} relevant advertisements identified by Jev.")
            return finish("no_match", "Jev found no sufficiently relevant product. No advertisement proposed.")
        except JevError as exc:
            metrics["api_calls"] += exc.request_count
            metrics["input_tokens"] += getattr(exc, "estimated_input_tokens", 0)
            metrics["estimated_cost_usd"] += exc.estimated_cost_usd
            provider = metrics["providers"].setdefault("jev", {"api_calls": 0, "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0})
            provider["api_calls"] += exc.request_count
            provider["input_tokens"] += getattr(exc, "estimated_input_tokens", 0)
            provider["estimated_cost_usd"] += exc.estimated_cost_usd
            provider["duration_ms"] = provider.get("duration_ms", 0.0) + exc.duration_ms
            provider["tokens_estimated"] = provider.get("tokens_estimated", False) or exc.request_count > 0
            provider["usage_source"] = "estimated" if provider["tokens_estimated"] else ("provider" if provider["api_calls"] else "none")
            if exc.request_count:
                metrics["usage_source"] = "estimated"
            result["error"] = str(exc)
            stage(active_stage, "error", str(exc), (time.perf_counter() - active_started) * 1000)
            return finish("error", "Jev could not complete the analysis. No advertisement proposed.")
        except (ValueError, KeyError, TypeError) as exc:
            # Do not surface input data or provider response bodies in public errors.
            result["error"] = "The Jev response does not match the expected format."
            stage(active_stage, "error", result["error"], (time.perf_counter() - active_started) * 1000)
            return finish("error", "The analysis stopped to prevent an unverifiable recommendation.")
        except Exception:
            result["error"] = "An unexpected processing error interrupted this client analysis."
            stage(active_stage, "error", result["error"], (time.perf_counter() - active_started) * 1000)
            return finish("error", "The analysis could not complete. No advertisement proposed.")


def _confidence(answers: dict, key: str) -> float:
    value = answers[key]["noul"]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError("Invalid confidence")
    return round(value, 4)
