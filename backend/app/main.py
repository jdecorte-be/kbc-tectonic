"""FastAPI application with durable data, bounded jobs and explicit lifecycle."""
import asyncio
from contextlib import asynccontextmanager
import logging
import sqlite3

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.config import Settings, settings
from app.banking import BankData, client_summary
from app.benchmark import BenchmarkBusy, BenchmarkManager
from app.categories import CategoryRegistry, CategoryService
from app.crud import BankRepository
from app.jev import JevClient
from app.run_store import RunStore
from app.schemas import (
    AnalysisRequest, AnalysisResponse, BenchmarkRequest, BenchmarkResponse,
    ClientDetail, ClientPage, HistoryPage, ProductPage, TransactionPage,
)
from app.workflow import Workflow

logger = logging.getLogger(__name__)


def create_app(config: Settings | None = None) -> FastAPI:
    config = config or settings

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        repository = jev = categories = registry = benchmarks = None
        try:
            repository = BankRepository(config.DATABASE_URL)
            data = await asyncio.to_thread(
                BankData, data_path=config.BANK_DATA_PATH, products_path=config.PRODUCTS_PATH,
                generated_count=config.GENERATED_CLIENT_COUNT, repository=repository,
            )
            store = RunStore(repository.engine)
            await asyncio.to_thread(store.recover_interrupted)
            jev = JevClient()
            registry = CategoryRegistry(config.CATEGORY_DB_PATH or None)
            categories = CategoryService(jev, registry=registry)
            workflow = Workflow(data, jev, max_api_concurrency=10, category_service=categories)
            benchmarks = BenchmarkManager(workflow, store=store)
            application.state.data = data
            application.state.repository = repository
            application.state.store = store
            application.state.jev = jev
            application.state.workflow = workflow
            application.state.benchmarks = benchmarks
            yield
        finally:
            if benchmarks is not None:
                await benchmarks.close()
            if categories is not None:
                await categories.close()
            if registry is not None:
                registry.close()
            if jev is not None:
                await jev.close()
            if repository is not None:
                repository.close()

    application = FastAPI(title=config.PROJECT_NAME, openapi_url="/api/openapi.json",
                          docs_url="/api/docs", lifespan=lifespan)
    application.add_middleware(CORSMiddleware, allow_origins=config.cors_origins_list,
                              allow_credentials=True, allow_methods=["GET", "POST", "DELETE"],
                              allow_headers=["Content-Type"])

    @application.exception_handler(SQLAlchemyError)
    @application.exception_handler(sqlite3.Error)
    async def database_error(_request: Request, exc: Exception):
        logger.error("Database operation failed: %s", type(exc).__name__)
        return JSONResponse(status_code=503, content={"detail": "The database is temporarily unavailable. Please try again."})

    def require_client(client_id: str) -> None:
        if client_id not in application.state.data.clients:
            raise HTTPException(status_code=404, detail="Synthetic client not found.")

    @application.get("/api/health", tags=["Health"])
    def health_check():
        if not application.state.repository.check_health():
            raise HTTPException(status_code=503, detail="The database is unavailable.")
        pricing = application.state.jev.pricing_info
        service = application.state.workflow.category_service
        snapshot = service.registry.snapshot()
        return {"status": "ok", "database": "connected", "storage": application.state.repository.engine.dialect.name,
                "jev_configured": application.state.jev.configured, "model": application.state.jev.model,
                "client_count": len(application.state.data.clients), "product_count": len(application.state.data.products),
                "category_count": len(snapshot["items"]), "openai_configured": service.openai.configured,
                "openai_model": service.openai.model, "openai_pricing": service.openai.pricing_info,
                "pricing": {**pricing, "source": pricing.get("source_url", "Configured demo estimate")}}

    @application.get("/api/clients", response_model=ClientPage, tags=["Clients"])
    def list_clients(q: str = Query(default="", max_length=100), limit: int = Query(default=50, ge=1, le=1000),
                     offset: int = Query(default=0, ge=0)):
        return application.state.data.list_clients(q, limit, offset)

    @application.get("/api/clients/{client_id}", response_model=ClientDetail, tags=["Clients"])
    def get_client(client_id: str):
        require_client(client_id)
        client = application.state.data.get(client_id)
        return {"client": client_summary(client), "facts": application.state.data.facts(client_id),
                "transactions": client["compte"]["transactions"]}

    @application.get("/api/clients/{client_id}/transactions", response_model=TransactionPage, tags=["Clients"])
    def list_transactions(client_id: str, limit: int = Query(default=50, ge=1, le=1000), offset: int = Query(default=0, ge=0)):
        require_client(client_id)
        return application.state.data.list_transactions(client_id, limit, offset)

    @application.get("/api/products", response_model=ProductPage, tags=["Products"])
    def list_products():
        return {"items": application.state.data.products}

    @application.get("/api/categories", tags=["Categories"])
    def list_categories():
        return application.state.workflow.category_service.registry.snapshot()

    @application.post("/api/analyses", response_model=AnalysisResponse, tags=["Analyses"])
    async def analyse_client(payload: AnalysisRequest):
        require_client(payload.client_id)
        result = await application.state.workflow.analyse(payload.client_id)
        identifier = await asyncio.to_thread(application.state.store.save_analysis, result)
        return await asyncio.to_thread(application.state.store.get_analysis, identifier)

    @application.get("/api/analyses", response_model=HistoryPage, tags=["Analyses"])
    def list_analyses(client_id: str | None = Query(default=None, max_length=100),
                      limit: int = Query(default=10, ge=1, le=100), offset: int = Query(default=0, ge=0)):
        if client_id is not None:
            require_client(client_id)
        return application.state.store.list_analyses(client_id, limit, offset)

    @application.get("/api/analyses/{analysis_id}", response_model=AnalysisResponse, tags=["Analyses"])
    def get_analysis(analysis_id: str):
        try:
            return application.state.store.get_analysis(analysis_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Analysis not found.") from None

    @application.post("/api/benchmarks", status_code=202, response_model=BenchmarkResponse, tags=["Benchmarks"])
    async def create_benchmark(payload: BenchmarkRequest):
        try:
            return application.state.benchmarks.start(payload.count, payload.concurrency)
        except BenchmarkBusy as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from None
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None

    @application.get("/api/benchmarks", response_model=HistoryPage, tags=["Benchmarks"])
    def list_benchmarks(limit: int = Query(default=10, ge=1, le=100), offset: int = Query(default=0, ge=0)):
        return application.state.store.list_benchmarks(limit, offset)

    @application.get("/api/benchmarks/{benchmark_id}", response_model=BenchmarkResponse, tags=["Benchmarks"])
    async def get_benchmark(benchmark_id: str, results_limit: int = Query(default=1000, ge=0, le=1000),
                            results_offset: int = Query(default=0, ge=0)):
        try:
            return application.state.benchmarks.snapshot(benchmark_id, results_limit, results_offset)
        except KeyError:
            raise HTTPException(status_code=404, detail="Benchmark not found.") from None

    @application.delete("/api/benchmarks/{benchmark_id}", response_model=BenchmarkResponse, tags=["Benchmarks"])
    async def cancel_benchmark(benchmark_id: str):
        try:
            return application.state.benchmarks.cancel(benchmark_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Benchmark not found.") from None

    return application


app = create_app()
