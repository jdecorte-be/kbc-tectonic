"""Rule-based habit + profiling engine: seeded users and their transactions -> dashboard clients and aggregates.

Everything is derived from the `users` / `transactions` tables; nothing is precomputed.
"""
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from statistics import mean

from app.profiles import PROFILES
from app.schemas import Habit, ProfileId

# Keyword -> category, first match wins (order matters: income before "student", insurance before "health").
CATEGORY_RULES = [
    (("salary", "retainer", "allowance", "grant", "income"), "Income"),
    (("insufficient funds",), "Rejected"),
    (("mortgage", "rent"), "Housing"),
    (("engie", "proximus", "utility"), "Bills"),
    (("insurance",), "Insurance"),
    (("fuel", "q-park", "parking", "garage", "stib", "sncb", "bike", "velo"), "Mobility"),
    (("crèche", "daycare", "toy"), "Childcare"),
    (("groceries",), "Groceries"),
    (("etf", "trade republic", "portfolio"), "Investing"),
    (("savings",), "Saving"),
    (("restaurant", "bar ", "pub", "kebab", "coffee", "bakery"), "Eating out"),
    (("spotify", "netflix"), "Subscriptions"),
    (("pharmacy",), "Health"),
    (("flight", "hotel", "airbnb", "booking"), "Travel"),
]
AGE = {"18-25": 22, "26-35": 30, "36-50": 43, "51-65": 58, "65+": 70}
WINDOW = 30  # days per "month" window
MIN_CONFIDENCE = 35
MIN_BASELINE = 50  # € per window; smaller categories are too noisy to flag drift
HABITS = [h.value for h in Habit]


def categorize(description: str) -> str:
    d = (description or "").lower()
    return next((cat for keys, cat in CATEGORY_RULES if any(k in d for k in keys)), "Shopping")


def _txs(user) -> list[dict]:
    out = []
    for t in user.transactions:
        amount = float(t.amount)
        out.append({
            "at": t.created_at,
            "merchant": t.description or t.transaction_type,
            "category": categorize(t.description),
            "amount": amount if t.transaction_type == "deposit" else -amount,
            "failed": t.status == "failed",
        })
    return sorted(out, key=lambda t: t["at"], reverse=True)


