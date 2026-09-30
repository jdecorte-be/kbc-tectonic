from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class TodoBase(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False

class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    completed: Optional[bool] = False

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

class TodoResponse(TodoBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class HealthCheckResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime
