"""Persistent categories: Jev first, guarded OpenAI learning only after UNKNOWN.

The registry begins with Student, Worker and UNKNOWN. Learned categories and
their evidence requirements become Jev choices on the very next analysis.
SQLite stores question definitions, the options used by each run, provider
answers, category provenance and the latest successful customer assignment.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import threading
import time
import unicodedata
import uuid
from datetime import datetime, timezone
from typing import Any

from .jev import JevError
from .openai_classifier import OpenAIClassifier, OpenAIError, CategoryDecision


QUESTION_ID = "income_life_stage"
QUESTION_INSTRUCTIONS = (
    "Which registered income/life-stage category is directly supported by this fictional customer's "
    "observed transactions? Use repeated concrete evidence, not age, names, purchases, hidden simulation "
    "labels or inferred sensitive traits. Pension credits are not salary; pension savings are not "
    "pension income. Choose UNKNOWN when no listed category fits, evidence is weak, or categories conflict."
)
JEV_THRESHOLD = 0.70
OPENAI_THRESHOLD = 0.85
MAX_CATEGORIES = 100
INCOME_KINDS = {
    "student_income": {"job_etudiant", "student_income", "student_job", "student_salary"},
    "salary_income": {"salaire", "salary", "salary_income", "employment_income", "wages"},
    "business_income": {"revenu_activite", "business_income", "invoice_payment", "freelance_income"},
    "pension_income": {"pension", "pension_income", "retirement_pension"},
}
SENSITIVE_TERMS = re.compile(r"\b(health|medical|religio\w*|christian|muslim|jewish|ethnic\w*|racial|race|politic\w*|sexual\w*|disabled|disability|pregnan\w*|cancer|diabet\w*|creditworth\w*)\b", re.I)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normal_label(label: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", label).casefold().split())


def _category_identity(label: str) -> tuple[str, str]:
    label = " ".join(unicodedata.normalize("NFKC", label).split())
    if not 2 <= len(label) <= 60 or not re.fullmatch(r"[A-Za-z][A-Za-z0-9 &'()-]*", label):
        raise ValueError("Category labels must be concise English text.")
    if _normal_label(label) in {"unknown", "none", "other", "miscellaneous", "uncategorized"}:
        raise ValueError("A vague category cannot be learned.")
    # Common equivalent labels must not create duplicate categories in concurrent runs.
    aliases = {"retiree": "Retired", "pensioner": "Retired", "retired person": "Retired",
               "employee": "Worker", "employed": "Worker", "students": "Student"}
    label = aliases.get(_normal_label(label), label)
    identifier = re.sub(r"[^a-z0-9]+", "_", label.casefold()).strip("_")
    return identifier, label


class CategoryRegistry:
    def __init__(self, path: str | Path | None = None):
        default_path = Path(__file__).resolve().parents[2] / "data" / "categories.sqlite3"
        self.path = str(path or os.getenv("CATEGORY_DB_PATH") or default_path)
        if self.path != ":memory:":
            Path(self.path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._db = sqlite3.connect(self.path, timeout=10, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS category_questions (
                id TEXT PRIMARY KEY, instructions TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS categories (
                id TEXT PRIMARY KEY, label TEXT NOT NULL, normalized_label TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL, support_kind TEXT NOT NULL, source TEXT NOT NULL,
                created_at TEXT NOT NULL, created_by_client TEXT, provenance_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS category_runs (
                id TEXT PRIMARY KEY, client_id TEXT NOT NULL, question_id TEXT NOT NULL,
                created_at TEXT NOT NULL, state_sha256 TEXT NOT NULL, options_json TEXT NOT NULL,
                answers_json TEXT NOT NULL, category_json TEXT NOT NULL, metrics_json TEXT NOT NULL,
                error_json TEXT, FOREIGN KEY(question_id) REFERENCES category_questions(id)
            );
            CREATE TABLE IF NOT EXISTS customer_categories (
                client_id TEXT NOT NULL, question_id TEXT NOT NULL, category_id TEXT NOT NULL,
                confidence REAL NOT NULL, source TEXT NOT NULL, evidence_json TEXT NOT NULL,
                updated_at TEXT NOT NULL, run_id TEXT NOT NULL,
                PRIMARY KEY(client_id, question_id),
                FOREIGN KEY(category_id) REFERENCES categories(id),
                FOREIGN KEY(run_id) REFERENCES category_runs(id)
            );
        """)
        with self._db:
            self._db.execute("INSERT OR IGNORE INTO category_questions VALUES (?, ?, ?)", (QUESTION_ID, QUESTION_INSTRUCTIONS, _now()))
            seeds = [
                ("student", "Student", "Repeated explicit student job income supports student activity; age and small payments alone are insufficient.", "student_income"),
                ("worker", "Worker", "Repeated earned salary credits support an employed worker; pension or business income alone does not match.", "salary_income"),
                ("UNKNOWN", "UNKNOWN", "No existing category is supported, the information is insufficient, or the category is ambiguous.", "none"),
            ]
            for identifier, label, description, support in seeds:
                self._db.execute("INSERT OR IGNORE INTO categories VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                 (identifier, label, _normal_label(label), description, support, "seed", _now(), None, "{}"))

    def close(self) -> None:
        with self._lock:
            self._db.close()

    def snapshot(self) -> dict:
        with self._lock:
            rows = self._db.execute("""SELECT c.id,c.label,c.description,c.support_kind,c.source,c.created_at,
                c.created_by_client,COUNT(a.client_id) AS client_count
                FROM categories c LEFT JOIN customer_categories a ON a.category_id=c.id
                GROUP BY c.id ORDER BY CASE WHEN c.id='UNKNOWN' THEN 1 ELSE 0 END,c.created_at,c.id""").fetchall()
            items = [dict(row) for row in rows]
            question = dict(self._db.execute("SELECT * FROM category_questions WHERE id=?", (QUESTION_ID,)).fetchone())
            question["options"] = {item["id"]: f"{item['label']}: {item['description']}" for item in items}
            question["run_count"] = self._db.execute("SELECT COUNT(*) FROM category_runs").fetchone()[0]
            return {"items": items, "questions": [question]}

    def learn(self, *, label: str, description: str, support_kind: str, client_id: str, evidence: list[str], model: str) -> tuple[dict, bool]:
        identifier, label = _category_identity(label)
        description = " ".join(description.split())
        if not 15 <= len(description) <= 300 or SENSITIVE_TERMS.search(label + " " + description):
            raise ValueError("The proposed category is unsupported or outside the income classification scope.")
        if support_kind not in {*INCOME_KINDS, "mixed_income"} or len(set(evidence)) < 2:
            raise ValueError("A learned category requires repeated verified income evidence.")
        with self._lock:
            # Serializes semantic deduplication and insertion across processes too.
            self._db.execute("BEGIN IMMEDIATE")
            try:
                existing = self._db.execute("SELECT * FROM categories WHERE id=? OR normalized_label=?", (identifier, _normal_label(label))).fetchone()
                if existing:
                    if existing["support_kind"] != support_kind:
                        raise ValueError("A conflicting category with this label already exists.")
                    self._db.commit()
                    return dict(existing), False
                if self._db.execute("SELECT COUNT(*) FROM categories").fetchone()[0] >= MAX_CATEGORIES:
                    raise ValueError("The category registry limit has been reached.")
                created_at = _now()
                provenance = json.dumps({"provider": "openai", "model": model, "evidence": evidence, "client_id": client_id, "trigger": "jev_unknown"})
                self._db.execute("INSERT INTO categories VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                 (identifier, label, _normal_label(label), description, support_kind, "openai", created_at, client_id, provenance))
                self._db.commit()
                return {"id": identifier, "label": label, "description": description, "support_kind": support_kind,
                        "source": "openai", "created_at": created_at}, True
            except Exception:
                self._db.rollback()
                raise

    def record(self, client_id: str, state: str, options: dict, answers: dict, result: dict) -> str:
        run_id = str(uuid.uuid4())
        category = result["category"]
        with self._lock, self._db:
            self._db.execute("INSERT INTO category_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                run_id, client_id, QUESTION_ID, _now(), hashlib.sha256(state.encode()).hexdigest(),
                json.dumps(options), json.dumps(answers), json.dumps(category), json.dumps(result["metrics"]),
                json.dumps(result["error"]) if result.get("error") else None,
            ))
            if not result.get("error"):
                self._db.execute("""INSERT INTO customer_categories VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(client_id,question_id) DO UPDATE SET category_id=excluded.category_id,
                    confidence=excluded.confidence,source=excluded.source,evidence_json=excluded.evidence_json,
                    updated_at=excluded.updated_at,run_id=excluded.run_id""", (
                    client_id, QUESTION_ID, category["id"], category["confidence"], category["source"],
                    json.dumps(category["evidence"]), _now(), run_id,
                ))
        return run_id

    def assignment(self, client_id: str) -> dict | None:
        with self._lock:
            row = self._db.execute("SELECT * FROM customer_categories WHERE client_id=? AND question_id=?", (client_id, QUESTION_ID)).fetchone()
            if row is None:
                return None
            result = dict(row)
            result["evidence"] = json.loads(result.pop("evidence_json"))
            return result


def _evidence_records(state: str, allowed_ids: list[str]) -> tuple[str, dict[str, dict]]:
    """Keep only explicit observed income records; never forward hidden labels or sensitive purchases."""
    parsed = json.loads(state)
    allowed = set(allowed_ids)
    records: dict[str, dict] = {}

    def visit(value):
        if isinstance(value, dict):
            identifier = value.get("id") or value.get("transaction_id")
            category = str(value.get("category") or value.get("categorie") or "").casefold()
            direction = value.get("direction") or value.get("sens")
            kind = next((kind for kind, categories in INCOME_KINDS.items() if category in categories), None)
            if identifier in allowed and kind and direction == "credit":
                records[identifier] = {"id": identifier, "category": category, "direction": "credit",
                                       "date": value.get("date"), "amount_cents": value.get("amount_cents"), "support_kind": kind}
            for key, item in value.items():
                if key.casefold() not in {"scenario_simulation", "ground_truth", "hidden_label", "expected_category"}:
                    visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(parsed)
    sanitized = json.dumps({"synthetic": True, "evidence": list(records.values()),
                            "limitations": "Only observed income credits are provided. Age, sensitive purchases and simulation labels are excluded."}, separators=(",", ":"))
    return sanitized, records


def _supported_ids(kind: str, records: dict[str, dict], cited: list[str] | None = None) -> list[str]:
    ids = list(dict.fromkeys(cited if cited is not None else records))
    if any(identifier not in records for identifier in ids):
        return []
    relevant = [identifier for identifier in ids if kind == "mixed_income" or records[identifier]["support_kind"] == kind]
    if cited is not None and len(relevant) != len(ids):
        return []
    if len(relevant) < 2:
        return []
    if kind == "mixed_income" and len({records[identifier]["support_kind"] for identifier in relevant}) < 2:
        return []
    return relevant[:12]


def _empty_metrics() -> dict:
    return {"input_tokens": 0, "output_tokens": 0, "api_calls": 0, "estimated_cost_usd": 0.0,
            "duration_ms": 0.0, "tokens_estimated": False, "usage_source": "none"}


class CategoryService:
    def __init__(self, jev, registry: CategoryRegistry | None = None, openai_client: OpenAIClassifier | None = None):
        self.jev = jev
        self.registry = registry or CategoryRegistry()
        self.openai = openai_client or OpenAIClassifier()
        self._owns_registry = registry is None
        self._owns_openai = openai_client is None

    async def close(self) -> None:
        if self._owns_openai:
            await self.openai.close()
        if self._owns_registry:
            self.registry.close()

    async def classify(self, client_id: str, state: str, evidence_ids: list[str]) -> dict:
        started = time.perf_counter()
        snapshot = self.registry.snapshot()
        question = snapshot["questions"][0]
        options = question["options"]
        items = {item["id"]: item for item in snapshot["items"]}
        metrics = {**_empty_metrics(), "openai_calls": 0, "providers": {"jev": _empty_metrics(), "openai": _empty_metrics()}}
        result = {"category": {"id": "UNKNOWN", "label": "UNKNOWN", "source": "unknown", "confidence": 0.0, "evidence": [], "created": False},
                  "metrics": metrics, "stages": [], "error": None}
        answers = {}

        def stage(identifier, label, status, detail, duration=0):
            result["stages"].append({"id": identifier, "label": label, "name": label, "status": status,
                                     "details": detail, "detail": detail, "duration_ms": round(duration, 2)})

        def account(provider, response, error=False):
            target = metrics["providers"][provider]
            counts = response.request_count
            tokens = (getattr(response, "input_tokens", getattr(response, "estimated_input_tokens", 0))
                      + (0 if error else getattr(response, "estimated_retry_input_tokens", 0)))
            output = getattr(response, "output_tokens", 0)
            estimated = getattr(response, "tokens_estimated", True) or getattr(response, "retry_count", 0) > 0
            for name, value in (("input_tokens", tokens), ("output_tokens", output), ("api_calls", counts),
                                ("estimated_cost_usd", response.estimated_cost_usd), ("duration_ms", response.duration_ms)):
                target[name] += value
                metrics[name] += value
            target["tokens_estimated"] |= estimated and counts > 0
            metrics["tokens_estimated"] |= estimated and counts > 0
            target["usage_source"] = "estimated" if target["tokens_estimated"] else ("provider" if target["api_calls"] else "none")
            metrics["usage_source"] = "estimated" if metrics["tokens_estimated"] else ("provider" if metrics["api_calls"] else "none")
            if provider == "openai":
                metrics["openai_calls"] += counts

        def finish():
            metrics["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
            result["run_id"] = self.registry.record(client_id, state, options, answers, result)
            return result

        try:
            clean_state, records = _evidence_records(state, evidence_ids)
        except (ValueError, TypeError):
            result["error"] = {"provider": "local", "code": "invalid_state", "message": "Category evidence must be valid structured transaction data."}
            stage("category_evidence", "Category evidence", "error", result["error"]["message"])
            return finish()
        try:
            jev_result = await self.jev.decide(clean_state, {QUESTION_ID: {"type": "choice", "instructions": question["instructions"], "criteria": options}})
            account("jev", jev_result)
            answer = jev_result.answers[QUESTION_ID]
            answers["jev"] = answer
            selected = answer["choice"]
            confidence = min(float(answer["confidence"]), float(answer["probabilities"].get(selected, 0)))
            supported = _supported_ids(items.get(selected, {}).get("support_kind", "none"), records)
            if selected in items and selected != "UNKNOWN" and confidence >= JEV_THRESHOLD and supported:
                item = items[selected]
                result["category"] = {"id": item["id"], "label": item["label"], "source": "jev", "confidence": confidence, "evidence": supported, "created": False}
                stage("category_jev", "Jev category", "completed", f"{item['label']} selected from {len(options)} registered choices; repeated income evidence verified.", jev_result.duration_ms)
                stage("category_openai", "OpenAI fallback", "skipped", "Jev resolved an existing category with sufficient evidence.")
                return finish()
            stage("category_jev", "Jev category", "completed", "UNKNOWN: no listed category has sufficient confidence and verified repeated evidence.", jev_result.duration_ms)
        except JevError as exc:
            account("jev", exc, error=True)
            result["error"] = {"provider": "jev", "code": exc.code, "message": str(exc)}
            stage("category_jev", "Jev category", "error", str(exc), exc.duration_ms)
            return finish()

        try:
            fallback = await self.openai.classify(clean_state, snapshot["items"], list(records))
            account("openai", fallback)
            decision = CategoryDecision.model_validate(fallback.decision).model_dump()
            answers["openai"] = decision
            cited = decision["evidence_ids"]
            supported = _supported_ids(decision["support_kind"], records, cited)
            if decision["action"] == "unknown" or decision["confidence"] < OPENAI_THRESHOLD or not supported:
                stage("category_openai", "OpenAI fallback", "completed", "UNKNOWN retained: a new category needs high confidence and at least two verified, relevant income observations.", fallback.duration_ms)
                return finish()
            created = False
            if decision["action"] == "existing":
                item = items.get(decision["category_id"])
                if not item or item["id"] == "UNKNOWN" or item["support_kind"] != decision["support_kind"]:
                    raise ValueError("An existing category must match the saved registry definition.")
            else:
                # A claimed retirement label must be backed by pension income, even
                # if the model incorrectly claims another support kind.
                normalized = _normal_label(decision["label"])
                if any(word in normalized for word in ("retir", "pension")) and decision["support_kind"] != "pension_income":
                    raise ValueError("Retirement categories require repeated pension credits.")
                item, created = self.registry.learn(label=decision["label"], description=decision["description"],
                    support_kind=decision["support_kind"], client_id=client_id, evidence=supported, model=fallback.model)
            result["category"] = {"id": item["id"], "label": item["label"], "source": "openai", "confidence": decision["confidence"], "evidence": supported, "created": created}
            detail = f"{item['label']} {'created and saved for future Jev analyses' if created else 'matched to the existing registry'}; cited income transactions verified."
            stage("category_openai", "OpenAI fallback", "completed", detail, fallback.duration_ms)
            return finish()
        except OpenAIError as exc:
            account("openai", exc, error=True)
            result["error"] = {"provider": "openai", "code": exc.code, "message": str(exc)}
            stage("category_openai", "OpenAI fallback", "error", str(exc), exc.duration_ms)
            return finish()
        except ValueError:
            stage("category_openai", "OpenAI fallback", "completed", "UNKNOWN retained: the proposed category did not pass the evidence and registry checks.")
            return finish()
