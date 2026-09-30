"""Jev (TypeSafe System One) client: profiles each client from their transactions.

API: POST https://api.typesafe.ai/v1/systemone with {state, model, questions};
returns typed answers with calibrated probabilities.
"""
from concurrent.futures import ThreadPoolExecutor
import httpx
from fastapi import HTTPException
from app.config import settings

PROFILES = {
    "student": "Student: small allowance/income, tuition, cheap food, public transport, streaming",
    "young_investor": "Young investor: first salary, regular transfers to brokerage/savings, ETF or crypto buys",
    "investor": "Investor: large or recurring investment flows, brokerage fees",
    "holiday_soon": "Going on holiday soon: flights, hotels, Airbnb, FX or ATM abroad, travel insurance",
    "new_parent": "New parent / family: baby shops, childcare, pharmacy, larger groceries",
    "homebuyer": "Homebuyer / mover: notary, agency, furniture/DIY, rent stops",
    "commuter": "Car owner / commuter: fuel, tolls, parking, car insurance, leasing",
    "freelancer": "Freelancer: irregular incoming payments, VAT, coworking, software subscriptions",
    "saver": "Saver: steady transfers to savings, low discretionary spending",
    "financial_stress": "Financial stress: overdraft, rejected payments, payday loans, rising fixed costs",
    "retiree": "Retiree: pension income, healthcare, pension savings",
    "big_event": "Wedding / big event: venues, jewelry, catering",
}

def _questions() -> dict:
    qs = {
        "main_profile": {
            "type": "choice",
            "instructions": "Which customer profile best describes this bank client, based on their transactions?",
            "criteria": PROFILES,
        },
        "income_regularity": {
            "type": "score",
            "instructions": "How regular is this client's income?",
            "criteria": ["No visible income", "Irregular income", "Mostly regular income", "Regular monthly salary or pension"],
        },
    }
    for key, desc in PROFILES.items():
        qs[f"is_{key}"] = {
            "type": "noul",
            "instructions": f"Do these transactions indicate the client fits this profile? {desc}",
        }
    return qs

def _state(user) -> str:
    lines = [f"Bank client #{user.id}, {user.city or 'unknown city'}, {user.country or 'unknown country'}.", "Transactions (date | amount | type | status | description):"]
    for t in sorted(user.transactions, key=lambda t: t.created_at or 0):
        date = t.created_at.date().isoformat() if t.created_at else "?"
        lines.append(f"{date} | {float(t.amount):.2f} {t.currency} | {t.transaction_type} | {t.status} | {t.description or ''}")
    return "\n".join(lines)

def _summarize(answers: dict) -> dict:
    """Turn raw Jev answers into profiles with confidence, highest first."""
    profiles = sorted(
        ({"profile": k, "confidence": answers[f"is_{k}"]["noul"]} for k in PROFILES if f"is_{k}" in answers),
        key=lambda p: p["confidence"], reverse=True,
    )
    main = answers.get("main_profile", {})
    return {
        "main_profile": main.get("choice"),
        "main_profile_confidence": main.get("confidence"),
        "profiles": profiles,
        "income_regularity": answers.get("income_regularity", {}).get("score"),
    }

def _ask(state: str) -> dict:
    if not settings.JEV_API_KEY:
        raise HTTPException(status_code=503, detail="JEV_API_KEY is not configured")
    body = {"state": state, "model": settings.JEV_MODEL, "questions": _questions()}
    try:
        r = httpx.post(
            settings.JEV_API_URL, json=body,
            headers={"Authorization": f"Bearer {settings.JEV_API_KEY}"},
            timeout=settings.JEV_TIMEOUT,
        )
        r.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Jev returned {e.response.status_code}: {e.response.text[:300]}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Jev request failed: {e}")
    return r.json()

def analyze_user(user) -> dict:
    if not user.transactions:
        return {"user_id": user.id, "error": "no transactions"}
    data = _ask(_state(user))
    return {"user_id": user.id, "model": data.get("model"), **_summarize(data.get("answers", {})), "answers": data.get("answers"), "usage": data.get("usage")}

def analyze_users(users) -> list[dict]:
    def one(u):
        try:
            return analyze_user(u)
        except HTTPException as e:
            return {"user_id": u.id, "error": e.detail}
    with ThreadPoolExecutor(max_workers=4) as ex:
        return list(ex.map(one, users))

# Jev profile keys -> dashboard profile ids (frontend ProfileId).
APP_PROFILE = {
    "student": "student", "young_investor": "young-investor", "investor": "investor",
    "holiday_soon": "holiday", "new_parent": "family", "homebuyer": "homebuyer",
    "commuter": "commuter", "freelancer": "freelancer", "saver": "saver",
    "financial_stress": "financial-stress", "retiree": "retiree", "big_event": "big-event",
}

def _client_state(c: dict) -> str:
    lines = [f"Bank client {c['id']}, age {c.get('age', '?')}, payday on day {c.get('payday', '?')}.", "Transactions (date | amount EUR | category | merchant):"]
    for t in sorted(c.get("transactions", []), key=lambda t: t["date"]):
        lines.append(f"{t['date']} | {t['amount']:.2f} | {t['category']} | {t['merchant']}")
    lines += ["Detected signals:", *(f"- {s['text']}" for s in c.get("signals", []))]
    return "\n".join(lines)

def analyze_client(c: dict) -> dict:
    """Score a dashboard demo client: one tracker (probability) per profile."""
    data = _ask(_client_state(c))
    summary = _summarize(data.get("answers", {}))
    return {
        "mainProfile": APP_PROFILE.get(summary["main_profile"]),
        "mainConfidence": summary["main_profile_confidence"],
        "trackers": [{"id": APP_PROFILE[p["profile"]], "confidence": p["confidence"]} for p in summary["profiles"]],
        "incomeRegularity": summary["income_regularity"],
        "model": data.get("model"),
    }

def analyze_clients(clients: list[dict]) -> dict:
    def one(c):
        try:
            return c["id"], analyze_client(c)
        except HTTPException as e:
            return c["id"], {"error": e.detail}
    with ThreadPoolExecutor(max_workers=4) as ex:
        return dict(ex.map(one, clients))
