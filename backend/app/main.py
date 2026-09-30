"""FastAPI entrypoint for the synthetic KBC targeting demo."""
from contextlib import asynccontextmanager
import os
from typing import Literal
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from app.config import settings
from app.banking import BankData, client_summary
from app.benchmark import BenchmarkBusy, BenchmarkManager
from app.jev import JevClient
from app.workflow import Workflow


@asynccontextmanager
async def lifespan(application: FastAPI):
    data = BankData(data_path=os.getenv("BANK_DATA_PATH", ""), products_path=os.getenv("PRODUCTS_PATH", ""))
    jev = JevClient()
    workflow = Workflow(data, jev, max_api_concurrency=10)
    benchmarks = BenchmarkManager(workflow)
    application.state.data = data
    application.state.jev = jev
    application.state.workflow = workflow
    application.state.benchmarks = benchmarks
    try:
        yield
    finally:
        await benchmarks.close()
        if workflow.category_service is not None:
            await workflow.category_service.close()
        await jev.close()


app = FastAPI(title="KBC Synthetic Customer Intelligence", openapi_url="/api/openapi.json", docs_url="/api/docs", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins_list,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


class AnalysisRequest(BaseModel):
    client_id: str = Field(min_length=1, max_length=100)


class BenchmarkRequest(BaseModel):
    count: Literal[10, 100, 1000] = 10
    concurrency: int = Field(default=5, ge=1, le=10, strict=True)


def require_client(client_id: str) -> None:
    if client_id not in app.state.data.clients:
        raise HTTPException(status_code=404, detail="Synthetic client not found.")


@app.get("/api/health")
async def health_check():
    pricing = app.state.jev.pricing_info
    category_service = app.state.workflow.category_service
    snapshot = category_service.registry.snapshot()
    return {"status": "ok", "jev_configured": app.state.jev.configured,
            "model": app.state.jev.model, "client_count": len(app.state.data.clients),
            "product_count": len(app.state.data.products), "category_count": len(snapshot["items"]),
            "openai_configured": category_service.openai.configured,
            "openai_model": category_service.openai.model,
            "openai_pricing": category_service.openai.pricing_info,
            "pricing": {**pricing, "source": pricing.get("source_url", "Configured demo estimate")}}


@app.get("/api/clients")
async def list_clients(q: str = Query(default="", max_length=100), limit: int = Query(default=50, ge=1, le=1000), offset: int = Query(default=0, ge=0)):
    return app.state.data.list_clients(q, limit, offset)


@app.get("/api/clients/{client_id}")
async def get_client(client_id: str):
    require_client(client_id)
    client = app.state.data.get(client_id)
    return {"client": client_summary(client), "facts": app.state.data.facts(client_id), "transactions": client["compte"]["transactions"]}


@app.get("/api/products")
async def list_products():
    return {"items": app.state.data.products}


@app.get("/api/categories")
async def list_categories():
    return app.state.workflow.category_service.registry.snapshot()


@app.post("/api/analyses")
async def analyse_client(payload: AnalysisRequest):
    require_client(payload.client_id)
    return await app.state.workflow.analyse(payload.client_id)


@app.post("/api/benchmarks", status_code=202)
async def create_benchmark(payload: BenchmarkRequest):
    try:
        return app.state.benchmarks.start(payload.count, payload.concurrency)
    except BenchmarkBusy as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None


@app.get("/api/benchmarks/{benchmark_id}")
async def get_benchmark(benchmark_id: str, results_limit: int = Query(default=1000, ge=0, le=1000), results_offset: int = Query(default=0, ge=0)):
    try:
        return app.state.benchmarks.snapshot(benchmark_id, results_limit, results_offset)
    except KeyError:
        raise HTTPException(status_code=404, detail="Benchmark not found or no longer retained.") from None


@app.delete("/api/benchmarks/{benchmark_id}")
async def cancel_benchmark(benchmark_id: str):
    try:
        return app.state.benchmarks.cancel(benchmark_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Benchmark not found or no longer retained.") from None
