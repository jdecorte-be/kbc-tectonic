"""Real, bounded asynchronous benchmark jobs; no result cache or extrapolation."""

import asyncio
from collections import OrderedDict
import math
import logging
import time
from uuid import uuid4

from app.workflow import Workflow
from app.run_store import RunStore


logger = logging.getLogger(__name__)


def aggregate_metrics(results: list[dict], elapsed_ms: float) -> dict:
    latencies = sorted(result["metrics"]["duration_ms"] for result in results)
    count = len(results)

    def percentile(fraction: float) -> float:
        return latencies[max(0, math.ceil(count * fraction) - 1)] if count else 0.0

    sources = {result["metrics"]["usage_source"] for result in results}
    providers = {}
    for result in results:
        for name, values in result["metrics"].get("providers", {}).items():
            aggregate = providers.setdefault(name, {"api_calls": 0, "input_tokens": 0, "output_tokens": 0,
                                                     "estimated_cost_usd": 0.0, "duration_ms": 0.0,
                                                     "tokens_estimated": False, "usage_source": "none"})
            for key in ("api_calls", "input_tokens", "output_tokens", "estimated_cost_usd", "duration_ms"):
                aggregate[key] += values.get(key, 0)
            aggregate["tokens_estimated"] |= bool(values.get("tokens_estimated", False))
            aggregate["usage_source"] = "estimated" if aggregate["tokens_estimated"] else ("provider" if aggregate["api_calls"] else "none")
    return {
        "duration_ms": round(elapsed_ms, 2),
        **{key: sum(result["metrics"][key] for result in results) for key in ("api_calls", "input_tokens", "output_tokens")},
        "estimated_cost_usd": round(sum(result["metrics"]["estimated_cost_usd"] for result in results), 10),
        "clients_per_second": round(count / (elapsed_ms / 1000), 3) if elapsed_ms else 0.0,
        "average_latency_ms": round(sum(latencies) / count, 2) if count else 0.0,
        "p50_latency_ms": round(percentile(.50), 2), "p95_latency_ms": round(percentile(.95), 2),
        "recommended_count": sum(result["status"] == "recommended" for result in results),
        "abstained_count": sum(result["status"] in {"insufficient_information", "no_match"} for result in results),
        "opt_out_count": sum(result["status"] == "opt_out" for result in results),
        "error_count": sum(result["status"] == "error" for result in results),
        "openai_calls": sum(result["metrics"].get("openai_calls", 0) for result in results),
        "providers": providers,
        "usage_source": "estimated" if "estimated" in sources else "provider" if "provider" in sources else "none",
    }


class BenchmarkBusy(ValueError):
    pass


