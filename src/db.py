import sqlite3
import os

DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "pipeline.db")
)


# ----------------------------
# CONNECTION
# ----------------------------
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ----------------------------
# INIT DB (VERSION CLEAN + PRO)
# ----------------------------
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # ------------------------
    # TABLE PRINCIPALE
    # ------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        siren TEXT,
        company TEXT,
        email TEXT,

        status TEXT DEFAULT 'new',
        sent_at TEXT,

        opt_out INTEGER DEFAULT 0,

        --CONTRAINTE ANTI-DUPLICATION MÉTIER
        UNIQUE(siren, email)
    )
    """)

    #
    # INDEX (PERF + PIPELINE)
    # 

    # accélère les filtres sender (status)
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_contacts_status
    ON contacts(status)
    """)

    # accélère recherche dédup / lookup
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_contacts_siren_email
    ON contacts(siren, email)
    """)

    # accélère opt-out filtering
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_contacts_opt_out
    ON contacts(opt_out)
    """)

    conn.commit()
    conn.close()


# ----------------------------
# INSERT CONTACTS SAFE
# ----------------------------
def insert_contacts(contacts):

    conn = get_connection()
    cur = conn.cursor()

    inserted = 0
    skipped = 0

    for c in contacts:

        siren = c["siren"]
        email = c["email"]
        company = c["company"]
        status = c["status"]

        # sécurité 1 : check existance
        cur.execute("""
        SELECT id FROM contacts
        WHERE siren = ? AND email = ?
        """, (siren, email))

        exists = cur.fetchone()

        if exists:
            skipped += 1
            continue

        # insertion
        cur.execute("""
        INSERT INTO contacts (
            siren,
            company,
            email,
            status
        )
        VALUES (?, ?, ?, ?)
        """, (
            siren,
            company,
            email,
            status
        ))

        inserted += 1

    conn.commit()
    conn.close()

    print(f"DB INSERTED: {inserted}, SKIPPED: {skipped}")


# 
# DEBUG UTIL
# 
def debug_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT id, siren, email, status, opt_out
    FROM contacts
    """)

    rows = cur.fetchall()

    print("\n=== DB STATE ===")
    for r in rows:
        print(dict(r))

    conn.close()