def _windows(txs: list[dict], end: datetime) -> list[list[dict]]:
    """Full 30-day windows covered by the data, oldest first."""
    start = min(t["at"] for t in txs)
    n = max(1, int((end - start).days // WINDOW))
    return [[t for t in txs if end - timedelta(days=WINDOW * (i + 1)) < t["at"] <= end - timedelta(days=WINDOW * i)]
            for i in reversed(range(n))]


def _spend(txs, categories=None) -> float:
    return sum(-t["amount"] for t in txs
               if t["amount"] < 0 and not t["failed"] and t["category"] not in ("Saving", "Investing")
               and (categories is None or t["category"] in categories))


def _flow(txs, category) -> float:
    return sum(-t["amount"] for t in txs if t["category"] == category and not t["failed"])


def _profiles(user, txs, windows, income_m, savings_rate) -> tuple[list[dict], dict]:
    """Score every profile from evidence; returns scores (highest first) and signals per profile."""
    age = AGE.get(user.age_range, 40)
    months = len(windows)
    by_cat = defaultdict(list)
    for t in txs:
        by_cat[t["category"]].append(t)
    income_desc = Counter(t["merchant"] for t in by_cat["Income"]).most_common(1)
    income_desc = income_desc[0][0].lower() if income_desc else ""
    invest_m = _flow(txs, "Investing") / months
    mobility = [t["merchant"] for t in by_cat["Mobility"]]
    ev: dict[ProfileId, list[tuple[str, float]]] = defaultdict(list)

    def add(p, cond, text, w):
        if cond:
            ev[p].append((text, w))

    add(ProfileId.student, "student" in income_desc, f"Student grant / part-time income (€{income_m:,.0f}/month)", 0.45)
    add(ProfileId.student, any("campus" in t["merchant"].lower() or "student" in t["merchant"].lower() for t in txs if t["amount"] < 0), "Student-priced spend (campus, student subscriptions)", 0.3)
    add(ProfileId.student, age <= 25, "Age 18–25", 0.15)

    add(ProfileId.young_investor, invest_m > 0 and age <= 35, f"Monthly ETF investing (€{invest_m:,.0f}/month) at age {user.age_range}", 0.55)
    add(ProfileId.young_investor, invest_m > 0 and savings_rate >= 15, f"Savings + investing rate {savings_rate:.0f}% of income", 0.25)
    add(ProfileId.investor, invest_m > 0 and age > 35, f"Recurring investment flows (€{invest_m:,.0f}/month)", 0.55)
    add(ProfileId.investor, invest_m >= 500 and income_m >= 3500, "High income with large investment transfers", 0.3)

    add(ProfileId.holiday, bool(by_cat["Travel"]), f"{len(by_cat['Travel'])} recent travel bookings (€{_flow(txs, 'Travel'):,.0f})", 0.45)
    add(ProfileId.holiday, any("travel" in t["merchant"].lower() for t in by_cat["Saving"]), "Monthly transfer to a travel savings pot", 0.35)

    care = [t for t in by_cat["Childcare"] if "crèche" in t["merchant"].lower() or "daycare" in t["merchant"].lower()]
    add(ProfileId.family, bool(care), f"Monthly crèche / daycare fee (€{abs(care[0]['amount']):,.0f})" if care else "", 0.55)
    add(ProfileId.family, any("toy" in t["merchant"].lower() for t in by_cat["Childcare"]), "Toy & school supplies purchases", 0.25)
    add(ProfileId.family, user.children_count > 0, f"{user.children_count} child{'ren' if user.children_count > 1 else ''} in household", 0.15)

    add(ProfileId.homebuyer, any("real estate" in t["merchant"].lower() for t in by_cat["Saving"]), "Monthly real-estate down-payment savings", 0.55)
    add(ProfileId.homebuyer, any("mortgage" in t["merchant"].lower() for t in by_cat["Housing"]), "Mortgage auto-debit", 0.2)

    add(ProfileId.commuter, any("fuel" in m.lower() for m in mobility), f"{sum('fuel' in m.lower() for m in mobility)} fuel station visits", 0.45)
    add(ProfileId.commuter, any("park" in m.lower() for m in mobility), "City parking", 0.2)
    add(ProfileId.commuter, any("transit" in m.lower() or "train" in m.lower() for m in mobility), "Monthly transit pass and train tickets", 0.45)
    add(ProfileId.commuter, any("garage" in m.lower() for m in mobility), "Car inspection & maintenance", 0.15)

    add(ProfileId.freelancer, "consulting" in income_desc or "retainer" in income_desc, "Income from a consulting retainer, not a payroll salary", 0.5)

    rejected = by_cat["Rejected"]
    stressed = bool(rejected) or "unemployment" in income_desc
    add(ProfileId.saver, savings_rate >= 15 and not stressed, f"{savings_rate:.0f}% of income moved to savings/investments", 0.5)
    add(ProfileId.saver, user.discretionary_spender == "frugal" and not stressed, "Low discretionary spend, budget grocery stores", 0.25)

    add(ProfileId.financial_stress, bool(rejected), f"{len(rejected)} rejected payment(s) for insufficient funds", 0.45)
    add(ProfileId.financial_stress, "unemployment" in income_desc, "Unemployment allowance as only income", 0.35)
    add(ProfileId.financial_stress, savings_rate < 5, f"Low savings rate ({savings_rate:.0f}%)", 0.1)

    add(ProfileId.retiree, "pension" in income_desc, "Pension income", 0.6)

    if not ev:  # no life-stage signal at all: fall back to a low-confidence saver profile
        ev[ProfileId.saver].append((f"No strong life-stage signal; saves {savings_rate:.0f}% of income", 0.2))

    scores = sorted(
        ({"id": p.value, "confidence": min(97, round(sum(w for _, w in e) * 100))} for p, e in ev.items()),
        key=lambda s: s["confidence"], reverse=True,
    )
    return [s for s in scores if s["confidence"] >= MIN_CONFIDENCE] or scores[:1], ev


def _change(windows) -> dict | None:
    """Biggest drift of the last window vs the client's own baseline (average of earlier windows)."""
    if len(windows) < 2:
        return None
    last, base = windows[-1], windows[:-1]
    rejected = [t for t in last + base[-1] if t["category"] == "Rejected"]
    if rejected:
        return {"habit": "Payments", "text": f"{len(rejected)} rejected payment(s) in the last 60 days", "delta": 100, "severity": "alert"}
    best = None
    for cat in {t["category"] for w in windows for t in w if t["amount"] < 0} - {"Rejected", "Housing"}:
        baseline = mean(_spend(w, {cat}) or _flow(w, cat) for w in base)
        now = _spend(last, {cat}) or _flow(last, cat)
        if baseline < MIN_BASELINE:
            continue
        delta = round((now - baseline) / baseline * 100)
        if abs(delta) >= 25 and (best is None or abs(delta) > abs(best["delta"])):
            best = {"habit": cat, "text": f"{cat} spend {'+' if delta > 0 else ''}{delta}% vs. own baseline (€{now:,.0f} vs €{baseline:,.0f})",
                    "delta": delta, "severity": "watch" if abs(delta) >= 50 else "info"}
    return best


def _recurring(windows) -> int:
    """Same merchant + amount, at most twice per window, in at least 3 windows."""
    seen = defaultdict(set)
    per_window = Counter()
    for i, w in enumerate(windows):
        for t in w:
            if t["amount"] < 0 and not t["failed"]:
                key = (t["merchant"], t["amount"])
                seen[key].add(i)
                per_window[(key, i)] += 1
    return sum(1 for k, ws in seen.items() if len(ws) >= 3 and all(per_window[(k, i)] <= 2 for i in ws))


def build_client(user, now: datetime) -> dict:
    txs = _txs(user)
    end = txs[0]["at"] if txs else now
    windows = _windows(txs, end) if txs else [[]]
    income_m = sum(t["amount"] for t in txs if t["category"] == "Income") / len(windows)
    saved_m = (_flow(txs, "Saving") + _flow(txs, "Investing")) / len(windows)
    savings_rate = round(saved_m / income_m * 100) if income_m else 0
    scores, ev = _profiles(user, txs, windows, income_m, savings_rate)
    main = ProfileId(scores[0]["id"])
    total = sum(w for _, w in ev[main]) or 1
    habit_spend = {h: _spend(txs, {h}) or _flow(txs, h) for h in HABITS}
    paydays = Counter(t["at"].day for t in txs if t["category"] == "Income")
    return {
        "id": str(user.id),
        "name": user.name,
        "age": AGE.get(user.age_range, 40),
        "profiles": scores,
        "monthlySpend": [round(_spend(w)) for w in windows],
        "spendMonths": [(end - timedelta(days=WINDOW * (len(windows) - 1 - i))).strftime("%-d %b") for i in range(len(windows))],
        "savingsRate": savings_rate,
        "recurringCount": _recurring(windows),
        "cashShare": 0,
        "payday": paydays.most_common(1)[0][0] if paydays else 1,
        "topHabit": max(habit_spend, key=habit_spend.get),
        "signals": [{"text": text, "weight": round(w / total, 2)} for text, w in ev[main]],
        "change": _change(windows),
        "transactions": [{"date": t["at"].date().isoformat(), "merchant": t["merchant"], "category": t["category"], "amount": t["amount"]} for t in txs],
        "lastScanned": now,
    }


def build_clients(users) -> list[dict]:
    now = datetime.now(timezone.utc)
    return [build_client(u, now) for u in sorted(users, key=lambda u: u.id) if u.transactions]


def build_dashboard(users, clients: list[dict]) -> dict:
    segments = Counter(c["profiles"][0]["id"] for c in clients)
    txs = [t for u in users for t in _txs(u)]
    end = max((t["at"] for t in txs), default=datetime.now(timezone.utc))
    n = max(1, len(clients))

    # Weekly spend per habit over the last 12 weeks (avg per client); baseline = mean of the first 8 weeks.
    habit_trends = {}
    for h in HABITS:
        weeks = []
        for w in reversed(range(12)):
            hi = end - timedelta(weeks=w)
            ws = [t for t in txs if hi - timedelta(weeks=1) < t["at"] <= hi]
            weeks.append((hi, (_spend(ws, {h}) or _flow(ws, h)) / n))
        baseline = round(mean(s for _, s in weeks[:8]), 2)
        habit_trends[h] = [{"date": d, "spend": round(s, 2), "baseline": baseline} for d, s in weeks]

    # Average daily spend per client, by weekday.
    days = Counter()
    spend = Counter()
    start = min((t["at"] for t in txs), default=end)
    d = start.date()
    while d <= end.date():
        days[d.weekday()] += 1
        d += timedelta(days=1)
    for t in txs:
        if t["amount"] < 0 and not t["failed"] and t["category"] not in ("Saving", "Investing"):
            spend[t["at"].weekday()] += -t["amount"]
    weekday = [{"day": name, "spend": round(spend[i] / max(1, days[i]) / n)} for i, name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])]

    return {
        "kpis": {
            "clientsTracked": len(clients),
            "profilesDetected": len({p["id"] for c in clients for p in c["profiles"]}),
            "habitChanges": sum(1 for c in clients if c["change"]),
            "openOpportunities": sum(1 for c in clients if c["change"] and c["change"]["severity"] != "info"),
        },
        "segments": [{"id": pid, "label": PROFILES[ProfileId(pid)]["label"], "count": cnt} for pid, cnt in segments.most_common()],
        "habitTrends": habit_trends,
        "weekdayRhythm": weekday,
        "links": [],
    }