class BenchmarkManager:
    def __init__(self, workflow: Workflow, max_retained_jobs: int = 5, store: RunStore | None = None):
        self.workflow = workflow
        self.jobs: OrderedDict[str, dict] = OrderedDict()
        self.tasks: dict[str, asyncio.Task] = {}
        self.max_retained_jobs = max_retained_jobs
        self.store = store

    def _checkpoint(self, identifier: str, results: list[dict] | None = None, results_offset: int = 0) -> None:
        if self.store is not None:
            pending = self.jobs[identifier]["_unsaved_results"]
            if results:
                pending.extend(enumerate(results, start=results_offset))
            snapshot = self.snapshot(identifier, results_limit=0)
            snapshot["results"] = [result for _, result in pending]
            self.store.save_benchmark(snapshot, results_offset=pending[0][0] if pending else 0)
            pending.clear()

    def _persistence_failed(self, job: dict) -> None:
        job["_persistence_failed"] = True
        job["cancel_requested"] = True
        job["status"] = "failed"
        job["error"] = "The benchmark stopped because its results could not be saved. Recorded provider costs remain included where available."
        logger.error("Could not persist benchmark %s", job["id"])

    def _registry_snapshot(self) -> dict:
        service = getattr(self.workflow, "category_service", None)
        if service is None:
            return {"count": 0, "labels": []}
        items = service.registry.snapshot()["items"]
        return {"count": len(items), "labels": [item["label"] for item in items]}

    def start(self, count: int, concurrency: int) -> dict:
        if self.tasks or any(job["status"] == "running" for job in self.jobs.values()):
            raise BenchmarkBusy("A benchmark is already running. Wait for it to finish or cancel it.")
        clients = self.workflow.data.benchmark_clients(count)
        while len(self.jobs) >= self.max_retained_jobs:
            self.jobs.popitem(last=False)
        identifier = uuid4().hex
        self.jobs[identifier] = {"id": identifier, "status": "running", "requested_count": count, "concurrency": concurrency,
                                 "results": [], "error": None, "cancel_requested": False, "_started": time.perf_counter(), "_elapsed_ms": None,
                                 "_persistence_failed": False, "_unsaved_results": [],
                                 "category_registry_before": self._registry_snapshot(), "category_registry_after": None}
        try:
            self._checkpoint(identifier)
        except Exception:
            self.jobs.pop(identifier)
            raise
        self.tasks[identifier] = asyncio.create_task(self._run(identifier, clients, concurrency))
        return self.snapshot(identifier)

    async def _run(self, identifier: str, clients: list[str], concurrency: int) -> None:
        job = self.jobs[identifier]
        queue = asyncio.Queue()
        for client_id in clients:
            queue.put_nowait(client_id)

        async def worker() -> None:
            while not job["cancel_requested"]:
                try:
                    client_id = queue.get_nowait()
                except asyncio.QueueEmpty:
                    return
                try:
                    result = await self.workflow.analyse(client_id)
                    compact = dict(result)
                    compact["facts"] = {key: result["facts"][key] for key in (
                        "currency", "observation_start", "observation_end", "transaction_count", "balance_cents", "monthly_cashflow", "existing_insurance",
                    ) if key in result["facts"]}
                    job["results"].append(compact)
                    try:
                        # Keep full evidence in SQL, compact evidence in bounded RAM.
                        self._checkpoint(identifier, [result], len(job["results"]) - 1)
                    except Exception:
                        self._persistence_failed(job)
                        raise
                finally:
                    queue.task_done()

        try:
            outcomes = await asyncio.gather(*(worker() for _ in range(min(concurrency, len(clients)))), return_exceptions=True)
            if any(isinstance(outcome, BaseException) for outcome in outcomes):
                job["status"] = "failed"
                if not job["_persistence_failed"]:
                    job["error"] = "A worker failed. All remaining active workers finished before final metrics were recorded."
            elif job["_persistence_failed"]:
                job["status"] = "failed"
            else:
                job["status"] = "cancelled" if job["cancel_requested"] else "completed"
        except asyncio.CancelledError:
            job["status"] = "failed"
            job["error"] = "Server shutdown interrupted this run; in-flight provider usage may be unavailable."
            raise
        except Exception:
            job["status"] = "failed"
            job["error"] = "The benchmark stopped because of an unexpected processing error."
        finally:
            job["_elapsed_ms"] = (time.perf_counter() - job["_started"]) * 1000
            job["category_registry_after"] = self._registry_snapshot()
            try:
                self._checkpoint(identifier)
            except Exception:
                self._persistence_failed(job)
                try:
                    self._checkpoint(identifier)
                except Exception:
                    # The last durable running checkpoint is recovered on startup.
                    pass
            self.tasks.pop(identifier, None)

    def snapshot(self, identifier: str, results_limit: int = 1000, results_offset: int = 0) -> dict:
        if identifier not in self.jobs and self.store is not None:
            return self.store.get_benchmark(identifier, results_limit=results_limit, results_offset=results_offset)
        job = self.jobs[identifier]
        elapsed = job["_elapsed_ms"] if job["_elapsed_ms"] is not None else (time.perf_counter() - job["_started"]) * 1000
        return {"id": identifier, "status": job["status"], "requested_count": job["requested_count"],
                "completed_count": len(job["results"]), "concurrency": job["concurrency"],
                "elapsed_ms": round(elapsed, 2), "results": job["results"][results_offset:results_offset + results_limit],
                "metrics": aggregate_metrics(job["results"], elapsed), "error": job["error"], "cancel_requested": job["cancel_requested"],
                "category_registry_before": job["category_registry_before"],
                "category_registry_after": job["category_registry_after"] or self._registry_snapshot()}

    def cancel(self, identifier: str) -> dict:
        if identifier not in self.jobs:
            return self.snapshot(identifier)
        job = self.jobs[identifier]
        if job["status"] == "running":
            # Finish current requests to retain their measured latency and cost.
            job["cancel_requested"] = True
            try:
                self._checkpoint(identifier)
            except Exception:
                self._persistence_failed(job)
        return self.snapshot(identifier)

    async def close(self) -> None:
        for job in self.jobs.values():
            if job["status"] == "running":
                self.cancel(job["id"])
        pending = list(self.tasks.values())
        if pending:
            try:
                await asyncio.wait_for(asyncio.gather(*pending, return_exceptions=True), timeout=30)
            except asyncio.TimeoutError:
                pass
