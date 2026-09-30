import sys
import logging
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal, engine, Base
from app.models import User, Transaction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SAMPLE_USERS = [
    {
        "name": "Jean Dupont",
        "phone_number": "+32 470 12 34 56",
        "email": "jean.dupont@example.com",
        "address": "Rue Royale 100",
        "city": "Brussels",
        "country": "Belgium",
        "is_active": True
    },
    {
        "name": "Sophie Martin",
        "phone_number": "+32 485 98 76 54",
        "email": "sophie.martin@example.com",
        "address": "Meir 42",
        "city": "Antwerp",
        "country": "Belgium",
        "is_active": True
    },
    {
        "name": "Lucas Janssens",
        "phone_number": "+32 496 11 22 33",
        "email": "lucas.janssens@example.com",
        "address": "Kortrijksesteenweg 201",
        "city": "Ghent",
        "country": "Belgium",
        "is_active": True
    },
    {
        "name": "Emma Peeters",
        "phone_number": "+32 478 55 66 77",
        "email": "emma.peeters@example.com",
        "address": "Place Saint-Lambert 15",
        "city": "Liège",
        "country": "Belgium",
        "is_active": True
    },
    {
        "name": "Marc Dubois",
        "phone_number": "+32 460 44 88 11",
        "email": "marc.dubois@example.com",
        "address": "Boulevard Tirou 88",
        "city": "Charleroi",
        "country": "Belgium",
        "is_active": False
    }
]

SAMPLE_TRANSACTIONS = [
    {"user_index": 0, "amount": Decimal("1250.00"), "currency": "EUR", "transaction_type": "deposit", "status": "completed", "description": "Monthly salary credit"},
    {"user_index": 0, "amount": Decimal("45.50"), "currency": "EUR", "transaction_type": "payment", "status": "completed", "description": "Grocery store purchase"},
    {"user_index": 0, "amount": Decimal("120.00"), "currency": "EUR", "transaction_type": "withdrawal", "status": "completed", "description": "ATM withdrawal Brussels Central"},

    {"user_index": 1, "amount": Decimal("3400.00"), "currency": "EUR", "transaction_type": "deposit", "status": "completed", "description": "Consulting invoice payment"},
    {"user_index": 1, "amount": Decimal("230.15"), "currency": "EUR", "transaction_type": "payment", "status": "completed", "description": "Online electronics store"},
    {"user_index": 1, "amount": Decimal("500.00"), "currency": "EUR", "transaction_type": "transfer", "status": "pending", "description": "Savings account transfer"},

    {"user_index": 2, "amount": Decimal("85.00"), "currency": "EUR", "transaction_type": "payment", "status": "completed", "description": "Restaurant dinner"},
    {"user_index": 2, "amount": Decimal("1500.00"), "currency": "EUR", "transaction_type": "deposit", "status": "completed", "description": "Freelance work payment"},

    {"user_index": 3, "amount": Decimal("2100.00"), "currency": "EUR", "transaction_type": "deposit", "status": "completed", "description": "Salary deposit"},
    {"user_index": 3, "amount": Decimal("12.99"), "currency": "EUR", "transaction_type": "payment", "status": "completed", "description": "Streaming service subscription"},

    {"user_index": 4, "amount": Decimal("50.00"), "currency": "EUR", "transaction_type": "payment", "status": "failed", "description": "Insufficient funds test"}
]

def seed_database(db: Session, force: bool = False) -> dict:
    Base.metadata.create_all(bind=engine)

    try:
        db.execute(text("DROP TABLE IF EXISTS todos CASCADE;"))
        db.commit()
    except Exception as e:
        logger.warning(f"Note dropping todos table: {e}")

    existing_users_count = db.query(User).count()
    if existing_users_count > 0 and not force:
        logger.info(f"Database contains {existing_users_count} users. Skipping seed. Pass force=True to reseed.")
        return {"status": "skipped", "message": f"Database already seeded ({existing_users_count} users present)"}

    if force:
        logger.info("Force flag set. Cleaning existing data...")
        db.query(Transaction).delete()
        db.query(User).delete()
        db.commit()

    logger.info("Seeding Users...")
    created_users = []
    for user_data in SAMPLE_USERS:
        user = User(**user_data)
        db.add(user)
        created_users.append(user)

    db.commit()
    for u in created_users:
        db.refresh(u)

    logger.info("Seeding Transactions...")
    created_transactions = 0
    for tx_data in SAMPLE_TRANSACTIONS:
        u_idx = tx_data["user_index"]
        if u_idx < len(created_users):
            user = created_users[u_idx]
            tx = Transaction(
                user_id=user.id,
                amount=tx_data["amount"],
                currency=tx_data["currency"],
                transaction_type=tx_data["transaction_type"],
                status=tx_data["status"],
                description=tx_data["description"]
            )
            db.add(tx)
            created_transactions += 1

    db.commit()
    logger.info(f"Successfully seeded {len(created_users)} users and {created_transactions} transactions!")

    return {
        "status": "success",
        "users_created": len(created_users),
        "transactions_created": created_transactions
    }

if __name__ == "__main__":
    force_seed = "--force" in sys.argv
    db = SessionLocal()
    try:
        res = seed_database(db, force=force_seed)
        print("Seed result:", res)
    finally:
        db.close()
