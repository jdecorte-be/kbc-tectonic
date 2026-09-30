from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pydantic import ValidationError
from sqlalchemy import event, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.banking import BankData, client_summary, extract_facts
from app.crud import BankRepository
from app.data_validation import customer_payload, validate_profiles
from app.models import Account, DatasetMetadata, Transaction


PRODUCTS = [{"id": "saving", "name": "Savings account", "description": "Save a fixed amount every month."}]


def customer(identifier="SYN-TEST", name="Jules_One"):
    return {
        "client_id": identifier, "synthetique": True, "prenom": name, "age": 30,
        "ville": "Bruxelles", "pays": "Belgique", "scenario_simulation": "SECRET_PROFILE",
        "risk_tolerance": "SECRET_RISK", "preferences": {"personnalisation_commerciale": True},
        "compte": {
            "compte_id": f"AC-{identifier}", "debut_historique": "2026-07-01", "fin_historique": "2026-09-30",
            "solde_initial": 100, "solde_final": 117.63,
            "transactions": [
                {"transaction_id": f"{identifier}-1", "date": "2026-07-01", "sens": "credit", "montant": 20.11,
                 "categorie": "salaire", "contrepartie": "Fictional employer", "type": "virement",
                 "solde_apres": 120.11, "crediteur": identifier, "pays_contrepartie": "Belgique"},
                {"transaction_id": f"{identifier}-2", "date": "2026-07-02", "sens": "debit", "montant": 3.59,
                 "categorie": "alimentation", "contrepartie": "Fictional grocer", "type": "paiement_carte",
                 "solde_apres": 116.52, "debiteur": identifier, "pays_contrepartie": "Belgique"},
                {"transaction_id": f"{identifier}-3", "date": "2026-07-03", "sens": "credit", "montant": 1.11,
                 "categorie": "remboursement", "contrepartie": "Fictional grocer", "type": "virement",
                 "solde_apres": 117.63, "transaction_origine_id": f"{identifier}-2", "pays_contrepartie": "Belgique"},
            ],
        },
    }


class BankingRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database_url = f"sqlite:///{Path(self.temp.name) / 'bank.sqlite3'}"
        self.repository = BankRepository(self.database_url)

    def tearDown(self):
        self.repository.close()
        self.temp.cleanup()

    def test_normalized_round_trip_exact_money_and_no_simulated_truth(self):
        original = customer()
        self.assertTrue(self.repository.seed([original], PRODUCTS))
        self.assertFalse(self.repository.seed([original], PRODUCTS))
        stored = self.repository.get_client(original["client_id"])
        expected = customer_payload(validate_profiles([original])[0])
        self.assertEqual(stored, expected)
        self.assertEqual(extract_facts(stored), extract_facts(expected))
        self.assertEqual(self.repository.list_clients()["items"], [client_summary(stored)])
        self.assertEqual(self.repository.counts(), {"clients": 1, "accounts": 1, "transactions": 3, "products": 1})
        self.assertNotIn("SECRET", json.dumps(stored))
        with Session(self.repository.engine) as session:
            account = session.scalar(select(Account))
            amounts = list(session.scalars(select(Transaction.amount_cents).order_by(Transaction.ordinal)))
            self.assertEqual(account.balance_cents, 11763)
            self.assertEqual(amounts, [2011, 359, 111])
            self.assertNotIn("SECRET", " ".join(item.value for item in session.scalars(select(DatasetMetadata))))
        self.assertTrue(self.repository.check_health())

    def test_invalid_imports_are_rejected_before_any_records_are_written(self):
        mutations = [
            lambda p: p.update(synthetique=False),
            lambda p: p.update(synthetique="true"),
            lambda p: p["preferences"].update(personnalisation_commerciale="false"),
            lambda p: p["compte"].update(solde_final=0),
            lambda p: p["compte"].update(fin_historique="2026-06-30"),
            lambda p: p["compte"].update(nombre_transactions=2),
            lambda p: p["compte"].update(total_debits=5),
            lambda p: p["compte"]["transactions"][0].update(montant="NaN"),
            lambda p: p["compte"]["transactions"][0].update(montant="Infinity"),
            lambda p: p["compte"]["transactions"][0].update(montant=-1),
            lambda p: p["compte"]["transactions"][0].update(montant=1.001),
            lambda p: p["compte"]["transactions"][0].update(sens="unknown"),
            lambda p: p["compte"]["transactions"][0].update(devise="USD"),
            lambda p: p["compte"]["transactions"][0].update(crediteur="another-client"),
            lambda p: p["compte"]["transactions"][0].update(statut="failed"),
            lambda p: p["compte"]["transactions"][0].update(date="2026-10-01"),
            lambda p: p["compte"]["transactions"][0].update(solde_apres=1),
            lambda p: p["compte"]["transactions"][1].update(transaction_id="SYN-TEST-1"),
            lambda p: p["compte"]["transactions"][2].update(transaction_origine_id="not-present"),
        ]
        for mutation in mutations:
            malformed = customer()
            mutation(malformed)
            with self.subTest(mutation=mutation), self.assertRaises((ValueError, ValidationError)):
                self.repository.seed([malformed], PRODUCTS)
            self.assertEqual(self.repository.counts(), {"clients": 0, "accounts": 0, "transactions": 0, "products": 0})
            self.assertFalse(self.repository.is_seeded())

    def test_sql_failure_rolls_back_customers_accounts_transactions_and_marker(self):
        def fail_products(_connection, _cursor, statement, _parameters, _context, _executemany):
            if statement.startswith("INSERT INTO bank_products"):
                raise RuntimeError("Simulated storage failure")
        event.listen(self.repository.engine, "before_cursor_execute", fail_products)
        try:
            with self.assertRaisesRegex(RuntimeError, "Simulated storage failure"):
                self.repository.seed([customer()], PRODUCTS)
        finally:
            event.remove(self.repository.engine, "before_cursor_execute", fail_products)
        self.assertEqual(self.repository.counts(), {"clients": 0, "accounts": 0, "transactions": 0, "products": 0})
        self.assertFalse(self.repository.is_seeded())
        self.assertTrue(self.repository.seed([customer()], PRODUCTS))

    def test_restart_reuses_persisted_population_without_generating(self):
        path = Path(self.temp.name) / "clients.json"
        products = Path(self.temp.name) / "products.json"
        path.write_text(json.dumps([customer()]))
        products.write_text(json.dumps(PRODUCTS))
        original = BankData(data_path=str(path), products_path=str(products), repository=self.repository)
        expected = original.list_clients()
        self.assertEqual(len(original.clients), 2)
        self.repository.close()
        self.repository = BankRepository(self.database_url)
        with patch("app.banking.importlib.util.spec_from_file_location", side_effect=AssertionError("Generator must not run")):
            restarted = BankData(products_path=str(products), repository=self.repository)
        self.assertEqual(restarted.list_clients(), expected)
        self.assertEqual(restarted.get("SYN-TEST"), original.get("SYN-TEST"))
        self.assertIn("SYN-SPARSE", restarted.clients)
        self.assertNotIn("missing", restarted.clients)
        self.assertEqual(set(restarted.benchmark_clients(2)), {"SYN-TEST", "SYN-SPARSE"})

    def test_changed_import_does_not_replace_existing_evidence(self):
        self.repository.seed([customer()], PRODUCTS)
        changed = customer(name="Different identity")
        with self.assertRaisesRegex(ValueError, "different synthetic dataset"):
            self.repository.seed([changed], PRODUCTS)
        self.assertEqual(self.repository.get_client("SYN-TEST")["prenom"], "Jules_One")
        malformed = deepcopy(customer())
        malformed["compte"]["solde_final"] = 0
        with self.assertRaises(ValueError):
            self.repository.seed([malformed], PRODUCTS)
        self.assertEqual(self.repository.counts()["transactions"], 3)

    def test_sql_search_and_transaction_pagination_preserve_total_and_order(self):
        self.repository.seed([customer(), customer("SYN-SECOND", "Another customer")], PRODUCTS)
        result = self.repository.list_clients("bruss", limit=1, offset=1)
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["items"][0]["id"], "SYN-SECOND")
        self.assertEqual(self.repository.list_clients("belgium")["total"], 2)
        self.assertEqual(self.repository.list_clients("_")["total"], 1)
        result = self.repository.list_transactions("SYN-TEST", limit=1, offset=1)
        self.assertEqual(result["total"], 3)
        self.assertEqual(result["items"][0]["transaction_id"], "SYN-TEST-2")
        self.assertEqual(result["items"][0]["montant"], 3.59)
        with self.assertRaises(KeyError):
            self.repository.list_transactions("missing")
        for limit, offset in ((0, 0), (1001, 0), (1, -1), (True, 0)):
            with self.assertRaises(ValueError):
                self.repository.list_clients(limit=limit, offset=offset)

    def test_duplicate_global_ids_and_foreign_key_constraints(self):
        second = customer("SYN-SECOND")
        second["compte"]["transactions"][0]["transaction_id"] = "SYN-TEST-1"
        with self.assertRaisesRegex(ValueError, "Duplicate synthetic transaction"):
            self.repository.seed([customer(), second], PRODUCTS)
        self.assertFalse(self.repository.is_seeded())
        self.repository.seed([customer()], PRODUCTS)
        with self.repository.engine.connect() as connection:
            with self.assertRaises(IntegrityError):
                connection.execute(insert(Account), {
                    "id": "orphan", "client_id": "missing", "account_type": "test", "currency": "EUR",
                    "observation_start": date(2026, 7, 1),
                    "observation_end": date(2026, 9, 30),
                    "initial_balance_cents": 0, "balance_cents": 0,
                    "total_credit_cents": 0, "total_debit_cents": 0, "transaction_count": 0,
                })


if __name__ == "__main__":
    unittest.main()
