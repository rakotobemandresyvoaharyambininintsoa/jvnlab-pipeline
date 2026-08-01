from src.db import get_connection
from datetime import datetime, timezone
import random


# États finaux du pipeline
FINAL_STATES = {"replied", "hard_bounce", "stopped"}


def days_since(date_str):
    if not date_str:
        return 999
    return (datetime.now(timezone.utc) - datetime.fromisoformat(date_str)).days


class EmailWorker:

    def __init__(self):
        self.conn = get_connection()
        self.cur = self.conn.cursor()

    # -------------------------------------------------
    # Sélection des candidats à traiter
    # -------------------------------------------------
    def get_candidates(self):

        self.cur.execute("""
        SELECT id, siren, company, email, status, sent_at
        FROM contacts
        WHERE opt_out = 0
        """)

        rows = self.cur.fetchall()
        candidates = []

        for r in rows:

            status = r["status"]
            sent_at = r["sent_at"]

            if status in FINAL_STATES:
                continue

            if status == "sent" and days_since(sent_at) < 3:
                continue

            if status == "followup_1" and days_since(sent_at) < 7:
                continue

            candidates.append(r)

        return candidates

    # -------------------------------------------------
    # Envoi + machine à états
    # -------------------------------------------------
    def send(self, contact):

        cid = contact["id"]

        # relecture DB (anti course condition)
        self.cur.execute("SELECT status FROM contacts WHERE id = ?", (cid,))
        row = self.cur.fetchone()

        if not row:
            return

        current = row["status"]

        if current in FINAL_STATES:
            print(f"SKIP {contact['email']} (final: {current})")
            return

        print(f"PROCESS {contact['email']} | current={current}")

        # machine à états principale
        transitions = {
            "new": "queued",
            "queued": "sent",
            "sent": "followup_1",
            "followup_1": "followup_2"
        }

        next_status = transitions.get(current, "followup_2")

        # simulation événements email
        event = random.random()

        if event < 0.03:
            next_status = "hard_bounce"
        elif event < 0.06:
            next_status = "soft_bounce"
        elif event < 0.10 and current == "sent":
            next_status = "replied"

        # course critique check (sécurité)
        self.cur.execute("SELECT status FROM contacts WHERE id = ?", (cid,))
        latest = self.cur.fetchone()["status"]

        if latest in {"replied", "hard_bounce"}:
            print(f"SKIP {contact['email']} (state changed: {latest})")
            return

        # update unique état
        self.cur.execute("""
        UPDATE contacts
        SET status = ?, sent_at = ?
        WHERE id = ?
        """, (next_status, datetime.now(timezone.utc).isoformat(), cid))

        self.conn.commit()

        print(f"{current} -> {next_status} | {contact['email']}")

    # -------------------------------------------------
    # fermeture connexion
    # -------------------------------------------------
    def close(self):
        self.conn.close()