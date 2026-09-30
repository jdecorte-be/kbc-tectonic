from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import User, Transaction
from app.schemas import UserCreate, UserUpdate, TransactionCreate

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate) -> User:
    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None

    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user

def get_transactions(db: Session, user_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[Transaction]:
    query = db.query(Transaction)
    if user_id is not None:
        query = query.filter(Transaction.user_id == user_id)
    return query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()

def create_transaction(db: Session, transaction: TransactionCreate) -> Transaction:
    db_transaction = Transaction(**transaction.model_dump())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction
