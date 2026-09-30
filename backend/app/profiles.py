"""Profile catalogue and client relations for the dashboard (source of truth for the frontend)."""
from app.schemas import ProfileId

# Order matters: the frontend spaces profile colours evenly in this order.
PROFILES: dict[ProfileId, dict] = {
    ProfileId.student: {"label": "Student", "core": True, "offer": "Youth account + student card",
        "description": "Small recurring allowance, tuition and cheap everyday spend.", "looksFor": ["Allowance / parental transfers", "Tuition & student pass", "Canteen and streaming plans"]},
    ProfileId.young_investor: {"label": "Young investor", "core": True, "offer": "ETF savings plan",
        "description": "First salary with regular transfers into brokerage or savings.", "looksFor": ["Monthly brokerage transfers", "ETF / crypto purchases", "Growing savings rate"]},
    ProfileId.investor: {"label": "Investor", "core": True, "offer": "Portfolio review with advisor",
        "description": "Large, recurring investment flows across several holdings.", "looksFor": ["Large brokerage inflows", "Broker fees and dividends", "Diversified holdings"]},
    ProfileId.holiday: {"label": "Holiday soon", "core": True, "offer": "Travel insurance + FX card",
        "description": "Travel bookings and abroad spending ahead of a trip.", "looksFor": ["Flights, hotels, Airbnb", "FX and ATM abroad", "Travel insurance, outdoor shops"]},
    ProfileId.family: {"label": "New parent / family", "core": False, "offer": "Child savings account",
        "description": "Baby, childcare and larger household spend.", "looksFor": ["Baby shops and pharmacies", "Childcare payments", "Bigger grocery baskets"]},
    ProfileId.homebuyer: {"label": "Homebuyer / mover", "core": False, "offer": "Mortgage simulation",
        "description": "Moving or buying: notary, agency and home fitting costs.", "looksFor": ["Notary and agency fees", "Furniture and DIY", "Rent stopped, mortgage enquiries"]},
    ProfileId.commuter: {"label": "Car owner / commuter", "core": False, "offer": "Car insurance check-up",
        "description": "Car-centric spend: fuel, tolls, parking and insurance.", "looksFor": ["Fuel and tolls", "Parking", "Car insurance or leasing"]},
    ProfileId.freelancer: {"label": "Freelancer", "core": False, "offer": "Business account + VAT pot",
        "description": "Irregular incoming payments and business-style costs.", "looksFor": ["Irregular income", "VAT payments", "Coworking and software"]},
    ProfileId.saver: {"label": "Saver", "core": False, "offer": "Higher-yield savings plan",
        "description": "Steady outflows to savings with restrained discretionary spend.", "looksFor": ["Regular savings transfers", "Low discretionary spend", "High end-of-month balance"]},
    ProfileId.financial_stress: {"label": "Financial stress", "core": False, "offer": "Budget coaching call",
        "description": "Pressure on the budget. Handle with care, offer support first.", "looksFor": ["Overdraft frequency", "Rejected payments", "Rising fixed costs"]},
    ProfileId.retiree: {"label": "Retiree", "core": False, "offer": "Pension planning session",
        "description": "Pension income with healthcare and pension-savings spend.", "looksFor": ["Pension payments", "Healthcare and pharmacy", "Pension savings"]},
    ProfileId.big_event: {"label": "Big event", "core": False, "offer": "Event savings pot",
        "description": "Saving and paying for a wedding or other large event.", "looksFor": ["Venue and catering", "Jewellery and attire", "Event savings pot"]},
}

def profile_list() -> list[dict]:
    return [{"id": pid.value, **p} for pid, p in PROFILES.items()]

def related_clients(c: dict, all_clients: list[dict], links: list[list[str]], limit: int = 4) -> list[dict]:
    """Explicit links (household, shared payments) first, then similarity on profiles, top habit and age."""
    out = []
    for o in all_clients:
        if o["id"] == c["id"]:
            continue
        link = next((l for l in links if {l[0], l[1]} == {c["id"], o["id"]}), None)
        if link:
            out.append({"clientId": o["id"], "kind": "linked", "reason": link[2], "score": 100})
            continue
        mine = {p["id"] for p in c["profiles"]}
        shared = [p["id"] for p in o["profiles"] if p["id"] in mine]
        reasons, score = [], 0
        if shared:
            score += 50 * len(shared)
            reasons.append("Shared profile: " + ", ".join(PROFILES[ProfileId(p)]["label"] for p in shared))
        if o["topHabit"] == c["topHabit"]:
            score += 15
            reasons.append(f"Same top habit ({o['topHabit']})")
        if abs(o["age"] - c["age"]) <= 5:
            score += 10
            reasons.append("Similar age")
        if score >= 25:
            out.append({"clientId": o["id"], "kind": "similar", "reason": " · ".join(reasons), "score": score})
    return sorted(out, key=lambda r: r["score"], reverse=True)[:limit]
