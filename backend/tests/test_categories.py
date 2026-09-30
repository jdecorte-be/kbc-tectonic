"""Persistent learning and conservative UNKNOWN fallback contract tests."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from backend.app.categories import CategoryRegistry, CategoryService, QUESTION_ID
from backend.app.jev import JevResult, JevError
from backend.app.openai_classifier import OpenAIResult, OpenAIError


PENSION_STATE = json.dumps({"scenario_simulation": "retired", "age": 72, "evidence": [
    {"id": "tx-1", "category": "pension", "direction": "credit", "date": "2026-08-01", "amount_cents": 180000},
    {"id": "tx-2", "category": "pension", "direction": "credit", "date": "2026-09-01", "amount_cents": 180000},
]})
RETIRED = {"action": "new", "category_id": "retired", "label": "Retired",
           "description": "Repeated pension income credits support an observed retirement income pattern.",
           "confidence": 0.96, "evidence_ids": ["tx-1", "tx-2"], "support_kind": "pension_income",
           "reason": "Two monthly pension credits are explicitly observed."}


class FakeJev:
    def __init__(self, choice="UNKNOWN", confidence=0.95):
        self.choice = choice
        self.confidence = confidence
        self.calls = []

    async def decide(self, state, questions):
        self.calls.append((state, questions))
        options = questions[QUESTION_ID]["criteria"]
        choice = self.choice(options) if callable(self.choice) else self.choice
        probabilities = {key: (self.confidence if key == choice else (1-self.confidence)/(len(options)-1)) for key in options}
        return JevResult(answers={QUESTION_ID: {"type": "choice", "choice": choice, "confidence": self.confidence, "probabilities": probabilities}},
                         model="fake-jev", input_tokens=120, output_tokens=30, tokens_estimated=False,
                         request_count=1, retry_count=0, duration_ms=2, estimated_cost_usd=0.000005)


class FakeOpenAI:
    def __init__(self, decision=None, error=None):
        self.decision = decision or dict(RETIRED)
        self.error = error
        self.calls = []

    async def classify(self, state, categories, evidence_ids):
        self.calls.append((state, categories, evidence_ids))
        if self.error:
            raise self.error
        return OpenAIResult(decision=self.decision, model="fake-openai", input_tokens=500, output_tokens=80,
                            tokens_estimated=False, request_count=1, retry_count=0, duration_ms=4,
                            estimated_cost_usd=0.000328)


class CategoryServiceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "categories.sqlite3"
        self.registry = CategoryRegistry(self.path)
        self.addCleanup(self.registry.close)

    async def test_unknown_learns_retired_and_next_jev_run_reuses_it(self):
        jev = FakeJev(choice=lambda options: "retired" if "retired" in options else "UNKNOWN")
        openai = FakeOpenAI()
        service = CategoryService(jev, self.registry, openai)
        self.assertNotIn("retired", {item["id"] for item in self.registry.snapshot()["items"]})
        first = await service.classify("customer-1", PENSION_STATE, ["tx-1", "tx-2"])
        self.assertEqual(first["category"]["id"], "retired")
        self.assertEqual(first["category"]["source"], "openai")
        self.assertTrue(first["category"]["created"])
        self.assertEqual(first["metrics"]["openai_calls"], 1)
        self.assertEqual(first["metrics"]["api_calls"], 2)
        self.assertEqual(first["metrics"]["input_tokens"], 620)
        self.assertNotIn("scenario_simulation", jev.calls[0][0])
        self.assertNotIn('"age"', jev.calls[0][0])
        second = await service.classify("customer-2", PENSION_STATE, ["tx-1", "tx-2"])
        self.assertEqual(second["category"]["id"], "retired")
        self.assertEqual(second["category"]["source"], "jev")
        self.assertFalse(second["category"]["created"])
        self.assertEqual(second["metrics"]["openai_calls"], 0)
        self.assertEqual(len(openai.calls), 1)
        self.assertIn("retired", jev.calls[1][1][QUESTION_ID]["criteria"])
        self.assertEqual(self.registry.assignment("customer-1")["category_id"], "retired")
        with sqlite3.connect(self.path) as db:
            rows = db.execute("SELECT options_json,answers_json FROM category_runs ORDER BY created_at").fetchall()
        self.assertNotIn("retired", json.loads(rows[0][0]))
        self.assertIn("retired", json.loads(rows[1][0]))
        self.assertIn("openai", json.loads(rows[0][1]))

    async def test_registry_survives_restart(self):
        service = CategoryService(FakeJev(), self.registry, FakeOpenAI())
        await service.classify("customer-1", PENSION_STATE, ["tx-1", "tx-2"])
        reloaded = CategoryRegistry(self.path)
        self.addCleanup(reloaded.close)
        retired = next(item for item in reloaded.snapshot()["items"] if item["id"] == "retired")
        self.assertEqual(retired["client_count"], 1)
        self.assertEqual(retired["source"], "openai")
        self.assertEqual(reloaded.snapshot()["questions"][0]["run_count"], 1)

    async def test_weak_or_invented_evidence_cannot_create_category(self):
        for change in ({"confidence": 0.6}, {"evidence_ids": ["tx-1", "invented"]}, {"evidence_ids": ["tx-1"]}, {"support_kind": "salary_income"}):
            with self.subTest(change=change):
                service = CategoryService(FakeJev(), self.registry, FakeOpenAI({**RETIRED, **change}))
                result = await service.classify("weak", PENSION_STATE, ["tx-1", "tx-2"])
                self.assertEqual(result["category"]["id"], "UNKNOWN")
                self.assertEqual(len(self.registry.snapshot()["items"]), 3)
                self.assertEqual(result["metrics"]["openai_calls"], 1)

    async def test_pension_savings_and_hidden_labels_do_not_prove_retirement(self):
        state = json.dumps({"scenario_simulation": {"evidence": json.loads(PENSION_STATE)["evidence"]},
                            "evidence": [{"id": "tx-1", "category": "pension", "direction": "debit"},
                                         {"id": "tx-2", "category": "pharmacy", "direction": "debit"}]})
        fallback = FakeOpenAI()
        result = await CategoryService(FakeJev(), self.registry, fallback).classify("invalid", state, ["tx-1", "tx-2"])
        self.assertEqual(result["category"]["id"], "UNKNOWN")
        self.assertEqual(json.loads(fallback.calls[0][0])["evidence"], [])

    async def test_sensitive_category_is_rejected(self):
        fallback = FakeOpenAI({**RETIRED, "label": "Medical pensioner", "description": "Pension payments suggest a medical disability."})
        result = await CategoryService(FakeJev(), self.registry, fallback).classify("invalid", PENSION_STATE, ["tx-1", "tx-2"])
        self.assertEqual(result["category"]["id"], "UNKNOWN")
        self.assertEqual(len(self.registry.snapshot()["items"]), 3)

    async def test_openai_refusal_is_error_with_usage_not_lack_of_information(self):
        refusal = OpenAIError("OpenAI declined classification.", code="refusal", request_count=1,
                              input_tokens=550, output_tokens=12, tokens_estimated=False, estimated_cost_usd=0.0002392)
        result = await CategoryService(FakeJev(), self.registry, FakeOpenAI(error=refusal)).classify("refused", PENSION_STATE, ["tx-1", "tx-2"])
        self.assertEqual(result["error"]["code"], "refusal")
        self.assertEqual(result["metrics"]["providers"]["openai"]["input_tokens"], 550)
        self.assertEqual(result["metrics"]["output_tokens"], 42)
        self.assertEqual(len(self.registry.snapshot()["items"]), 3)
        self.assertIsNone(self.registry.assignment("refused"))

    async def test_low_jev_confidence_triggers_fallback(self):
        service = CategoryService(FakeJev(choice="worker", confidence=0.4), self.registry, FakeOpenAI())
        result = await service.classify("low-confidence", PENSION_STATE, ["tx-1", "tx-2"])
        self.assertEqual(result["category"]["source"], "openai")
        self.assertEqual(result["metrics"]["openai_calls"], 1)

    async def test_provider_failure_does_not_invoke_openai_or_assign_unknown(self):
        class FailedJev:
            async def decide(self, *_):
                raise JevError("Jev timed out.", code="timeout", request_count=2,
                               estimated_input_tokens=300, estimated_cost_usd=0.0000126)
        fallback = FakeOpenAI()
        result = await CategoryService(FailedJev(), self.registry, fallback).classify("failed", PENSION_STATE, ["tx-1", "tx-2"])
        self.assertEqual(result["error"]["provider"], "jev")
        self.assertEqual(result["metrics"]["api_calls"], 2)
        self.assertEqual(result["metrics"]["input_tokens"], 300)
        self.assertEqual(result["metrics"]["openai_calls"], 0)
        self.assertEqual(fallback.calls, [])
        self.assertIsNone(self.registry.assignment("failed"))

    async def test_concurrent_duplicate_labels_are_created_once(self):
        other = CategoryRegistry(self.path)
        self.addCleanup(other.close)
        def learn(registry, label):
            return registry.learn(label=label, description=RETIRED["description"], support_kind="pension_income", client_id="race", evidence=["tx-1", "tx-2"], model="mock")
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(learn, self.registry, "Retired"), executor.submit(learn, other, "Retiree")]
            outcomes = [future.result() for future in futures]
        self.assertEqual(sum(created for _, created in outcomes), 1)
        self.assertEqual([item["id"] for item in self.registry.snapshot()["items"]].count("retired"), 1)


if __name__ == "__main__":
    unittest.main()
