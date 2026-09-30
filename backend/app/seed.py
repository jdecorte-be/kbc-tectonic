import sys
import logging
import random
from datetime import datetime, timedelta, timezone
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
        "is_active": True,
        "financial_situation": "comfortable",
        "is_student": False,
        "is_unemployed": False,
        "is_high_income": True,
        "discretionary_spender": "frugal",
        "main_transportation": "car",
        "children_count": 2,
        "in_couple": True,
        "has_insurance": True,
        "housing_status": "owner",
        "age_range": "36-50",
        "savings_goal": "real_estate",
        "risk_tolerance": "medium"
    },
    {
        "name": "Sophie Martin",
        "phone_number": "+32 485 98 76 54",
        "email": "sophie.martin@example.com",
        "address": "Meir 42",
        "city": "Antwerp",
        "country": "Belgium",
        "is_active": True,
        "financial_situation": "comfortable",
        "is_student": False,
        "is_unemployed": False,
        "is_high_income": True,
        "discretionary_spender": "impulsive",
        "main_transportation": "public_transit",
        "children_count": 0,
        "in_couple": False,
        "has_insurance": True,
        "housing_status": "renter",
        "age_range": "26-35",
        "savings_goal": "investment",
        "risk_tolerance": "high"
    },
    {
        "name": "Lucas Janssens",
        "phone_number": "+32 496 11 22 33",
        "email": "lucas.janssens@example.com",
        "address": "Kortrijksesteenweg 201",
        "city": "Ghent",
        "country": "Belgium",
        "is_active": True,
        "financial_situation": "balanced",
        "is_student": True,
        "is_unemployed": False,
        "is_high_income": False,
        "discretionary_spender": "moderate",
        "main_transportation": "bicycle",
        "children_count": 0,
        "in_couple": True,
        "has_insurance": True,
        "housing_status": "free_housing",
        "age_range": "18-25",
        "savings_goal": "travel",
        "risk_tolerance": "low"
    },
    {
        "name": "Emma Peeters",
        "phone_number": "+32 478 55 66 77",
        "email": "emma.peeters@example.com",
        "address": "Place Saint-Lambert 15",
        "city": "Liège",
        "country": "Belgium",
        "is_active": True,
        "financial_situation": "balanced",
        "is_student": False,
        "is_unemployed": False,
        "is_high_income": False,
        "discretionary_spender": "moderate",
        "main_transportation": "car",
        "children_count": 1,
        "in_couple": True,
        "has_insurance": True,
        "housing_status": "renter",
        "age_range": "26-35",
        "savings_goal": "emergency_fund",
        "risk_tolerance": "low"
    },
    {
        "name": "Marc Dubois",
        "phone_number": "+32 460 44 88 11",
        "email": "marc.dubois@example.com",
        "address": "Boulevard Tirou 88",
        "city": "Charleroi",
        "country": "Belgium",
        "is_active": False,
        "financial_situation": "tight",
        "is_student": False,
        "is_unemployed": True,
        "is_high_income": False,
        "discretionary_spender": "impulsive",
        "main_transportation": "walking",
        "children_count": 0,
        "in_couple": False,
        "has_insurance": False,
        "housing_status": "renter",
        "age_range": "51-65",
        "savings_goal": "emergency_fund",
        "risk_tolerance": "low"
    }
]

