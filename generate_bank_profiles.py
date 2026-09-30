#!/usr/bin/env python3
"""Deterministic synthetic profiles. No real customer or payment data is used."""
import json
import random
import zipfile
from collections import Counter, OrderedDict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from faker import Faker, VERSION as FAKER_VERSION
from faker.providers import BaseProvider

ROOT = Path(__file__).resolve().parent
RNG = random.Random(202609301)
Faker.seed(202609301)
FAKES = {locale: Faker(locale) for locale in ("fr_BE", "nl_BE", "fr_FR", "nl_NL", "de_DE")}
for index, fake in enumerate(FAKES.values()):
    fake.seed_instance(202609301 + index)
COUNT = 5000
START = date(2026, 7, 1)
END = date(2026, 9, 30)
PLACES = [
    ("Belgique", "Bruxelles-Capitale", "Bruxelles", 12),
    ("Belgique", "Anvers", "Anvers", 12),
    ("Belgique", "Flandre orientale", "Gand", 10),
    ("Belgique", "Flandre occidentale", "Bruges", 8),
    ("Belgique", "Brabant flamand", "Louvain", 8),
    ("Belgique", "Limbourg", "Hasselt", 6),
    ("Belgique", "Hainaut", "Mons", 7),
    ("Belgique", "Liège", "Liège", 8),
    ("Belgique", "Brabant wallon", "Wavre", 4),
    ("Belgique", "Namur", "Namur", 4),
    ("Belgique", "Luxembourg", "Arlon", 3),
    ("France", "Hauts-de-France", "Lille", 6),
    ("France", "Île-de-France", "Paris", 3),
    ("Pays-Bas", "Hollande-Méridionale", "Rotterdam", 3),
    ("Pays-Bas", "Brabant-Septentrional", "Eindhoven", 2),
    ("Allemagne", "Rhénanie-du-Nord-Westphalie", "Cologne", 2),
    ("Luxembourg", "Luxembourg", "Luxembourg", 2),
]


class BankLocationProvider(BaseProvider):
    """Choose whole location tuples so cities always match their regions."""
    def bank_location(self):
        return self.random_element(OrderedDict((p[:3], p[3]) for p in PLACES))


for fake in FAKES.values():
    fake.add_provider(BankLocationProvider)


def locale_for(country, region):
    if country == "Belgique":
        return "nl_BE" if region in {"Anvers", "Flandre orientale", "Flandre occidentale", "Brabant flamand", "Limbourg"} else "fr_BE"
    return {"France": "fr_FR", "Pays-Bas": "nl_NL", "Allemagne": "de_DE", "Luxembourg": "fr_FR"}[country]


# Ranges are simulation choices, not population statistics or KBC customer segments.
SEGMENTS = {
    "etudiant": (18, 28, 500, 1400, 150, 1400, 25, 65),
    "debut_carriere": (21, 32, 1800, 3000, 500, 4500, 35, 85),
    "salarie": (25, 64, 2300, 4300, 700, 9000, 40, 95),
    "famille": (28, 59, 3000, 5800, 1000, 12000, 55, 115),
    "independant": (23, 65, 2400, 6500, 1500, 18000, 40, 90),
    "revenus_irreguliers": (19, 61, 850, 2000, 100, 1800, 20, 55),
    "retraite": (65, 85, 1300, 3300, 1000, 15000, 25, 70),
    "revenus_eleves": (30, 64, 5000, 9500, 5000, 35000, 50, 110),
}
SEGMENT_WEIGHTS = [12, 17, 25, 18, 9, 8, 8, 3]
MERCHANTS = {
    "courses": (["Carrefour", "Lidl", "Aldi", "Épicerie du quartier (fictive)", "Marché local (fictif)"], 800, 11000),
    "restauration_rapide": (["McDonald's", "Burger King", "Quick", "KFC", "Domino's Pizza", "Friterie du Centre (fictive)"], 650, 3800),
    "restaurant": (["Restaurant Le Jardin (fictif)", "Pizzeria Bella (fictive)", "Sushi Corner (fictif)", "Brasserie de la Place (fictive)"], 1800, 12500),
    "cafe_boulangerie": (["Starbucks", "PAUL", "Boulangerie du Parc (fictive)", "Café Central (fictif)"], 220, 1800),
    "shopping": (["H&M", "Zara", "Uniqlo", "Zalando", "Primark", "Vinted"], 900, 15000),
    "electronique": (["MediaMarkt", "Apple", "Amazon", "Fnac", "Coolblue"], 1500, 120000),
    "maison": (["IKEA", "JYSK", "Action", "Brico", "Maisons du Monde"], 650, 45000),
    "transport_public": (["Billetterie transport local (fictive)"], 250, 4500),
    "carburant": (["Shell", "TotalEnergies", "Q8", "Esso"], 2000, 9500),
    "loisirs": (["Cinéma local (fictif)", "Musée municipal (fictif)", "Ticketmaster", "Steam"], 600, 12000),
    "sport": (["Decathlon", "Intersport", "Boutique Sport Plus (fictive)"], 1000, 18000),
    "livres": (["Fnac", "Librairie du Centre (fictive)", "Amazon Books"], 700, 6500),
    "animaux": (["Zooplus", "Animalerie du quartier (fictive)"], 1200, 9500),
}
LOCAL = {
    "Belgique": {"courses": ["Colruyt", "Delhaize", "Carrefour", "Lidl", "Aldi"], "transport_public": ["SNCB", "STIB", "De Lijn", "TEC"], "telecom": ["Proximus", "Orange Belgium", "Telenet"], "energie": ["Engie", "Luminus"]},
    "France": {"courses": ["Carrefour", "E.Leclerc", "Auchan", "Lidl", "Intermarché"], "transport_public": ["SNCF", "Billetterie transport local (fictive)"], "telecom": ["Orange", "Free", "SFR"], "energie": ["EDF", "Engie"]},
    "Pays-Bas": {"courses": ["Albert Heijn", "Jumbo", "Lidl", "Aldi"], "transport_public": ["NS", "RET"], "telecom": ["KPN", "Odido", "Vodafone"], "energie": ["Eneco", "Vattenfall"]},
    "Allemagne": {"courses": ["REWE", "Edeka", "Lidl", "Aldi"], "transport_public": ["Deutsche Bahn", "Billetterie transport local (fictive)"], "telecom": ["Telekom", "Vodafone", "O2"], "energie": ["E.ON", "Vattenfall"]},
    "Luxembourg": {"courses": ["Cactus", "Auchan", "Lidl", "Delhaize"], "transport_public": ["CFL - trajet international (fictif)"], "telecom": ["POST Luxembourg", "Orange Luxembourg"], "energie": ["Enovos"]},
}


def money(cents):
    return round(cents / 100, 2)


def random_day(fake):
    return fake.date_between_dates(date_start=START, date_end=END)


