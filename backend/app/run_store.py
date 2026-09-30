"""Durable analysis and benchmark history on the application's SQLAlchemy engine."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, ForeignKey, Integer, String, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class RunBase(DeclarativeBase):
    """Independent metadata so bank models and run history can evolve separately."""


class AnalysisRun(RunBase):
    __tablename__ = "analysis_runs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    client_id: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[str] = mapped_column(String(40), index=True)
    result: Mapped[dict] = mapped_column(JSON)


class BenchmarkRun(RunBase):
    __tablename__ = "benchmark_runs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    status: Mapped[str] = mapped_column(String(40), index=True)
    created_at: Mapped[str] = mapped_column(String(40), index=True)
    updated_at: Mapped[str] = mapped_column(String(40))
    snapshot: Mapped[dict] = mapped_column(JSON)


class BenchmarkResult(RunBase):
    __tablename__ = "benchmark_results"

    benchmark_id: Mapped[str] = mapped_column(ForeignKey("benchmark_runs.id"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    result: Mapped[dict] = mapped_column(JSON)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pagination(limit: int, offset: int) -> None:
    if limit < 0 or offset < 0:
        raise ValueError("Pagination limit and offset must be non-negative.")


class RunStore:
    def __init__(self, engine: Engine):
        self.engine = engine
        RunBase.metadata.create_all(engine)

    def save_analysis(self, result: dict) -> str:
        identifier = uuid4().hex
        with Session(self.engine) as session, session.begin():
            session.add(AnalysisRun(id=identifier, client_id=result["client"]["id"],
                                    status=result["status"], created_at=_now(), result=result))
        return identifier

    def get_analysis(self, identifier: str) -> dict:
        with Session(self.engine) as session:
            run = session.get(AnalysisRun, identifier)
            if run is None:
                raise KeyError(identifier)
            return {**run.result, "analysis_id": run.id, "created_at": run.created_at}

    def list_analyses(self, client_id: str | None = None, limit: int = 50, offset: int = 0) -> dict:
        _pagination(limit, offset)
        query = select(AnalysisRun)
        count = select(func.count()).select_from(AnalysisRun)
        if client_id is not None:
            query = query.where(AnalysisRun.client_id == client_id)
            count = count.where(AnalysisRun.client_id == client_id)
        with Session(self.engine) as session:
            total = session.scalar(count)
            rows = session.scalars(query.order_by(AnalysisRun.created_at.desc(), AnalysisRun.id.desc()).limit(limit).offset(offset))
            items = []
            for run in rows:
                result = run.result
                metrics = result["metrics"]
                items.append({"id": run.id, "client_id": run.client_id, "client": result["client"],
                              "status": run.status, "created_at": run.created_at,
                              "duration_ms": metrics["duration_ms"], "estimated_cost_usd": metrics["estimated_cost_usd"],
                              "summary": result.get("summary", ""), "category": result.get("category"),
                              "ad_count": len(result.get("ads", []))})
            return {"items": items, "total": total}

    def save_benchmark(self, snapshot: dict, *, results_offset: int = 0) -> None:
        """Update metadata and insert new results atomically without rewriting old JSON.

        The default accepts a complete snapshot. BenchmarkManager supplies only the
        latest result and its absolute offset, keeping each checkpoint small.
        """
        _pagination(len(snapshot.get("results", [])), results_offset)
        identifier = snapshot["id"]
        results = snapshot.get("results", [])
        metadata = {key: value for key, value in snapshot.items() if key not in {"results", "created_at", "updated_at"}}
        now = _now()
        with Session(self.engine) as session, session.begin():
            run = session.get(BenchmarkRun, identifier)
            if run is None:
                run = BenchmarkRun(id=identifier, status=snapshot["status"], created_at=now,
                                   updated_at=now, snapshot=metadata)
                session.add(run)
                session.flush()
            else:
                run.status = snapshot["status"]
                run.updated_at = now
                run.snapshot = metadata
            if results:
                existing = set(session.scalars(select(BenchmarkResult.position).where(
                    BenchmarkResult.benchmark_id == identifier,
                    BenchmarkResult.position >= results_offset,
                    BenchmarkResult.position < results_offset + len(results),
                )))
                for position, result in enumerate(results, start=results_offset):
                    if position not in existing:
                        session.add(BenchmarkResult(benchmark_id=identifier, position=position, result=result))

    def get_benchmark(self, identifier: str, results_limit: int = 1000, results_offset: int = 0) -> dict:
        _pagination(results_limit, results_offset)
        with Session(self.engine) as session:
            run = session.get(BenchmarkRun, identifier)
            if run is None:
                raise KeyError(identifier)
            results = session.scalars(select(BenchmarkResult.result).where(
                BenchmarkResult.benchmark_id == identifier,
            ).order_by(BenchmarkResult.position).limit(results_limit).offset(results_offset)).all()
            return {**run.snapshot, "results": list(results), "created_at": run.created_at, "updated_at": run.updated_at}

    def list_benchmarks(self, limit: int = 50, offset: int = 0) -> dict:
        _pagination(limit, offset)
        with Session(self.engine) as session:
            total = session.scalar(select(func.count()).select_from(BenchmarkRun))
            rows = session.scalars(select(BenchmarkRun).order_by(
                BenchmarkRun.created_at.desc(), BenchmarkRun.id.desc(),
            ).limit(limit).offset(offset))
            items = [{**run.snapshot, "created_at": run.created_at, "updated_at": run.updated_at} for run in rows]
            return {"items": items, "total": total}

    def recover_interrupted(self) -> int:
        """Mark unfinished jobs failed; never repeat provider requests on startup."""
        with Session(self.engine) as session, session.begin():
            runs = session.scalars(select(BenchmarkRun).where(BenchmarkRun.status == "running")).all()
            for run in runs:
                run.status = "failed"
                run.updated_at = _now()
                run.snapshot = {**run.snapshot, "status": "failed", "cancel_requested": True,
                                "error": "Server restart interrupted this benchmark. Completed results and recorded costs are preserved; in-flight provider usage may be unavailable."}
            return len(runs)
