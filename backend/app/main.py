from datetime import datetime, timezone
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.config import settings
from app.database import engine, Base, get_db
from app import models, schemas, crud

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/api/todos", response_model=List[schemas.TodoResponse], tags=["Todos"])
def list_todos(
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    db: Session = Depends(get_db)
):
    return crud.get_todos(db, completed=completed)

@app.post("/api/todos", response_model=schemas.TodoResponse, status_code=status.HTTP_201_CREATED, tags=["Todos"])
def create_todo(todo: schemas.TodoCreate, db: Session = Depends(get_db)):
    if not todo.title.strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    return crud.create_todo(db, todo)

@app.get("/api/todos/{todo_id}", response_model=schemas.TodoResponse, tags=["Todos"])
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    db_todo = crud.get_todo_by_id(db, todo_id)
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return db_todo

@app.put("/api/todos/{todo_id}", response_model=schemas.TodoResponse, tags=["Todos"])
def update_todo(todo_id: int, todo_update: schemas.TodoUpdate, db: Session = Depends(get_db)):
    db_todo = crud.update_todo(db, todo_id, todo_update)
    if not db_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return db_todo

@app.delete("/api/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Todos"])
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    success = crud.delete_todo(db, todo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Todo not found")
    return None
