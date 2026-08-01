import os
import sqlite3
import logging

from src.db import init_db, DB_PATH, insert_contacts
from src.clean import process_data
from src.sender import EmailWorker
from src.enrichment import fetch_with_retry


logging.basicConfig(
    filename="pipeline.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)


def reset_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()


def enrichment():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT DISTINCT siren FROM contacts")

    rows = cur.fetchall()

    print("\n=== ENRICHMENT ===")

    for (siren,) in rows:
        print(fetch_with_retry(siren))

    conn.close()


def run():
    print("\n=== SENDER START ===")

    worker = EmailWorker()
    contacts = worker.get_candidates()

    print(f"DEBUG CANDIDATES: {len(contacts)}")

    if not contacts:
        print("No contacts to process")
        return

    for c in contacts:
        worker.send(c)

    worker.close()

    print("=== SENDER END ===")


def main():

    print("PIPELINE STARTED")

    reset_db()

    print("\nCLEANING STEP")

    stats, report, contacts = process_data("data/raw_contacts.csv")

    print("\nSTATS")
    print(stats)

    print("\nREPORT")
    for r in report:
        print("-", r)

    print("\nINSERTING CONTACTS")
    insert_contacts(contacts)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM contacts")
    print("DB CONTACTS:", cur.fetchone()[0])
    conn.close()

    print("\nENRICHMENT STEP")
    enrichment()

    print("\nSENDER INITIAL")
    run()

    print("\nSENDER FOLLOWUP")
    run()
    


if __name__ == "__main__":
    main()