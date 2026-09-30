"""Expand demo_data.json with synthetic clients cloned + jittered from the handcrafted ones (c1-c15).

Usage: python -m app.gen_demo_clients [total=150]   (idempotent: always rebuilds from c1-c15)
Synthetic data only - no real client data.
"""
import json
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

PATH = Path(__file__).parent / "demo_data.json"
FIRST = ["Emma", "Noah", "Louise", "Liam", "Olivia", "Arthur", "Mila", "Jules", "Elise", "Victor", "Lena", "Finn",
         "Fien", "Senne", "Axel", "Ella", "Mathis", "Jade", "Robbe", "Lore", "Tom", "An", "Pieter", "Sara", "Koen",
         "Eva", "Wim", "Katrien", "Dries", "Lien", "Stijn", "Charlotte", "Maxime", "Camille", "Yasmine", "Omar"]
LAST = ["Peeters", "Janssens", "Maes", "Jacobs", "Mertens", "Willems", "Claes", "Goossens", "Wouters", "De Smet",
        "Dubois", "Lambert", "Martens", "Vermeulen", "Hermans", "Pauwels", "Dupont", "Van den Berg", "Declercq",
        "Desmet", "Vandenberghe", "Aerts", "Hendrickx", "Bogaert", "Leclercq", "Michiels", "Verhoeven", "Segers"]
AGE_SPREAD = 4


def jitter(rng, v, pct):
    return round(v * rng.uniform(1 - pct, 1 + pct))


def clone(rng, t, idx, name):
    c = json.loads(json.dumps(t))
    c["id"] = f"c{idx}"
    c["name"] = name
    c["age"] = max(18, t["age"] + rng.randint(-AGE_SPREAD, AGE_SPREAD))
    for p in c["profiles"]:
        p["confidence"] = max(35, min(97, p["confidence"] + rng.randint(-12, 6)))
    c["profiles"].sort(key=lambda p: -p["confidence"])
    c["monthlySpend"] = [jitter(rng, v, 0.25) for v in t["monthlySpend"]]
    c["savingsRate"] = max(0, t["savingsRate"] + rng.randint(-3, 3))
    c["cashShare"] = max(0, t["cashShare"] + rng.randint(-4, 4))
    c["recurringCount"] = max(1, t["recurringCount"] + rng.randint(-1, 2))
    c["payday"] = max(1, min(28, t["payday"] + rng.randint(-2, 2)))
    for s in c["signals"]:
        s["weight"] = round(max(0.05, s["weight"] + rng.uniform(-0.05, 0.05)), 2)
    if c.get("change") and rng.random() < 0.4:
        c["change"] = None
    c["lastScanned"] = (datetime(2026, 9, 30, 6, 13) - timedelta(minutes=rng.randint(0, 600))).strftime("%Y-%m-%dT%H:%M:00.000Z")
    shift = rng.randint(0, 6)
    for tx in c["transactions"]:
        tx["date"] = (date.fromisoformat(tx["date"]) - timedelta(days=shift)).isoformat()
        tx["amount"] = round(tx["amount"] * rng.uniform(0.85, 1.15), 2)
    return c


def main(total=150):
    data = json.loads(PATH.read_text())
    base = data["clients"][:15]
    rng = random.Random(42)
    used = {c["name"] for c in base}
    clients = list(base)
    while len(clients) < total:
        name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
        if name in used:
            continue
        used.add(name)
        clients.append(clone(rng, base[len(clients) % len(base)], len(clients) + 1, name))
    data["clients"] = clients
    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    print(f"{len(clients)} clients written")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 150)
