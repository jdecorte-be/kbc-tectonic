import contextlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.crud import BankRepository
from app.seed import main


class SeedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp.name) / "bank.sqlite3"
        self.database_url = f"sqlite:///{self.database_path}"
        self.environment = patch.dict(os.environ, {
            "DATABASE_URL": self.database_url, "PRODUCTS_PATH": "", "BANK_DATA_PATH": "",
        })
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temp.cleanup()

    def invoke(self, *arguments):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            status = main(list(arguments))
        return status, output.getvalue(), errors.getvalue()

    def test_first_run_generates_clients_transactions_catalogue_and_sparse_example(self):
        status, output, errors = self.invoke("--count", "3")
        self.assertEqual(status, 0)
        self.assertEqual(errors, "")
        self.assertIn("Seeded 4 clients", output)
        self.assertIn("No AI calls were made", output)
        repository = BankRepository(self.database_url)
        try:
            counts = repository.counts()
            self.assertEqual(counts["clients"], 4)
            self.assertEqual(counts["accounts"], 4)
            self.assertGreater(counts["transactions"], 3)
            self.assertEqual(counts["products"], 10)
            self.assertTrue(repository.has_client("SYN-SPARSE"))
        finally:
            repository.close()

    def test_repeated_run_and_default_reuse_existing_records_without_generating(self):
        self.assertEqual(self.invoke("--count", "2")[0], 0)
        repository = BankRepository(self.database_url)
        try:
            before = repository.get_client("CLIENT-SYN-000001")
            counts = repository.counts()
        finally:
            repository.close()
        with patch("app.seed.BankData", side_effect=AssertionError("Existing population must be reused")):
            for arguments in (("--count", "2"), ()):
                status, output, errors = self.invoke(*arguments)
                self.assertEqual(status, 0)
                self.assertIn("Reused 3 clients", output)
                self.assertEqual(errors, "")
        repository = BankRepository(self.database_url)
        try:
            self.assertEqual(repository.counts(), counts)
            self.assertEqual(repository.get_client("CLIENT-SYN-000001"), before)
        finally:
            repository.close()

    def test_explicit_count_mismatch_explains_fresh_database_and_preserves_population(self):
        self.assertEqual(self.invoke("--count", "2")[0], 0)
        with patch("app.seed.BankData", side_effect=AssertionError("Existing population must be reused")):
            status, output, errors = self.invoke("--count", "7")
        self.assertEqual(status, 2)
        self.assertIn("Reused 3 clients", output)
        self.assertIn("fresh DATABASE_URL", errors)
        repository = BankRepository(self.database_url)
        try:
            self.assertEqual(repository.counts()["clients"], 3)
        finally:
            repository.close()

    def test_invalid_counts_fail_before_creating_database(self):
        for value in ("0", "-1", "10001", "1.5", "invalid"):
            with self.subTest(value=value), self.assertRaises(SystemExit) as exception:
                self.invoke("--count", value)
            self.assertEqual(exception.exception.code, 2)
            self.assertFalse(self.database_path.exists())

    def test_connection_errors_are_sanitized(self):
        private_value = "invalid-scheme-containing-private-credentials"
        with patch.dict(os.environ, {"DATABASE_URL": private_value}):
            status, output, errors = self.invoke("--count", "2")
        self.assertEqual(status, 1)
        self.assertEqual(output, "")
        self.assertIn("Seeding failed", errors)
        self.assertNotIn(private_value, errors)
        self.assertNotIn("Traceback", errors)

    def test_storage_is_closed_when_generation_fails(self):
        repository = BankRepository(self.database_url)
        with patch("app.seed.BankRepository", return_value=repository), \
             patch.object(repository, "close", wraps=repository.close) as close, \
             patch("app.seed.BankData", side_effect=RuntimeError("private source contents")):
            status, output, errors = self.invoke("--count", "2")
        self.assertEqual(status, 1)
        self.assertTrue(close.called)
        self.assertNotIn("private source contents", errors)
        self.assertEqual(output, "")


if __name__ == "__main__":
    unittest.main()
