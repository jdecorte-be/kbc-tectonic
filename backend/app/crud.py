from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Todo
from app.schemas import TodoCreate, TodoUpdate

def get_todos(db: Session, completed: Optional[bool] = None, skip: int = 0, limit: int = 100) -> List[Todo]:
    query = db.query(Todo)
    if completed is not None:
        query = query.filter(Todo.completed == completed)
    return query.order_by(Todo.created_at.desc()).offset(skip).limit(limit).all()

def get_todo_by_id(db: Session, todo_id: int) -> Optional[Todo]:
    return db.query(Todo).filter(Todo.id == todo_id).first()

def create_todo(db: Session, todo: TodoCreate) -> Todo:
    db_todo = Todo(
        title=todo.title,
        description=todo.description,
        completed=todo.completed or False
    )
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

def update_todo(db: Session, todo_id: int, todo_update: TodoUpdate) -> Optional[Todo]:
    db_todo = get_todo_by_id(db, todo_id)
    if not db_todo:
        return None

    update_data = todo_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_todo, key, value)

    db.commit()
    db.refresh(db_todo)
    return db_todo

def delete_todo(db: Session, todo_id: int) -> bool:
    db_todo = get_todo_by_id(db, todo_id)
    if not db_todo:
        return False
    db.delete(db_todo)
    db.commit()
    return True
