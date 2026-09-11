import sqlite3


DB_NAME = "distress.db"


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_distress_db():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS distress_records (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_email TEXT NOT NULL,

            assessment_score REAL,

            mood TEXT,

            emotion TEXT,

            distress_score REAL,

            risk_level TEXT,

            trend TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()

    conn.close()


# =========================================================
# SAVE DISTRESS RECORD
# =========================================================

def save_distress_record(
    user_email,
    assessment_score,
    mood,
    emotion,
    distress_score,
    risk_level,
    trend
):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO distress_records
        (
            user_email,
            assessment_score,
            mood,
            emotion,
            distress_score,
            risk_level,
            trend
        )

        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,

        (
            user_email,
            assessment_score,
            mood,
            emotion,
            distress_score,
            risk_level,
            trend
        )
    )

    conn.commit()

    conn.close()


# =========================================================
# GET LATEST DISTRESS
# =========================================================

def get_latest_distress(user_email):

    conn = sqlite3.connect(DB_NAME)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM distress_records

        WHERE user_email = ?

        ORDER BY id DESC

        LIMIT 1
        """,

        (user_email,)
    )

    row = cursor.fetchone()

    conn.close()

    if row:
        return dict(row)

    return None


# =========================================================
# GET DISTRESS HISTORY
# =========================================================

def get_distress_history(
    user_email,
    limit=7
):

    conn = sqlite3.connect(DB_NAME)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM distress_records

        WHERE user_email = ?

        ORDER BY id DESC

        LIMIT ?
        """,

        (
            user_email,
            limit
        )
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]