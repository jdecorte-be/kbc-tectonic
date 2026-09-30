import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from sqlalchemy import create_engine

from app.benchmark import BenchmarkManager, aggregate_metrics
from app.run_store import RunStore


def analysis(client_id="client-1"):
    return {"client": {"id": client_id, "name": "Synthetic client"}, "status": "recommended",
            "summary": "An observed habit", "category": {"label": "Worker"},
            "facts": {"currency": "EUR", "full_evidence": ["transaction-1", "transaction-2"]},
            "ads": [{"product_id": "product-1", "reason": "Observed recurring transfers"}],
            "metrics": {"duration_ms": 12, "api_calls": 2, "input_tokens": 100,
                        "output_tokens": 20, "estimated_cost_usd": .001, "usage_source": "provider"}}


def snapshot(identifier="benchmark-1", results=None, status="running", elapsed=20):
    results = results if results is not None else [analysis()]
    return {"id": identifier, "status": status, "requested_count": 10, "completed_count": len(results),
            "concurrency": 2, "elapsed_ms": elapsed, "results": results,
            "metrics": aggregate_metrics(results, elapsed), "error": None, "cancel_requested": False,
            "category_registry_before": {"count": 1, "labels": ["Worker"]},
            "category_registry_after": {"count": 1, "labels": ["Worker"]}}


class RunStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.url = f"sqlite:///{Path(self.temporary.name) / 'runs.db'}"
        self.engine = create_engine(self.url)
        self.store = RunStore(self.engine)

    def tearDown(self):
        self.engine.dispose()
        self.temporary.cleanup()

    def test_analysis_survives_reopen_with_full_evidence_and_filtered_history(self):
        original = analysis()
        first_id = self.store.save_analysis(original)
        self.store.save_analysis(analysis("client-2"))
        newest_id = self.store.save_analysis(analysis())
        self.engine.dispose()
        self.engine = create_engine(self.url)
        self.store = RunStore(self.engine)
        recovered = self.store.get_analysis(first_id)
        self.assertEqual(recovered["analysis_id"], first_id)
        self.assertTrue(recovered["created_at"].endswith("+00:00"))
        self.assertEqual({key: recovered[key] for key in original}, original)
        page = self.store.list_analyses("client-1", limit=1)
        self.assertEqual(page["total"], 2)
        self.assertEqual(page["items"][0]["id"], newest_id)
        self.assertEqual(page["items"][0]["duration_ms"], 12)
        self.assertEqual(page["items"][0]["estimated_cost_usd"], .001)
        self.assertEqual(self.store.list_analyses("client-1", limit=1, offset=1)["items"][0]["id"], first_id)
        self.assertEqual(self.store.list_analyses()["total"], 3)
        with self.assertRaises(KeyError):
            self.store.get_analysis("missing")

    def test_incremental_checkpoint_does_not_rewrite_existing_results(self):
        first = analysis("first")
        second = analysis("second")
        self.store.save_benchmark(snapshot(results=[first]))
        complete = snapshot(results=[first, second], status="completed", elapsed=35)
        # Existing rows must not be serialized again, even in a complete snapshot.
        complete["results"][0] = {"not_serializable": object()}
        self.store.save_benchmark(complete)
        recovered = self.store.get_benchmark("benchmark-1", results_limit=1, results_offset=1)
        self.assertEqual(recovered["results"], [second])
        self.assertEqual(recovered["completed_count"], 2)
        self.assertEqual(recovered["metrics"]["estimated_cost_usd"], .002)
        self.assertEqual(self.store.get_benchmark("benchmark-1")["results"][0], first)
        self.assertEqual(self.store.get_benchmark("benchmark-1", results_limit=0)["results"], [])
        history = self.store.list_benchmarks()
        self.assertEqual(history["total"], 1)
        self.assertNotIn("results", history["items"][0])
        self.assertEqual(history["items"][0]["status"], "completed")

    def test_recovery_preserves_partial_cost_and_does_not_recover_terminal_runs(self):
        running = snapshot(elapsed=123.45)
        self.store.save_benchmark(running)
        self.store.save_benchmark(snapshot(identifier="completed", status="completed"))
        self.engine.dispose()
        self.engine = create_engine(self.url)
        self.store = RunStore(self.engine)
        self.assertEqual(self.store.recover_interrupted(), 1)
        recovered = self.store.get_benchmark("benchmark-1")
        self.assertEqual(recovered["status"], "failed")
        self.assertIn("restart interrupted", recovered["error"])
        self.assertEqual(recovered["results"], running["results"])
        self.assertEqual(recovered["elapsed_ms"], running["elapsed_ms"])
        self.assertEqual(recovered["metrics"], running["metrics"])
        self.assertEqual(self.store.get_benchmark("completed")["status"], "completed")
        self.assertEqual(self.store.recover_interrupted(), 0)
        with self.assertRaises(KeyError):
            self.store.get_benchmark("missing")


