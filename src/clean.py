import pandas as pd
import re

GENERIC_PREFIXES = ("info@", "contact@", "support@", "admin@", "direction@")
DISPOSABLE_DOMAINS = ("mailinator.com", "tempmail.com")


def normalize_siren(siren):
    if pd.isna(siren):
        return None
    return str(siren).replace(" ", "").strip()


def normalize_email(email):
    if pd.isna(email):
        return None
    return str(email).strip().lower()


def normalize_company(company):
    if pd.isna(company):
        return None
    return str(company).strip()


def is_valid_email(email):
    if not email:
        return False
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return bool(re.match(pattern, email))


def is_generic_email(email):
    return email.startswith(GENERIC_PREFIXES)


def is_disposable_email(email):
    if not email or "@" not in email:
        return False
    domain = email.split("@")[-1]
    return domain in DISPOSABLE_DOMAINS


# ----------------------------
#  priorité email métier
# ----------------------------
def email_priority(email):
    if not email:
        return 0
    if is_disposable_email(email):
        return 0
    if is_generic_email(email):
        return 1
    return 2


def process_data(csv_path):

    df = pd.read_csv(csv_path)

    # clé métier enrichie
    best_by_siren = {}

    reasons = {
        "invalid": 0,
        "generic": 0,
        "disposable": 0,
        "duplicate": 0
    }

    report = []

    for idx, row in df.iterrows():

        raw_id = row.get("raw_id", idx + 1)

        siren = normalize_siren(row["siren"])
        email = normalize_email(row["email"])
        company = normalize_company(row["societe"])

        if not is_valid_email(email):
            reasons["invalid"] += 1
            report.append(f"{raw_id}: rejected invalid")
            continue

        # choix du meilleur email par SIREN
        current_score = email_priority(email)

        if siren in best_by_siren:
            existing = best_by_siren[siren]
            existing_score = email_priority(existing["email"])

            if current_score <= existing_score:
                reasons["duplicate"] += 1
                report.append(f"{raw_id}: rejected weaker email for same siren")
                continue

        best_by_siren[siren] = {
            "siren": siren,
            "company": company,
            "email": email,
            "status": "new"
        }

        report.append(f"{raw_id}: kept {siren} ({email})")

    kept = list(best_by_siren.values())

    stats = {
        "input": len(df),
        "kept": len(kept),
        "rejected": len(df) - len(kept),
        "reasons": reasons
    }

    return stats, report, kept