"""Dashboard cohorts, consent and saved-outcome lineage without provider calls."""
import gc
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.banking import sparse_client
from app.config import Settings
from app.crud import BankRepository
from app.dashboard import DashboardService
from app.main import create_app
from app.run_store import RunStore


PRODUCTS = [{"id": "investment-plan", "name": "Investment plan", "description": "Regular investment service."}]


def customer(identifier, age=24, consent=True, salary=2, investments=2, pension=0):
    profile = {"client_id": identifier, "synthetique": True, "prenom": f"Client {identifier}", "age": age,
               "ville": "Bruxelles", "pays": "Belgique", "scenario_simulation": "SECRET_PERSONA",
               "preferences": {"personnalisation_commerciale": consent}}
    transactions = []
    balance = 100000
    for category, direction, count, amount in [
        ("salaire", "credit", salary, 200000), ("investissement", "debit", investments, 10000),
        ("pension", "credit", pension, 150000), ("transfert_epargne", "debit", 2, 5000),
        ("loyer", "debit", 2, 60000),
    ]:
        for index in range(count):
            balance += amount if direction == "credit" else -amount
            transactions.append({"transaction_id": f"{identifier}-{len(transactions)}", "date": f"2026-0{7 + index % 3}-15",
                                 "sens": direction, "montant": amount / 100, "categorie": category,
                                 "contrepartie": f"Fictional {category}", "type": "ordre_permanent" if direction == "debit" else "virement",
                                 "solde_apres": balance / 100})
    # Validators require transactions sorted by date and matching running balances.
    transactions.sort(key=lambda item: item["date"])
    balance = 100000
    for item in transactions:
        balance += round(item["montant"] * 100) * (1 if item["sens"] == "credit" else -1)
        item["solde_apres"] = balance / 100
    profile["compte"] = {"compte_id": f"AC-{identifier}", "debut_historique": "2026-07-01", "fin_historique": "2026-09-30",
                         "solde_initial": 1000, "solde_final": balance / 100, "transactions": transactions}
    return profile