def generate_user_transactions(user_id: int, u: dict, target_count: int = 100) -> list:
    """Generate exactly `target_count` lifestyle-matched transactions for a user."""
    rng = random.Random(user_id * 42) # Deterministic random per user
    now = datetime.now(timezone.utc)
    raw_txs = []

    # 1. Income / Salary Credits (12 months)
    for month in range(12):
        tx_date = now - timedelta(days=month * 30 + rng.randint(0, 3))
        if u["is_high_income"]:
            amount = Decimal(str(rng.randint(3800, 4800))) + Decimal("0.00")
            desc = "Monthly Executive Senior Salary" if u["age_range"] == "36-50" else "Consulting Senior Monthly Retainer"
            raw_txs.append((tx_date, amount, "EUR", "deposit", "completed", desc))
        elif u["is_unemployed"]:
            amount = Decimal(str(rng.randint(1020, 1150))) + Decimal(".50")
            raw_txs.append((tx_date, amount, "EUR", "deposit", "completed", "Monthly Unemployment Social Allowance"))
        elif u["is_student"]:
            amount = Decimal(str(rng.randint(550, 750))) + Decimal(".00")
            raw_txs.append((tx_date, amount, "EUR", "deposit", "completed", "Student Grant & Part-time Job Income"))
        else:
            amount = Decimal(str(rng.randint(2100, 2600))) + Decimal(".00")
            raw_txs.append((tx_date, amount, "EUR", "deposit", "completed", "Monthly Net Salary Deposit"))

    # 2. Housing & Utility Bills (Monthly)
    for month in range(12):
        tx_date = now - timedelta(days=month * 30 + rng.randint(4, 7))
        if u["housing_status"] == "owner":
            amount = Decimal(str(rng.randint(1100, 1400))) + Decimal(".00")
            raw_txs.append((tx_date, amount, "EUR", "payment", "completed", "KBC Bank Monthly Mortgage Auto-Debit"))
            util_date = tx_date + timedelta(days=2)
            raw_txs.append((util_date, Decimal("145.20"), "EUR", "payment", "completed", "Engie Electricity & Gas Monthly Utility"))
        elif u["housing_status"] == "renter":
            amount = Decimal("850.00") if u["financial_situation"] == "comfortable" else Decimal("550.00")
            raw_txs.append((tx_date, amount, "EUR", "payment", "completed", "Monthly Apartment Rent Payment"))
            util_date = tx_date + timedelta(days=2)
            raw_txs.append((util_date, Decimal("89.90"), "EUR", "payment", "completed", "Proximus Internet & Fiber Monthly Bill"))

    # 3. Insurance Payments (if applicable)
    if u["has_insurance"]:
        for month in range(12):
            tx_date = now - timedelta(days=month * 30 + rng.randint(8, 12))
            raw_txs.append((tx_date, Decimal("48.50"), "EUR", "payment", "completed", "Ethias Health & Family Insurance Premium"))

    # 4. Transportation Specific Transactions
    if u["main_transportation"] == "car":
        # 2-3 fuel station visits per month + parking + tolls
        for month in range(12):
            for fuel_idx in range(2):
                tx_date = now - timedelta(days=month * 30 + fuel_idx * 12 + rng.randint(0, 3))
                brand = rng.choice(["Shell Station Brussels", "TotalEnergies Highway", "Q8 Refueling Antwerp"])
                amount = Decimal(str(rng.randint(55, 85))) + Decimal(".40")
                raw_txs.append((tx_date, amount, "EUR", "payment", "completed", f"Fuel Station Refueling - {brand}"))

            # Parking & Tolls
            park_date = now - timedelta(days=month * 30 + rng.randint(5, 25))
            raw_txs.append((park_date, Decimal("18.50"), "EUR", "payment", "completed", "Q-Park Underground City Parking"))

        # Periodic Maintenance
        maint_date = now - timedelta(days=120)
        raw_txs.append((maint_date, Decimal("320.00"), "EUR", "payment", "completed", "Eurogarage Car Inspection & Maintenance"))

    elif u["main_transportation"] == "public_transit":
        for month in range(12):
            tx_date = now - timedelta(days=month * 30 + 1)
            raw_txs.append((tx_date, Decimal("85.00"), "EUR", "payment", "completed", "STIB/MIVB Brussels Monthly Transit Pass"))
            tx_date2 = now - timedelta(days=month * 30 + 15)
            raw_txs.append((tx_date2, Decimal("24.60"), "EUR", "payment", "completed", "SNCB/NMBS Train Ticket Brussels-Antwerp"))

    elif u["main_transportation"] == "bicycle":
        for month in range(12):
            tx_date = now - timedelta(days=month * 30 + rng.randint(2, 20))
            if month % 3 == 0:
                raw_txs.append((tx_date, Decimal("45.00"), "EUR", "payment", "completed", "Cyclo Ghent Bike Repair & Brake Tuning"))
            else:
                raw_txs.append((tx_date, Decimal("12.50"), "EUR", "payment", "completed", "Velo City Bike Monthly Subscription"))

    # 5. Children & Family Expenses
    if u["children_count"] > 0:
        for month in range(12):
            tx_date = now - timedelta(days=month * 30 + rng.randint(3, 10))
            care_amount = Decimal("380.00") if u["children_count"] >= 2 else Decimal("220.00")
            raw_txs.append((tx_date, care_amount, "EUR", "payment", "completed", f"Crèche / Daycare Monthly Fee ({u['children_count']} children)"))

            toy_date = now - timedelta(days=month * 30 + rng.randint(12, 28))
            raw_txs.append((toy_date, Decimal("35.90"), "EUR", "payment", "completed", "DreamLand Toy & School Supplies Store"))

    # 6. Groceries Matching Financial Profile
    for day in range(1, 360, 5): # Roughly every 5 days
        tx_date = now - timedelta(days=day + rng.randint(-1, 1))
        if u["discretionary_spender"] == "frugal" or u["financial_situation"] == "tight":
            store = rng.choice(["Aldi Supermarket", "Lidl Discount Store", "Colruyt Budget Groceries"])
            amount = Decimal(str(rng.randint(25, 55))) + Decimal(".30")
        elif u["is_high_income"]:
            store = rng.choice(["Delhaize Gourmet Market", "Carrefour Market", "Bio-Planet Organic Grocery"])
            amount = Decimal(str(rng.randint(65, 140))) + Decimal(".80")
        else:
            store = rng.choice(["Carrefour Express", "Delhaize Market", "Colruyt Supermarket"])
            amount = Decimal(str(rng.randint(35, 85))) + Decimal(".50")
        raw_txs.append((tx_date, amount, "EUR", "payment", "completed", f"Groceries at {store}"))

    # 7. Discretionary / Lifestyle Purchases
    for day in range(1, 360, 4):
        tx_date = now - timedelta(days=day + rng.randint(-1, 1))
        if u["discretionary_spender"] == "impulsive":
            item = rng.choice([
                ("Zalando Fashion Purchase", 129.90),
                ("Amazon.com Tech Gadgets", 89.50),
                ("Cocktail Bar Antwerp Evening", 65.00),
                ("Gourmet Restaurant Dinner", 145.00),
                ("Sephora Beauty Care Order", 78.20),
                ("Apple Store Accessories", 59.00)
            ])
            raw_txs.append((tx_date, Decimal(str(item[1])), "EUR", "payment", "completed", item[0]))
        elif u["is_student"]:
            item = rng.choice([
                ("Campus Bookstore Textbooks", 24.50),
                ("Student Pub Drinks Night", 14.00),
                ("Spotify Student Subscription", 5.99),
                ("Cheap Kebab & Fries Snack", 8.50),
                ("Netflix Shared Subscription", 11.99)
            ])
            raw_txs.append((tx_date, Decimal(str(item[1])), "EUR", "payment", "completed", item[0]))
        else: # Frugal or moderate
            item = rng.choice([
                ("Local Bakery Artisan Bread", 6.50),
                ("Pharmacy Healthcare Order", 18.20),
                ("Coffee Shop Espresso & Pastry", 7.80),
                ("Decathlon Sports Gear", 29.90)
            ])
            raw_txs.append((tx_date, Decimal(str(item[1])), "EUR", "payment", "completed", item[0]))

    # 8. Savings & Investments (Monthly)
    for month in range(12):
        tx_date = now - timedelta(days=month * 30 + 28)
        if u["savings_goal"] == "investment":
            raw_txs.append((tx_date, Decimal("500.00"), "EUR", "transfer", "completed", "Trade Republic ETF Portfolio Investment"))
        elif u["savings_goal"] == "real_estate":
            raw_txs.append((tx_date, Decimal("750.00"), "EUR", "transfer", "completed", "Real Estate Downpayment Savings Deposit"))
        elif u["savings_goal"] == "travel":
            raw_txs.append((tx_date, Decimal("100.00"), "EUR", "transfer", "completed", "Summer Travel Savings Transfer"))
        else:
            raw_txs.append((tx_date, Decimal("200.00"), "EUR", "transfer", "completed", "Emergency Savings Fund Deposit"))

    # 9. Failed Transactions for Unemployed / Tight Financial Users
    if u["is_unemployed"] or u["financial_situation"] == "tight":
        fail_date1 = now - timedelta(days=45)
        raw_txs.append((fail_date1, Decimal("50.00"), "EUR", "payment", "failed", "Insufficient Funds - Direct Debit Rejection"))
        fail_date2 = now - timedelta(days=120)
        raw_txs.append((fail_date2, Decimal("35.00"), "EUR", "payment", "failed", "Insufficient Funds - Card Payment Declined"))

    # Sort all by date descending
    raw_txs.sort(key=lambda x: x[0], reverse=True)

    # Trim or select exactly `target_count` transactions
    selected_txs = raw_txs[:target_count]

    # Return formatted transaction dicts
    result = []
    for tx in selected_txs:
        result.append({
            "user_id": user_id,
            "amount": tx[1],
            "currency": tx[2],
            "transaction_type": tx[3],
            "status": tx[4],
            "description": tx[5],
            "created_at": tx[0]
        })

    return result