def profile(i):
    cid = f"CLIENT-SYN-{i:06d}"
    aid = f"COMPTE-SYN-{i:06d}"
    country, region, city = FAKES["fr_BE"].bank_location()
    locale = locale_for(country, region)
    fake = FAKES[locale]
    name = fake.first_name()
    scenario = RNG.choices(list(SEGMENTS), SEGMENT_WEIGHTS)[0]
    minage, maxage, mininc, maxinc, minbal, maxbal, minops, maxops = SEGMENTS[scenario]
    age = fake.random_int(min=minage, max=maxage)
    income = RNG.randint(mininc, maxinc) * 100
    family = scenario == "famille"
    car = scenario not in {"etudiant"} and RNG.random() < .62
    pet = RNG.random() < .27
    # Personal accounts only; family income can include transfers from a partner.
    housing = RNG.choices(["locataire", "proprietaire_credit", "proprietaire_sans_credit", "heberge"], [50, 0, 0, 50] if scenario == "etudiant" else [20, 15, 60, 5] if scenario == "retraite" else [40, 35, 15, 10])[0]
    housing_cost = int(income * RNG.uniform(.19, .34)) if housing in {"locataire", "proprietaire_credit"} else 0
    events = []

    def add(day, cents, direction, category, counterparty, kind="paiement_carte", merchant_country=None, note=None, linked=None):
        events.append({"_day": day, "_cents": int(cents), "sens": direction,
                       "categorie": category, "contrepartie": counterparty, "type": kind,
                       "pays_contrepartie": merchant_country or country,
                       "libelle": note or category.replace("_", " ").capitalize(), "_linked": linked})
        return len(events) - 1

    provider_tel = RNG.choice(LOCAL[country]["telecom"])
    provider_energy = RNG.choice(LOCAL[country]["energie"])
    tel_amount = RNG.randint(1800, 9500)
    energy_amount = RNG.randint(6500, 23000)
    insurance_amount = RNG.randint(1200, 6800)
    subs = RNG.sample([("Spotify", 1099), ("Netflix", 1399), ("Disney+", 999), ("Amazon Prime", 699), ("YouTube Premium", 1299)], RNG.randint(0, 3))
    salary_day = RNG.choice([1, 25, 27, 28])
    employer = f"{fake.company()} (entreprise fictive)"
    relatives = [f"{fake.first_name()} {fake.last_name()} (personne fictive)" for _ in range(4)]
    business_clients = [f"{fake.company()} (entreprise fictive)" for _ in range(5)]
    landlord = f"{fake.first_name()} {fake.last_name()} (bailleur fictif)"
    has_investment = scenario in {"salarie", "famille", "revenus_eleves", "independant"} and RNG.random() < .3
    savings_order = int(income * RNG.uniform(.03, .12)) if scenario not in {"revenus_irreguliers"} and RNG.random() < .65 else 0

    for month in (7, 8, 9):
        if scenario == "etudiant":
            add(date(2026, month, 2), income * .65, "credit", "aide_familiale", relatives[0], "virement")
            add(date(2026, month, 26), income * RNG.uniform(.2, .45), "credit", "job_etudiant", employer, "virement")
        elif scenario in {"independant", "revenus_irreguliers"}:
            n = RNG.randint(2, 5)
            for k in range(n):
                add(date(2026, month, RNG.randint(1, 28)), income / n * RNG.uniform(.7, 1.3), "credit", "revenu_activite", business_clients[k], "virement", note="Règlement prestation fictive")
        elif scenario == "retraite":
            add(date(2026, month, 8), income, "credit", "pension", "Organisme de pension fictif", "virement")
        else:
            add(date(2026, month, salary_day), income, "credit", "salaire", employer, "virement")
        if housing_cost:
            add(date(2026, month, 3), housing_cost, "debit", "loyer" if housing == "locataire" else "credit_logement", landlord if housing == "locataire" else "Prêteur logement fictif", "ordre_permanent" if housing == "locataire" else "domiciliation")
        if housing != "heberge":
            add(date(2026, month, 11), energy_amount, "debit", "energie", provider_energy, "domiciliation")
            add(date(2026, month, 14), insurance_amount, "debit", "assurance_habitation", "Assureur fictif", "domiciliation")
        add(date(2026, month, 9), tel_amount, "debit", "telecom", provider_tel, "domiciliation")
        for j, (brand, amount) in enumerate(subs):
            add(date(2026, month, 15+j), amount, "debit", "abonnement", brand, "domiciliation")
        if car:
            add(date(2026, month, 19), 5500, "debit", "assurance_auto", "Assureur fictif", "domiciliation")
        if savings_order:
            add(date(2026, month, 29), savings_order, "debit", "transfert_epargne", "Compte épargne personnel fictif", "ordre_permanent")
        if has_investment:
            add(date(2026, month, 28), 10000, "debit", "investissement", "Compte investissement personnel fictif", "ordre_permanent")

    cats = list(MERCHANTS)
    weights = [30, 12, 8, 13, 7, 1, 3, 7, 8 if car else 0, 5, 3, 3, 4 if pet else 0]
    if scenario == "etudiant":
        weights = [20, 18, 3, 12, 7, 1, 1, 15, 0, 8, 5, 6, 3 if pet else 0]
    if scenario == "retraite":
        weights = [40, 2, 8, 12, 4, 1, 6, 8, 8 if car else 0, 3, 2, 6, 4 if pet else 0]
    for _ in range(RNG.randint(minops, maxops)):
        cat = RNG.choices(cats, weights)[0]
        brands, low, high = MERCHANTS[cat]
        merchant = RNG.choice(LOCAL[country].get(cat, brands))
        amount = int(RNG.triangular(low, high, low + (high-low)*.18))
        if scenario in {"etudiant", "revenus_irreguliers"}:
            amount = max(150, int(amount * .62))
        if family and cat == "courses":
            amount = int(amount * 1.45)
        if scenario == "revenus_eleves" and cat in {"restaurant", "shopping", "electronique"}:
            amount = int(amount * 1.4)
        day = random_day(fake)
        idx = add(day, amount, "debit", cat, merchant)
        if cat in {"shopping", "electronique", "maison"} and RNG.random() < .07:
            refund_day = day + timedelta(days=RNG.randint(2, 12))
            if refund_day <= END:
                add(refund_day, amount, "credit", "remboursement_achat", merchant, "remboursement", linked=idx)

    if RNG.random() < (.12 if scenario == "revenus_irreguliers" else .3):
        destination = RNG.choice(["France", "Espagne", "Italie", "Portugal", "Pays-Bas", "Allemagne"])
        day = START + timedelta(days=RNG.randint(10, 75))
        add(day - timedelta(days=8), RNG.randint(6500, 42000), "debit", "voyage_transport", RNG.choice(["Ryanair", "Brussels Airlines", "Eurostar", "easyJet"]), note="Réservation transport fictive")
        add(day, RNG.randint(9000, 75000), "debit", "hebergement_voyage", "Hôtel Horizon (fictif)", merchant_country=destination)
        for offset in range(RNG.randint(2, 5)):
            add(day + timedelta(days=offset), RNG.randint(1800, 9500), "debit", "restaurant", "Restaurant de vacances (fictif)", merchant_country=destination)
    for _ in range(RNG.randint(0, 4)):
        incoming = RNG.random() < .5
        add(random_day(fake), RNG.randint(1000, 18000), "credit" if incoming else "debit", "virement_entre_proches", fake.random_element(relatives), "virement", note=RNG.choice(["Partage de frais fictif", "Cadeau fictif", "Remboursement entre proches fictif"]))
    if RNG.random() < .22:
        add(random_day(fake), RNG.choice([2000, 5000, 10000, 15000]), "debit", "retrait_especes", "Distributeur fictif", "retrait")

    # Establish balances in integer cents and tune starting funds to make the full
    # history feasible. Some accounts deliberately have a small overdraft.
    order = sorted(range(len(events)), key=lambda k: (events[k]["_day"], 0 if events[k]["sens"] == "credit" else 1, k))
    initial = RNG.randint(minbal, maxbal) * 100
    running = 0
    lowest = 0
    for k in order:
        e = events[k]
        running += e["_cents"] * (1 if e["sens"] == "credit" else -1)
        lowest = min(lowest, running)
    overdraft = scenario in {"revenus_irreguliers", "debut_carriere", "etudiant"} and RNG.random() < .3
    floor = -RNG.randint(50, 400)*100 if overdraft else RNG.randint(30, 300)*100
    initial = max(initial, floor-lowest) if not overdraft else max(0, floor-lowest)
    ids = {k: f"TX-SYN-{i:06d}-{n:04d}" for n, k in enumerate(order, 1)}
    balance = initial
    transactions = []
    for k in order:
        e = events[k]
        credit = e["sens"] == "credit"
        balance += e["_cents"] * (1 if credit else -1)
        row = {"transaction_id": ids[k], "date": e["_day"].isoformat(),
               "statut": "comptabilisee", "sens": e["sens"], "montant": money(e["_cents"]),
               "devise": "EUR", "debiteur": e["contrepartie"] if credit else cid,
               "crediteur": cid if credit else e["contrepartie"],
               "contrepartie": e["contrepartie"], "pays_contrepartie": e["pays_contrepartie"],
               "categorie": e["categorie"], "type": e["type"], "libelle": e["libelle"],
               "solde_apres": money(balance)}
        if e["_linked"] is not None:
            row["transaction_origine_id"] = ids[e["_linked"]]
        transactions.append(row)
    credits = sum(e["_cents"] for e in events if e["sens"] == "credit")
    debits = sum(e["_cents"] for e in events if e["sens"] == "debit")
    return {"client_id": cid, "synthetique": True, "generateur": "Faker", "locale_faker": locale, "prenom": name, "age": age,
            "pays": country, "region": region, "ville": city,
            "scenario_simulation": scenario, "situation_logement": housing,
            "preferences": {"personnalisation_commerciale": RNG.random() < .72, "canal_prefere": RNG.choice(["application", "email", "telephone", "agence"])},
            "compte": {"compte_id": aid, "type": "compte_courant_personnel", "devise": "EUR",
                       "debut_historique": START.isoformat(), "fin_historique": END.isoformat(),
                       "solde_initial": money(initial), "solde_final": money(balance),
                       "nombre_transactions": len(transactions), "total_credits": money(credits), "total_debits": money(debits),
                       "transactions": transactions}}