def saved_result(identifier="young", status="recommended"):
    return {"client": {"id": identifier}, "status": status, "summary": f"Saved {status} decision.",
            "category": {"id": "investor", "label": "Investor", "extra": "not in DTO"},
            "ads": [{"product_id": "investment-plan", "product_name": "Old label", "title": "Explore regular investing",
                     "reason": "Repeated investment transfers.", "confidence": .91}],
            "metrics": {"duration_ms": 1, "estimated_cost_usd": 0}}


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.url = f"sqlite:///{self.root / 'bank.db'}"
        self.repository = BankRepository(self.url)
        self.profiles = [customer("young"), customer("one-salary", salary=1),
                         customer("off", consent=False), customer("pension", age=67, salary=0, investments=0, pension=2),
                         sparse_client()]
        self.repository.seed(self.profiles, PRODUCTS)
        self.store = RunStore(self.repository.engine)
        self.dashboard = DashboardService(self.repository, self.store)

    def tearDown(self):
        self.repository.close()
        self.temp.cleanup()
        # Collect TestClient portal streams in this test, before CLI tests capture stderr.
        gc.collect()

    def test_observed_segments_need_transaction_evidence_and_consent(self):
        item = self.dashboard.client_context("young")
        tags = {row["id"]: row for row in item["segments"]}
        self.assertIn("young_investor", tags)
        self.assertIn("Recorded age: 24", tags["young_investor"]["evidence"][0])
        self.assertIn("2 salary credits", tags["young_investor"]["evidence"][1])
        self.assertEqual(item["context"]["monthly_income_cents"], 133333)
        self.assertEqual(item["context"]["investment_cents"], 20000)
        self.assertEqual(item["context"]["savings_cents"], 10000)
        self.assertEqual(item["context"]["recurring_payment_count"], 3)
        self.assertNotIn("young_investor", {row["id"] for row in self.dashboard.client_context("one-salary")["segments"]})
        self.assertIn("retired", {row["id"] for row in self.dashboard.client_context("pension")["segments"]})
        self.assertEqual(self.dashboard.client_context("SYN-SPARSE")["segments"], [])
        self.store.save_analysis(saved_result("off"))
        opted_out = self.dashboard.client_context("off")
        self.assertEqual(opted_out["segments"], [])
        self.assertEqual(opted_out["analysis"]["status"], "opt_out")
        self.assertIsNone(opted_out["analysis"]["category"])
        self.assertEqual(opted_out["analysis"]["ads"], [])
        self.assertNotIn("SECRET", json.dumps(self.dashboard.snapshot()))

    def test_newest_single_or_benchmark_wins_and_errors_clear_old_ads(self):
        with patch("app.run_store._now", return_value="2026-09-30T10:00:00+00:00"):
            first = self.store.save_analysis(saved_result())
        with patch("app.run_store._now", return_value="2026-09-30T10:01:00+00:00"):
            self.store.save_benchmark({"id": "batch", "status": "running", "results": [saved_result(status="no_match")]})
        item = self.dashboard.client_context("young")
        self.assertEqual(item["analysis"]["source"], "benchmark")
        self.assertEqual(item["analysis"]["status"], "no_match")
        self.assertEqual(item["analysis"]["ads"], [])
        with patch("app.run_store._now", return_value="2026-09-30T10:02:00+00:00"):
            newest = self.store.save_analysis(saved_result())
        # A later checkpoint for another customer must not retimestamp existing decisions.
        with patch("app.run_store._now", return_value="2026-09-30T10:03:00+00:00"):
            self.store.save_benchmark({"id": "batch", "status": "completed", "results": [saved_result("pension")]}, results_offset=1)
        item = self.dashboard.client_context("young")
        self.assertEqual(item["analysis"]["id"], newest)
        self.assertNotEqual(item["analysis"]["id"], first)
        self.assertEqual(len(item["analysis"]["ads"]), 1)
        self.assertEqual(item["analysis"]["ads"][0]["product_name"], "Investment plan")
        with patch("app.run_store._now", return_value="2026-09-30T10:04:00+00:00"):
            self.store.save_analysis(saved_result(status="error"))
        snapshot = self.dashboard.snapshot()
        self.assertEqual(snapshot["summary"]["error_count"], 1)
        self.assertEqual(self.dashboard.client_context("young")["analysis"]["ads"], [])
        self.assertEqual(snapshot["summary"]["analyzed_count"], 2)
        self.assertNotIn("_dashboard_saved_at", json.dumps(self.store.get_benchmark("batch")))

    def test_no_saved_analysis_does_not_invent_ads(self):
        snapshot = self.dashboard.snapshot()
        self.assertEqual(snapshot["summary"]["selected_ad_count"], 0)
        self.assertEqual(snapshot["summary"]["recommended_count"], 0)
        self.assertEqual(snapshot["summary"]["analyzed_count"], 0)
        self.assertTrue(all(not item["analysis"]["ads"] for item in snapshot["clients"]["items"]))
        self.assertTrue(all(node["kind"] != "product" for node in snapshot["network"]["nodes"]))
        sparse = self.dashboard.client_context("SYN-SPARSE")
        self.assertEqual(sparse["analysis"]["status"], "not_analyzed")
        self.assertIsNone(sparse["analysis"]["source"])

    def test_filters_and_pagination_use_full_cohort_totals(self):
        self.store.save_analysis(saved_result())
        full = self.dashboard.snapshot(opt_in_only=True)
        page = self.dashboard.snapshot(opt_in_only=True, limit=1, offset=2)
        self.assertEqual(page["clients"]["total"], 4)
        self.assertEqual(len(page["clients"]["items"]), 1)
        self.assertEqual(page["summary"], full["summary"])
        self.assertEqual(page["cashflow"], full["cashflow"])
        self.assertEqual(page["summary"]["opt_out_count"], 0)
        filtered = self.dashboard.snapshot(segment="young_investor")
        self.assertEqual(filtered["clients"]["total"], 1)
        self.assertEqual(filtered["clients"]["items"][0]["client"]["id"], "young")
        self.assertEqual(filtered["segments"], self.dashboard.snapshot()["segments"])
        recommended = self.dashboard.snapshot(product="investment-plan", outcome="recommended")
        self.assertEqual(recommended["summary"]["total_clients"], 1)
        self.assertEqual(recommended["summary"]["selected_ad_count"], 1)
        self.assertEqual(self.dashboard.snapshot(query="pension")["clients"]["total"], 1)
        self.assertEqual(self.dashboard.snapshot(query="missing")["cashflow"], [])
        selected_profile = self.profiles[0]
        self.assertEqual(sum(row["credit_cents"] for row in filtered["cashflow"]), 400000)
        self.assertEqual(filtered["summary"]["total_balance_cents"], round(selected_profile["compte"]["solde_final"] * 100))
        self.assertEqual(filtered["network"]["shown_clients"], 1)
        node_ids = {node["id"] for node in filtered["network"]["nodes"]}
        self.assertTrue(all(edge["source"] in node_ids and edge["target"] in node_ids for edge in filtered["network"]["links"]))

    def test_queries_are_grouped_and_do_not_load_transaction_histories(self):
        statements = []
        def capture(_connection, _cursor, statement, _parameters, _context, _many):
            if statement.lstrip().upper().startswith("SELECT"):
                statements.append(statement)
        event.listen(self.repository.engine, "before_cursor_execute", capture)
        try:
            with patch.object(self.repository, "get_client", side_effect=AssertionError("No full client history")):
                self.dashboard.snapshot()
        finally:
            event.remove(self.repository.engine, "before_cursor_execute", capture)
        self.assertEqual(len(statements), 6)
        transaction_queries = [statement for statement in statements if "bank_transactions" in statement]
        self.assertEqual(len(transaction_queries), 3)
        self.assertTrue(all("GROUP BY" in statement for statement in transaction_queries))
        self.assertTrue(any("row_number() OVER" in statement for statement in statements))

    def test_http_context_dashboard_consent_and_validation(self):
        source = self.root / "clients.json"
        catalogue = self.root / "products.json"
        source.write_text(json.dumps(self.profiles))
        catalogue.write_text(json.dumps(PRODUCTS))
        config = Settings(DATABASE_URL=self.url, BANK_DATA_PATH=str(source), PRODUCTS_PATH=str(catalogue),
                          CATEGORY_DB_PATH=str(self.root / "categories.db"))
        with TestClient(create_app(config)) as client:
            response = client.get("/api/dashboard", params={"opt_in_only": True, "limit": 1, "offset": 1})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["summary"]["total_clients"], 4)
            self.assertIsNone(response.json()["clients"]["items"][0]["analysis"]["source"])
            self.assertEqual(client.get("/api/clients", params={"opt_in_only": True, "limit": 1}).json()["total"], 4)
            context = client.get("/api/clients/young/context")
            self.assertEqual(context.status_code, 200, context.text)
            self.assertEqual(context.json()["segments"][0]["id"], "young_investor")
            self.assertEqual(client.get("/api/clients/missing/context").status_code, 404)
            self.assertEqual(client.get("/api/dashboard", params={"offset": -1}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
