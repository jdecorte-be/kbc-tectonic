"""Real, bounded asynchronous benchmark jobs; no result cache or extrapolation."""

import asyncio
from collections import OrderedDict
import math
import time
from uuid import uuid4

from app.workflow import Workflow


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
    def __init__(self, workflow: Workflow, max_retained_jobs: int = 5):
        self.workflow = workflow
        self.jobs: OrderedDict[str, dict] = OrderedDict()
        self.tasks: dict[str, asyncio.Task] = {}
        self.max_retained_jobs = max_retained_jobs

    def _registry_snapshot(self) -> dict:
        service = getattr(self.workflow, "category_service", None)
        if service is None:
            return {"count": 0, "labels": []}
        items = service.registry.snapshot()["items"]
        return {"count": len(items), "labels": [item["label"] for item in items]}

    def start(self, count: int, concurrency: int) -> dict:
        if any(job["status"] == "running" for job in self.jobs.values()):
            raise BenchmarkBusy("A benchmark is already running. Wait for it to finish or cancel it.")
        clients = self.workflow.data.benchmark_clients(count)
        while len(self.jobs) >= self.max_retained_jobs:
            self.jobs.popitem(last=False)
        identifier = uuid4().hex
        self.jobs[identifier] = {"id": identifier, "status": "running", "requested_count": count, "concurrency": concurrency,
                                 "results": [], "error": None, "cancel_requested": False, "_started": time.perf_counter(), "_elapsed_ms": None,
                                 "category_registry_before": self._registry_snapshot(), "category_registry_after": None}
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
                finally:
                    queue.task_done()

        try:
            outcomes = await asyncio.gather(*(worker() for _ in range(min(concurrency, len(clients)))), return_exceptions=True)
            if any(isinstance(outcome, BaseException) for outcome in outcomes):
                job["status"] = "failed"
                job["error"] = "A worker failed. All remaining active workers finished before final metrics were recorded."
            else:
                job["status"] = "cancelled" if job["cancel_requested"] else "completed"
        except asyncio.CancelledError:
            job["status"] = "cancelled"
            job["error"] = "Server shutdown interrupted this run; in-flight provider usage may be unavailable."
            raise
        except Exception:
            job["status"] = "failed"
            job["error"] = "The benchmark stopped because of an unexpected processing error."
        finally:
            job["_elapsed_ms"] = (time.perf_counter() - job["_started"]) * 1000
            job["category_registry_after"] = self._registry_snapshot()
            self.tasks.pop(identifier, None)

    def snapshot(self, identifier: str, results_limit: int = 1000, results_offset: int = 0) -> dict:
        job = self.jobs[identifier]
        elapsed = job["_elapsed_ms"] if job["_elapsed_ms"] is not None else (time.perf_counter() - job["_started"]) * 1000
        return {"id": identifier, "status": job["status"], "requested_count": job["requested_count"],
                "completed_count": len(job["results"]), "concurrency": job["concurrency"],
                "elapsed_ms": round(elapsed, 2), "results": job["results"][results_offset:results_offset + results_limit],
                "metrics": aggregate_metrics(job["results"], elapsed), "error": job["error"], "cancel_requested": job["cancel_requested"],
                "category_registry_before": job["category_registry_before"],
                "category_registry_after": job["category_registry_after"] or self._registry_snapshot()}

    def cancel(self, identifier: str) -> dict:
        job = self.jobs[identifier]
        if job["status"] == "running":
            # Finish current requests to retain their measured latency and cost.
            job["cancel_requested"] = True
        return self.snapshot(identifier)

    async def close(self) -> None:
        for job in self.jobs.values():
            if job["status"] == "running":
                job["cancel_requested"] = True
        pending = list(self.tasks.values())
        if pending:
            try:
                await asyncio.wait_for(asyncio.gather(*pending, return_exceptions=True), timeout=30)
            except asyncio.TimeoutError:
                pass
