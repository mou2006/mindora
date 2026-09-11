import sqlite3


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

DATABASE = "mindsentinel.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    conn = get_db_connection()

    # -----------------------------------------------------
    # USERS
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            created_at
            TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    # -----------------------------------------------------
    # ASSESSMENTS
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS assessments (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_email TEXT NOT NULL,

            score INTEGER NOT NULL,

            risk_level TEXT NOT NULL,

            emotion TEXT NOT NULL,

            created_at
            TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    # -----------------------------------------------------
    # MOODS
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS moods (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_email TEXT NOT NULL,

            mood TEXT NOT NULL,

            created_at
            TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    # -----------------------------------------------------
    # EMOTION LOGS
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS emotion_logs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_email TEXT NOT NULL,

            input_text TEXT NOT NULL,

            detected_emotion TEXT NOT NULL,

            confidence REAL NOT NULL,

            created_at
            TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    # -----------------------------------------------------
    # AI CONVERSATIONS
    # -----------------------------------------------------

    conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_conversations (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_email TEXT NOT NULL,

            user_message TEXT NOT NULL,

            ai_response TEXT NOT NULL,

            detected_emotion TEXT,

            confidence REAL,

            created_at
            TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    conn.commit()

    conn.close()


# =========================================================
# USER REGISTRATION
# =========================================================

def register_user(
    name,
    email,
    password
):

    conn = get_db_connection()

    try:

        conn.execute("""
            INSERT INTO users
            (
                name,
                email,
                password
            )

            VALUES (?, ?, ?)
        """, (
            name,
            email,
            password
        ))

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        conn.close()


# =========================================================
# VERIFY USER
# =========================================================

def verify_user(
    email,
    password
):

    conn = get_db_connection()

    result = conn.execute("""
        SELECT
            id,
            name,
            email
        FROM users

        WHERE email = ?
        AND password = ?

        LIMIT 1
    """, (
        email,
        password
    )).fetchone()

    conn.close()

    return result


# =========================================================
# SAVE ASSESSMENT
# =========================================================

def save_assessment(
    user_email,
    score,
    risk_level,
    emotion
):

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO assessments
        (
            user_email,
            score,
            risk_level,
            emotion
        )

        VALUES (?, ?, ?, ?)
    """, (
        user_email,
        score,
        risk_level,
        emotion
    ))

    conn.commit()

    conn.close()


# =========================================================
# GET LATEST ASSESSMENT
# =========================================================

def get_latest_assessment(
    user_email
):

    conn = get_db_connection()

    result = conn.execute("""
        SELECT
            id,
            score,
            risk_level,
            emotion,
            created_at

        FROM assessments

        WHERE user_email = ?

        ORDER BY id DESC

        LIMIT 1
    """, (
        user_email,
    )).fetchone()

    conn.close()

    return result


# =========================================================
# GET ALL ASSESSMENTS
# =========================================================

def get_all_assessments(
    user_email
):

    conn = get_db_connection()

    results = conn.execute("""
        SELECT
            id,
            score,
            risk_level,
            emotion,
            created_at

        FROM assessments

        WHERE user_email = ?

        ORDER BY id DESC
    """, (
        user_email,
    )).fetchall()

    conn.close()

    return results


# =========================================================
# SAVE MOOD
# =========================================================

def save_mood(
    user_email,
    mood
):

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO moods
        (
            user_email,
            mood
        )

        VALUES (?, ?)
    """, (
        user_email,
        mood
    ))

    conn.commit()

    conn.close()


# =========================================================
# GET MOOD COUNT
# =========================================================

def get_mood_count(
    user_email
):

    conn = get_db_connection()

    result = conn.execute("""
        SELECT
            COUNT(*) AS count

        FROM moods

        WHERE user_email = ?
    """, (
        user_email,
    )).fetchone()

    conn.close()

    return result["count"]


# =========================================================
# GET ALL MOODS
# =========================================================

def get_all_moods(
    user_email
):

    conn = get_db_connection()

    results = conn.execute("""
        SELECT
            id,
            mood,
            created_at

        FROM moods

        WHERE user_email = ?

        ORDER BY id DESC
    """, (
        user_email,
    )).fetchall()

    conn.close()

    return results


# =========================================================
# SAVE EMOTION RESULT
# =========================================================

def save_emotion_result(
    user_email,
    input_text,
    detected_emotion,
    confidence
):

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO emotion_logs
        (
            user_email,
            input_text,
            detected_emotion,
            confidence
        )

        VALUES (?, ?, ?, ?)
    """, (
        user_email,
        input_text,
        detected_emotion,
        confidence
    ))

    conn.commit()

    conn.close()


# =========================================================
# GET LATEST EMOTION
# =========================================================

def get_latest_emotion(
    user_email
):

    conn = get_db_connection()

    result = conn.execute("""
        SELECT
            detected_emotion,
            confidence,
            input_text,
            created_at

        FROM emotion_logs

        WHERE user_email = ?

        ORDER BY id DESC

        LIMIT 1
    """, (
        user_email,
    )).fetchone()

    conn.close()

    return result


# =========================================================
# GET ALL EMOTIONS
# =========================================================

def get_all_emotions(
    user_email
):

    conn = get_db_connection()

    results = conn.execute("""
        SELECT
            detected_emotion,
            confidence,
            input_text,
            created_at

        FROM emotion_logs

        WHERE user_email = ?

        ORDER BY id DESC
    """, (
        user_email,
    )).fetchall()

    conn.close()

    return results


# =========================================================
# GET RECENT MOODS
# =========================================================

def get_recent_moods(
    user_email,
    limit=7
):

    conn = get_db_connection()

    results = conn.execute("""
        SELECT
            mood,
            created_at

        FROM moods

        WHERE user_email = ?

        ORDER BY id DESC

        LIMIT ?
    """, (
        user_email,
        limit
    )).fetchall()

    conn.close()

    return results


# =========================================================
# GET MOOD SUMMARY
# =========================================================

def get_mood_summary(
    user_email
):

    conn = get_db_connection()

    results = conn.execute("""
        SELECT
            mood,
            COUNT(*) AS total

        FROM moods

        WHERE user_email = ?

        GROUP BY mood

        ORDER BY total DESC
    """, (
        user_email,
    )).fetchall()

    conn.close()

    return results


# =========================================================
# SAVE AI CONVERSATION
# =========================================================

def save_ai_conversation(
    user_email,
    user_message,
    ai_response,
    detected_emotion,
    confidence
):

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO ai_conversations
        (
            user_email,
            user_message,
            ai_response,
            detected_emotion,
            confidence
        )

        VALUES (?, ?, ?, ?, ?)
    """, (
        user_email,
        user_message,
        ai_response,
        detected_emotion,
        confidence
    ))

    conn.commit()

    conn.close()


# =========================================================
# GET AI CONVERSATIONS
# =========================================================

def get_ai_conversations(
    user_email
):

    conn = get_db_connection()

    results = conn.execute("""
        SELECT
            id,
            user_message,
            ai_response,
            detected_emotion,
            confidence,
            created_at

        FROM ai_conversations

        WHERE user_email = ?

        ORDER BY id DESC
    """, (
        user_email,
    )).fetchall()

    conn.close()

    return results