def seed_database(db: Session, force: bool = False) -> dict:
    if force:
        logger.info("Force flag set. Re-creating tables and seeding clean data...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    else:
        Base.metadata.create_all(bind=engine)
        existing_users_count = db.query(User).count()
        if existing_users_count > 0:
            logger.info(f"Database contains {existing_users_count} users. Skipping seed. Pass force=True to reseed.")
            return {"status": "skipped", "message": f"Database already seeded ({existing_users_count} users present)"}

    logger.info("Seeding Users...")
    created_users = []
    for user_data in SAMPLE_USERS:
        user = User(**user_data)
        db.add(user)
        created_users.append(user)

    db.commit()
    for u in created_users:
        db.refresh(u)

    logger.info("Seeding 100 Lifestyle-Matched Transactions per user...")
    total_transactions_created = 0
    for user in created_users:
        # Find raw sample dict for profile traits
        u_dict = next(item for item in SAMPLE_USERS if item["email"] == user.email)
        user_txs = generate_user_transactions(user.id, u_dict, target_count=100)

        for tx_data in user_txs:
            tx = Transaction(
                user_id=user.id,
                amount=tx_data["amount"],
                currency=tx_data["currency"],
                transaction_type=tx_data["transaction_type"],
                status=tx_data["status"],
                description=tx_data["description"],
                created_at=tx_data["created_at"]
            )
            db.add(tx)
            total_transactions_created += 1

    db.commit()
    logger.info(f"Successfully seeded {len(created_users)} users and {total_transactions_created} lifestyle-matched transactions!")

    return {
        "status": "success",
        "users_created": len(created_users),
        "transactions_created": total_transactions_created,
        "transactions_per_user": 100
    }

if __name__ == "__main__":
    force_seed = "--force" in sys.argv
    db = SessionLocal()
    try:
        res = seed_database(db, force=force_seed)
        print("Seed result:", res)
    finally:
        db.close()
