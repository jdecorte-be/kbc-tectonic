from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal

from app.config import settings
from app.database import engine, Base, get_db
from app import models, schemas, crud, seed, jev, profiles

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

with SessionLocal() as _db:
    seed.seed_demo_clients(_db)

def _meta(db: Session, key: str):
    row = db.get(models.DashboardMeta, key)
    return row.payload if row else None

def _clients(db: Session) -> list[dict]:
    return [r.payload for r in db.query(models.ClientRecord).order_by(models.ClientRecord.id).all()]

@app.get("/api/profiles", response_model=List[schemas.ProfileDef], tags=["Clients"])
def list_profiles():
    """Profile catalogue: label, core segment flag and the offer to make."""
    return profiles.profile_list()

@app.get("/api/clients", response_model=List[schemas.Client], tags=["Clients"])
def list_clients(db: Session = Depends(get_db)):
    return _clients(db)

@app.get("/api/clients/{client_id}", response_model=schemas.Client, tags=["Clients"])
def get_client(client_id: str, db: Session = Depends(get_db)):
    row = db.get(models.ClientRecord, client_id)
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    return row.payload

@app.get("/api/relations", response_model=Dict[str, List[schemas.Relation]], tags=["Clients"])
def list_relations(limit: int = 4, db: Session = Depends(get_db)):
    """Related clients per client id: explicit links first, then similar clients."""
    clients, links = _clients(db), _meta(db, "links") or []
    return {c["id"]: profiles.related_clients(c, clients, links, limit) for c in clients}

@app.get("/api/dashboard", response_model=schemas.Dashboard, tags=["Clients"])
def dashboard(db: Session = Depends(get_db)):
    return {k: _meta(db, k) for k in ("kpis", "segments", "habitTrends", "weekdayRhythm", "links", "jevUsage")}

@app.get("/api/health", response_model=schemas.HealthCheckResponse, tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc)
    }

@app.post("/api/seed", tags=["Database"])
def trigger_seed(force: bool = False, db: Session = Depends(get_db)):
    return {**seed.seed_database(db, force=force), "demo": seed.seed_demo_clients(db, force=force)}

@app.get("/api/users", response_model=List[schemas.UserResponse], tags=["Users"])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_users(db, skip=skip, limit=limit)

@app.get("/api/users/{user_id}", response_model=schemas.UserDetailResponse, tags=["Users"])
def get_user_detail(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/api/users", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if user.email and crud.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="User with this email already exists")
    return crud.create_user(db, user)

@app.put("/api/users/{user_id}", response_model=schemas.UserResponse, tags=["Users"])
@app.patch("/api/users/{user_id}", response_model=schemas.UserResponse, tags=["Users"])
def update_user(user_id: int, user_update: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = crud.update_user(db, user_id, user_update)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.get("/api/transactions", response_model=List[schemas.TransactionResponse], tags=["Transactions"])
def list_transactions(user_id: Optional[int] = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_transactions(db, user_id=user_id, skip=skip, limit=limit)

@app.post("/api/transactions", response_model=schemas.TransactionResponse, status_code=status.HTTP_201_CREATED, tags=["Transactions"])
def create_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    user = crud.get_user_by_id(db, transaction.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.create_transaction(db, transaction)

@app.post("/api/jev/analyze/{user_id}", tags=["Jev AI"])
def jev_analyze_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = jev.analyze_user(user)
    jev.record_usage(db, [result])
    return result

@app.post("/api/jev/analyze", tags=["Jev AI"])
def jev_analyze_all(db: Session = Depends(get_db)):
    """Run Jev over the transactions of every profile."""
    results = jev.analyze_users(crud.get_users(db, limit=10_000))
    return {"results": results, "usage": jev.record_usage(db, results)}

@app.get("/api/jev/clients", response_model=Optional[schemas.JevTrackers], tags=["Jev AI"])
def jev_client_trackers(db: Session = Depends(get_db)):
    """Cached Jev trackers for the dashboard clients (null until POSTed once)."""
    return _meta(db, "jev")

@app.post("/api/jev/clients", response_model=schemas.JevTrackers, tags=["Jev AI"])
def jev_score_clients(db: Session = Depends(get_db)):
    """Run Jev over every dashboard client and cache the trackers."""
    clients = _clients(db)
    payload = {"analyzedAt": datetime.now(timezone.utc).isoformat(), "clients": jev.analyze_clients(clients)}
    db.merge(models.DashboardMeta(key="jev", payload=payload))
    db.commit()
    return payload

@app.get("/api/openapi.md", response_class=PlainTextResponse, tags=["Documentation"])
def get_openapi_markdown():
    try:
        with open("OPENAPI.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "# REST API OpenAPI Specification\nDocumentation available at /OPENAPI.md"
