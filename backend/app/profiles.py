"""Profile catalogue and client relations for the dashboard (source of truth for the frontend)."""
from app.schemas import ProfileId

# Order matters: the frontend spaces profile colours evenly in this order.
PROFILES: dict[ProfileId, dict] = {
    ProfileId.student: {"label": "Student", "core": True, "offer": "Youth account + student card"},
    ProfileId.young_investor: {"label": "Young investor", "core": True, "offer": "ETF savings plan"},
    ProfileId.investor: {"label": "Investor", "core": True, "offer": "Portfolio review with advisor"},
    ProfileId.holiday: {"label": "Holiday soon", "core": True, "offer": "Travel insurance + FX card"},
    ProfileId.family: {"label": "New parent / family", "core": False, "offer": "Child savings account"},
    ProfileId.homebuyer: {"label": "Homebuyer / mover", "core": False, "offer": "Mortgage simulation"},
    ProfileId.commuter: {"label": "Car owner / commuter", "core": False, "offer": "Car insurance check-up"},
    ProfileId.freelancer: {"label": "Freelancer", "core": False, "offer": "Business account + VAT pot"},
    ProfileId.saver: {"label": "Saver", "core": False, "offer": "Higher-yield savings plan"},
    ProfileId.financial_stress: {"label": "Financial stress", "core": False, "offer": "Budget coaching call"},
    ProfileId.retiree: {"label": "Retiree", "core": False, "offer": "Pension planning session"},
    ProfileId.big_event: {"label": "Big event", "core": False, "offer": "Event savings pot"},
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