class FakeWorkflow:
    def __init__(self, delay=0):
        self.data = SimpleNamespace(benchmark_clients=lambda count: [str(index) for index in range(count)])
        self.active = 0
        self.calls = []
        self.delay = delay

    async def analyse(self, identifier):
        self.calls.append(identifier)
        self.active += 1
        try:
            await asyncio.sleep(self.delay)
            return analysis(identifier)
        finally:
            self.active -= 1


class BenchmarkPersistenceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.engine = create_engine(f"sqlite:///{Path(self.temporary.name) / 'runs.db'}")
        self.store = RunStore(self.engine)

    def tearDown(self):
        self.engine.dispose()
        self.temporary.cleanup()

    async def test_jobs_survive_memory_eviction_and_new_manager_without_replaying(self):
        workflow = FakeWorkflow()
        manager = BenchmarkManager(workflow, max_retained_jobs=1, store=self.store)
        first = manager.start(3, 2)
        self.assertEqual(self.store.get_benchmark(first["id"])["status"], "running")
        await manager.tasks[first["id"]]
        self.assertNotIn("full_evidence", manager.snapshot(first["id"])["results"][0]["facts"])
        second = manager.start(2, 1)
        await manager.tasks[second["id"]]
        self.assertEqual(len(manager.jobs), 1)
        archived = manager.snapshot(first["id"], results_limit=1, results_offset=1)
        self.assertEqual(archived["status"], "completed")
        self.assertEqual(archived["completed_count"], 3)
        self.assertEqual(archived["results"][0]["facts"]["full_evidence"], ["transaction-1", "transaction-2"])
        restarted = BenchmarkManager(workflow, store=self.store)
        self.assertEqual(restarted.cancel(first["id"])["status"], "completed")
        self.assertEqual(restarted.snapshot(second["id"])["completed_count"], 2)
        self.assertEqual(len(workflow.calls), 5)
        await manager.close()

    async def test_cancel_persists_inflight_results_and_cost(self):
        workflow = FakeWorkflow(delay=.01)
        manager = BenchmarkManager(workflow, store=self.store)
        initial = manager.start(10, 2)
        task = manager.tasks[initial["id"]]
        while workflow.active < 2:
            await asyncio.sleep(0)
        manager.cancel(initial["id"])
        self.assertTrue(self.store.get_benchmark(initial["id"])["cancel_requested"])
        await task
        archived = self.store.get_benchmark(initial["id"])
        self.assertEqual(archived["status"], "cancelled")
        self.assertEqual(archived["completed_count"], 2)
        self.assertEqual(len(archived["results"]), 2)
        self.assertEqual(archived["metrics"]["api_calls"], 4)
        self.assertEqual(archived["metrics"]["estimated_cost_usd"], .002)

    async def test_failed_creation_makes_no_workflow_calls(self):
        workflow = FakeWorkflow()
        manager = BenchmarkManager(workflow, store=self.store)
        self.store.save_benchmark = lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("DB unavailable"))
        with self.assertRaises(RuntimeError):
            manager.start(10, 2)
        self.assertEqual(manager.jobs, {})
        self.assertEqual(manager.tasks, {})
        self.assertEqual(workflow.calls, [])

    async def test_failed_result_checkpoint_stops_work_and_retries_full_evidence(self):
        workflow = FakeWorkflow()
        manager = BenchmarkManager(workflow, store=self.store)
        save = self.store.save_benchmark
        calls = 0

        def fail_once(value, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("Temporary database failure")
            return save(value, **kwargs)

        self.store.save_benchmark = fail_once
        initial = manager.start(10, 2)
        with self.assertLogs("app.benchmark", level="ERROR"):
            await manager.tasks[initial["id"]]
        result = manager.snapshot(initial["id"])
        persisted = self.store.get_benchmark(initial["id"])
        self.assertEqual(result["status"], "failed")
        self.assertEqual(persisted["status"], "failed")
        self.assertEqual(len(workflow.calls), 2)
        self.assertEqual(len(persisted["results"]), 2)
        self.assertEqual(persisted["completed_count"], 2)
        self.assertEqual(persisted["results"][0]["facts"]["full_evidence"], ["transaction-1", "transaction-2"])
        self.assertEqual(persisted["metrics"], result["metrics"])

    async def test_final_checkpoint_failure_is_not_reported_as_success(self):
        workflow = FakeWorkflow()
        manager = BenchmarkManager(workflow, store=self.store)
        save = self.store.save_benchmark

        def fail_completion(value, **kwargs):
            if value["status"] == "completed":
                raise RuntimeError("Database write failed")
            return save(value, **kwargs)

        self.store.save_benchmark = fail_completion
        initial = manager.start(2, 1)
        with self.assertLogs("app.benchmark", level="ERROR"):
            await manager.tasks[initial["id"]]
        self.assertEqual(manager.snapshot(initial["id"])["status"], "failed")
        self.assertEqual(self.store.get_benchmark(initial["id"])["status"], "failed")