def cents(value):
    return int(Decimal(str(value)) * 100)


def validate(p):
    account = p["compte"]
    balance = cents(account["solde_initial"])
    previous = START.isoformat()
    ids = set()
    for t in account["transactions"]:
        assert previous <= t["date"] <= END.isoformat()
        previous = t["date"]
        assert cents(t["montant"]) > 0
        assert t["transaction_id"] not in ids
        if "transaction_origine_id" in t:
            assert t["transaction_origine_id"] in ids
        ids.add(t["transaction_id"])
        assert (t["debiteur"] if t["sens"] == "debit" else t["crediteur"]) == p["client_id"]
        balance += cents(t["montant"]) * (1 if t["sens"] == "credit" else -1)
        assert balance == cents(t["solde_apres"])
    assert balance == cents(account["solde_final"])
    assert balance == cents(account["solde_initial"]) + cents(account["total_credits"]) - cents(account["total_debits"])
    assert len(ids) == account["nombre_transactions"]
    assert (p["pays"], p["region"], p["ville"]) in {place[:3] for place in PLACES}
    assert SEGMENTS[p["scenario_simulation"]][0] <= p["age"] <= SEGMENTS[p["scenario_simulation"]][1]


def main():
    profiles = [profile(i) for i in range(1, COUNT+1)]
    for p in profiles:
        validate(p)
    assert len({p["client_id"] for p in profiles}) == COUNT
    output = ROOT / "profils_bancaires_synthetiques_5000.json"
    output.write_text(json.dumps(profiles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Parse saved JSON as an independent serialization check.
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert len(saved) == COUNT
    sample = ROOT / "apercu_5_profils.json"
    sample.write_text(json.dumps(profiles[:5], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    stats = {"generateur": "Faker", "version_faker": FAKER_VERSION, "graine": 202609301,
             "profils": COUNT, "transactions": sum(p["compte"]["nombre_transactions"] for p in profiles),
             "periode": [START.isoformat(), END.isoformat()], "pays": dict(Counter(p["pays"] for p in profiles)),
             "scenarios": dict(Counter(p["scenario_simulation"] for p in profiles)),
             "age_min": min(p["age"] for p in profiles), "age_max": max(p["age"] for p in profiles),
             "transactions_min_par_profil": min(p["compte"]["nombre_transactions"] for p in profiles),
             "transactions_max_par_profil": max(p["compte"]["nombre_transactions"] for p in profiles),
             "profils_avec_decouvert": sum(any(t["solde_apres"] < 0 for t in p["compte"]["transactions"]) for p in profiles),
             "transactions_mcdonalds": sum(t["contrepartie"] == "McDonald's" for p in profiles for t in p["compte"]["transactions"])}
    (ROOT / "statistiques_profils.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    guide = ROOT / "LIRE_MOI_profils.txt"
    requirements = ROOT / "requirements.txt"
    requirements.write_text(f"Faker=={FAKER_VERSION}\n", encoding="utf-8")
    guide.write_text("""DONNÉES BANCAIRES ENTIÈREMENT SYNTHÉTIQUES — HACKATHON — FAKER

5 000 profils fictifs, un compte courant personnel par profil, du 01/07 au 30/09/2026.
Aucune donnée client KBC réelle n'a été utilisée. Les marques de commerçants peuvent
être réelles, mais tous les paiements, personnes et relations commerciales sont inventés.
Les tarifs, revenus et répartitions sont des choix de simulation, non des statistiques.
Aucun IBAN, numéro de carte ou identifiant bancaire réel n'est présent.

Le fichier principal est un tableau JSON de profils. Chaque profil contient un objet
compte, dont transactions est un tableau chronologique. Tous les montants sont en EUR.
Pour toute somme exacte, utiliser Decimal ou convertir en centimes.

montant : toujours positif ; sens : debit (sortie) ou credit (entrée).
debiteur : celui qui paie ; crediteur : celui qui reçoit.
Exemple : pour un achat McDonald's, le client est débiteur, McDonald's est créditeur.
contrepartie : l'autre partie à l'opération, quel que soit son sens.
solde_initial : avant la première opération ; solde_apres : après cette opération.
solde_final = solde_initial + total_credits - total_debits.
Les remboursements d'achats référencent leur opération d'origine.
Les transferts vers l'épargne sont des sorties de ce compte, pas des dépenses de consommation.
Les contreparties génériques ne permettent pas de reconstituer un registre interbancaire.

scenario_simulation sert à créer des profils variés. Ce champ est une étiquette du
générateur et devrait être masqué si votre modèle doit inférer lui-même le profil.
preferences simule le choix de personnalisation et le canal préféré du client.
Ne pas interpréter le solde courant comme le patrimoine total ou un budget disponible.

Ces profils sont indépendants du précédent fichier de tickets : aucune correspondance
client/ticket n'a été créée. Les identifiants de profils permettent de futures jointures.

Faker génère les prénoms, âges, dates des achats, noms d'employeurs, bailleurs,
clients professionnels et proches. Les locales sont fr_BE, nl_BE, fr_FR, nl_NL, de_DE.
Pour le Luxembourg, fr_FR est utilisé comme approximation linguistique.
Un fournisseur Faker personnalisé choisit des triplets pays/région/ville cohérents.
Les marques, catégories et règles financières sont définies dans le script.
Les noms générés peuvent coïncider fortuitement avec des personnes ou entreprises réelles.

Contenu : JSON complet, aperçu, statistiques, générateur et requirements.txt.
Reproduction avec Python 3.10+ :
  python3 -m venv .venv
  .venv/bin/python -m pip install -r requirements.txt
  .venv/bin/python generate_bank_profiles.py
La version de Faker est fixée et les graines sont constantes pour la reproductibilité.
Contrôles : JSON valide, identifiants uniques, dates ordonnées, sens et contreparties,
soldes transaction par transaction, totaux, références des remboursements.
""", encoding="utf-8")
    archive = ROOT / "profils_bancaires_synthetiques_5000.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for f in [output, sample, ROOT / "statistiques_profils.json", guide, requirements, Path(__file__)]:
            z.write(f, arcname=f.name)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"JSON: {output.stat().st_size / 1_000_000:.1f} Mo; ZIP: {archive.stat().st_size / 1_000_000:.1f} Mo")


if __name__ == "__main__":
    main()
