from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

import os
import sqlite3

from database import (
    init_db,
    register_user,
    verify_user,
    save_assessment,
    get_latest_assessment,
    get_all_assessments,
    save_mood,
    get_mood_count,
    get_all_moods,
    get_recent_moods,
    get_mood_summary,
    save_emotion_result,
    get_latest_emotion,
    get_all_emotions,
    save_ai_conversation,
    get_ai_conversations
)

from emotion_model import detect_emotion


# =========================================================
# FLASK CONFIGURATION
# =========================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "MINDSENTINEL_SECRET_KEY",
    "mindsentinel-secret-key-2026"
)


# =========================================================
# INITIALIZE MAIN DATABASE
# =========================================================

init_db()


# =========================================================
# DISTRESS DATABASE CONFIGURATION
# =========================================================

DISTRESS_DATABASE = "distress.db"


def get_distress_connection():

    conn = sqlite3.connect(DISTRESS_DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


def init_distress_db():

    conn = get_distress_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS distress_records (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_email TEXT NOT NULL,

            assessment_score REAL DEFAULT 0,

            mood TEXT DEFAULT 'Neutral',

            emotion TEXT DEFAULT 'Neutral',

            distress_score REAL DEFAULT 0,

            risk_level TEXT DEFAULT 'LOW',

            trend TEXT DEFAULT 'Stable',

            early_warning TEXT DEFAULT '',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    conn.commit()
    conn.close()


init_distress_db()


# =========================================================
# DISTRESS DATABASE FUNCTIONS
# =========================================================

def save_distress_record(
    user_email,
    assessment_score,
    mood,
    emotion,
    distress_score,
    risk_level,
    trend,
    early_warning
):

    conn = get_distress_connection()

    conn.execute("""
        INSERT INTO distress_records
        (
            user_email,
            assessment_score,
            mood,
            emotion,
            distress_score,
            risk_level,
            trend,
            early_warning
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_email,
        assessment_score,
        mood,
        emotion,
        distress_score,
        risk_level,
        trend,
        early_warning
    ))

    conn.commit()
    conn.close()


def get_latest_distress(user_email):

    conn = get_distress_connection()

    result = conn.execute("""
        SELECT *
        FROM distress_records
        WHERE user_email = ?
        ORDER BY id DESC
        LIMIT 1
    """, (
        user_email,
    )).fetchone()

    conn.close()

    return result


def get_distress_history(user_email, limit=10):

    conn = get_distress_connection()

    results = conn.execute("""
        SELECT *
        FROM distress_records
        WHERE user_email = ?
        ORDER BY id DESC
        LIMIT ?
    """, (
        user_email,
        limit
    )).fetchall()

    conn.close()

    # Oldest → newest for chart
    return list(reversed(results))


# =========================================================
# HELPER FUNCTION
# =========================================================

def get_value(data, key, default=None):

    if data is None:
        return default

    try:
        return data[key]
    except (KeyError, TypeError, IndexError):
        return default


# =========================================================
# MOOD SCORE
# =========================================================

MOOD_SCORES = {

    "Happy": 10,
    "Good": 15,
    "Calm": 15,
    "Okay": 30,
    "Neutral": 35,

    "Sad": 65,
    "Anxious": 75,
    "Angry": 70,
    "Stressed": 80,

    "Fear": 85,
    "Afraid": 85,
    "Depressed": 90,
    "Very Sad": 85,
    "Distressed": 85

}


# =========================================================
# EMOTION SCORE
# =========================================================

EMOTION_SCORES = {

    "Happy": 10,
    "Stable": 10,

    "Neutral": 30,
    "Surprise": 35,

    "Sad": 65,
    "Angry": 70,
    "Disgust": 70,

    "Fear": 85,
    "Anxious": 80,
    "Stressed": 80,

    "Distressed": 85,
    "Critical": 95

}


# =========================================================
# ASSESSMENT SCORE → PERCENTAGE
# =========================================================

def assessment_to_percentage(score):

    try:

        score = float(score)

    except (TypeError, ValueError):

        return 0

    score = max(0, min(score, 27))

    return (score / 27) * 100


# =========================================================
# DYNAMIC DISTRESS CALCULATION
# =========================================================

def calculate_dynamic_distress(
    assessment_score,
    mood,
    emotion,
    previous_score=None
):

    # -----------------------------------------------------
    # Assessment
    # -----------------------------------------------------

    assessment_percentage = assessment_to_percentage(
        assessment_score
    )

    # -----------------------------------------------------
    # Mood
    # -----------------------------------------------------

    mood_score = MOOD_SCORES.get(
        str(mood).strip(),
        35
    )

    # -----------------------------------------------------
    # Emotion
    # -----------------------------------------------------

    emotion_score = EMOTION_SCORES.get(
        str(emotion).strip(),
        30
    )

    # -----------------------------------------------------
    # If previous record exists
    # -----------------------------------------------------

    if previous_score is not None:

        distress_score = (
            assessment_percentage * 0.45
            +
            mood_score * 0.20
            +
            emotion_score * 0.20
            +
            float(previous_score) * 0.15
        )

    # -----------------------------------------------------
    # First record
    # -----------------------------------------------------

    else:

        distress_score = (
            assessment_percentage * 0.55
            +
            mood_score * 0.25
            +
            emotion_score * 0.20
        )

    distress_score = round(
        max(0, min(distress_score, 100)),
        2
    )

    return distress_score


# =========================================================
# RISK LEVEL
# =========================================================

def get_dynamic_risk(distress_score):

    if distress_score < 30:

        return "LOW"

    elif distress_score < 50:

        return "MODERATE"

    elif distress_score < 70:

        return "HIGH"

    else:

        return "CRITICAL"


# =========================================================
# TREND
# =========================================================

def calculate_trend(
    current_score,
    previous_score
):

    if previous_score is None:

        return "Stable"

    difference = (
        float(current_score)
        -
        float(previous_score)
    )

    if difference > 5:

        return "Increasing"

    elif difference < -5:

        return "Decreasing"

    else:

        return "Stable"


# =========================================================
# EARLY WARNING
# =========================================================

def get_early_warning(
    distress_score,
    trend
):

    if distress_score >= 70:

        return (
            "High distress detected. "
            "Consider seeking support from a qualified "
            "mental-health professional or trusted person."
        )

    elif distress_score >= 50:

        return (
            "Your distress indicator is elevated. "
            "Consider taking a break and connecting "
            "with someone you trust."
        )

    elif trend == "Increasing":

        return (
            "Your distress indicator is showing an "
            "increasing trend. Keep monitoring your wellbeing."
        )

    else:

        return (
            "No immediate high-risk pattern detected. "
            "Continue monitoring your emotional wellbeing."
        )


# =========================================================
# UPDATE DYNAMIC DISTRESS
# =========================================================

def update_dynamic_distress(user_email):

    # -----------------------------------------------------
    # Latest assessment
    # -----------------------------------------------------

    assessment = get_latest_assessment(
        user_email
    )

    assessment_score = get_value(
        assessment,
        "score",
        0
    )

    # -----------------------------------------------------
    # Latest mood
    # -----------------------------------------------------

    recent_moods = get_recent_moods(
        user_email,
        1
    )

    if recent_moods:

        mood = get_value(
            recent_moods[0],
            "mood",
            "Neutral"
        )

    else:

        mood = "Neutral"

    # -----------------------------------------------------
    # Latest emotion
    # -----------------------------------------------------

    emotion_data = get_latest_emotion(
        user_email
    )

    emotion = get_value(
        emotion_data,
        "detected_emotion",
        "Neutral"
    )

    # -----------------------------------------------------
    # Previous distress record
    # -----------------------------------------------------

    previous = get_latest_distress(
        user_email
    )

    previous_score = get_value(
        previous,
        "distress_score",
        None
    )

    # -----------------------------------------------------
    # Calculate score
    # -----------------------------------------------------

    distress_score = calculate_dynamic_distress(

        assessment_score,

        mood,

        emotion,

        previous_score

    )

    # -----------------------------------------------------
    # Risk
    # -----------------------------------------------------

    risk_level = get_dynamic_risk(
        distress_score
    )

    # -----------------------------------------------------
    # Trend
    # -----------------------------------------------------

    trend = calculate_trend(
        distress_score,
        previous_score
    )

    # -----------------------------------------------------
    # Early warning
    # -----------------------------------------------------

    early_warning = get_early_warning(
        distress_score,
        trend
    )

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    save_distress_record(

        user_email,

        assessment_score,

        mood,

        emotion,

        distress_score,

        risk_level,

        trend,

        early_warning

    )

    return {

        "distress_score": distress_score,

        "risk_level": risk_level,

        "trend": trend,

        "early_warning": early_warning,

        "mood": mood,

        "emotion": emotion,

        "assessment_score": assessment_score

    }


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        # -------------------------------------------------
        # Validation
        # -------------------------------------------------

        if not name or not email or not password:

            flash(
                "Please fill in all required fields.",
                "error"
            )

            return render_template(
                "register.html"
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return render_template(
                "register.html"
            )

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "error"
            )

            return render_template(
                "register.html"
            )

        # -------------------------------------------------
        # Register
        # -------------------------------------------------

        success = register_user(
            name,
            email,
            password
        )

        if success:

            flash(
                "Registration successful. Please login.",
                "success"
            )

            return redirect(
                url_for("login")
            )

        else:

            flash(
                "This email is already registered.",
                "error"
            )

    return render_template(
        "register.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = verify_user(
            email,
            password
        )

        if user:

            session["user_email"] = user["email"]
            session["user_name"] = user["name"]

            flash(
                "Login successful. Welcome to MindSentinel!",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        else:

            flash(
                "Invalid email or password.",
                "error"
            )

    return render_template(
        "login.html"
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_email" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("login")
        )

    user_email = session["user_email"]

    user_name = session.get(
        "user_name",
        "User"
    )

    # -----------------------------------------------------
    # Latest assessment
    # -----------------------------------------------------

    latest_assessment = get_latest_assessment(
        user_email
    )

    score = get_value(
        latest_assessment,
        "score",
        0
    )

    risk = get_value(
        latest_assessment,
        "risk_level",
        "Not Available"
    )

    assessment_emotion = get_value(
        latest_assessment,
        "emotion",
        "Not Available"
    )

    # -----------------------------------------------------
    # Latest emotion
    # -----------------------------------------------------

    latest_emotion = get_latest_emotion(
        user_email
    )

    emotion = get_value(
        latest_emotion,
        "detected_emotion",
        assessment_emotion
    )

    # -----------------------------------------------------
    # Mood
    # -----------------------------------------------------

    mood_count = get_mood_count(
        user_email
    )

    recent_moods = get_recent_moods(
        user_email,
        7
    )

    mood_summary = get_mood_summary(
        user_email
    )

    # -----------------------------------------------------
    # Dynamic distress
    # -----------------------------------------------------

    latest_distress = get_latest_distress(
        user_email
    )

    if latest_distress:

        distress_score = get_value(
            latest_distress,
            "distress_score",
            0
        )

        distress_risk = get_value(
            latest_distress,
            "risk_level",
            "LOW"
        )

        distress_trend = get_value(
            latest_distress,
            "trend",
            "Stable"
        )

        early_warning = get_value(
            latest_distress,
            "early_warning",
            "Continue monitoring your wellbeing."
        )

    else:

        distress_score = 0
        distress_risk = "NOT AVAILABLE"
        distress_trend = "Stable"

        early_warning = (
            "Complete an assessment and mood check "
            "to generate your dynamic distress indicator."
        )

    # -----------------------------------------------------
    # Distress history
    # -----------------------------------------------------

    distress_history = get_distress_history(
        user_email,
        10
    )

    # -----------------------------------------------------
    # AI conversations
    # -----------------------------------------------------

    ai_conversations = get_ai_conversations(
        user_email
    )

    return render_template(

        "dashboard.html",

        user_name=user_name,

        distress_score=distress_score,

        distress_risk=distress_risk,

        distress_trend=distress_trend,

        early_warning=early_warning,

        score=score,

        risk=risk,

        emotion=emotion,

        mood_count=mood_count,

        distress_history=distress_history,

        recent_moods=recent_moods,

        mood_summary=mood_summary,

        ai_conversations=ai_conversations

    )


# =========================================================
# ASSESSMENT
# =========================================================

@app.route(
    "/assessment",
    methods=["GET", "POST"]
)
def assessment():

    if "user_email" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        total_score = 0

        # -------------------------------------------------
        # 9 Questions
        # -------------------------------------------------

        for i in range(1, 10):

            value = request.form.get(
                f"q{i}",
                "0"
            )

            try:

                value = int(value)

            except (ValueError, TypeError):

                value = 0

            value = max(
                0,
                min(value, 3)
            )

            total_score += value

        # -------------------------------------------------
        # Risk classification
        # -------------------------------------------------

        if total_score <= 7:

            risk_level = "LOW"
            emotion = "Stable"

        elif total_score <= 14:

            risk_level = "MODERATE"
            emotion = "Anxious"

        elif total_score <= 21:

            risk_level = "HIGH"
            emotion = "Distressed"

        else:

            risk_level = "VERY HIGH"
            emotion = "Critical"

        # -------------------------------------------------
        # Save assessment
        # -------------------------------------------------

        save_assessment(

            session["user_email"],

            total_score,

            risk_level,

            emotion

        )

        # -------------------------------------------------
        # Update distress
        # -------------------------------------------------

        update_dynamic_distress(
            session["user_email"]
        )

        flash(
            "Assessment completed successfully.",
            "success"
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "assessment.html"
    )


# =========================================================
# ASSESSMENT HISTORY
# =========================================================

@app.route("/history")
def history():

    if "user_email" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("login")
        )

    assessments = get_all_assessments(
        session["user_email"]
    )

    return render_template(
        "history.html",
        assessments=assessments
    )


# =========================================================
# MOOD TRACKER
# =========================================================

@app.route(
    "/mood",
    methods=["GET", "POST"]
)
def mood():

    if "user_email" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        selected_mood = request.form.get(
            "mood",
            ""
        ).strip()

        if not selected_mood:

            flash(
                "Please select a mood.",
                "error"
            )

            return redirect(
                url_for("mood")
            )

        save_mood(

            session["user_email"],

            selected_mood

        )

        # -------------------------------------------------
        # Update distress
        # -------------------------------------------------

        update_dynamic_distress(
            session["user_email"]
        )

        flash(
            "Your mood has been recorded.",
            "success"
        )

        return redirect(
            url_for("mood_history")
        )

    return render_template(
        "mood.html"
    )


# =========================================================
# MOOD HISTORY
# =========================================================

@app.route("/mood-history")
def mood_history():

    if "user_email" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("login")
        )

    moods = get_all_moods(
        session["user_email"]
    )

    mood_summary = get_mood_summary(
        session["user_email"]
    )

    return render_template(

        "mood_history.html",

        moods=moods,

        mood_summary=mood_summary

    )


# =========================================================
# EMOTION DETECTION
# =========================================================

@app.route(
    "/emotion",
    methods=["GET", "POST"]
)
def emotion():

    if "user_email" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("login")
        )

    result = None

    if request.method == "POST":

        text = request.form.get(
            "text",
            ""
        ).strip()

        if not text:

            flash(
                "Please enter some text.",
                "error"
            )

            return render_template(
                "emotion.html"
            )

        try:

            detected_emotion, confidence = detect_emotion(
                text
            )

        except Exception as error:

            print(
                "Emotion detection error:",
                error
            )

            detected_emotion = "Neutral"
            confidence = 0

        try:

            confidence = float(
                confidence
            )

        except (ValueError, TypeError):

            confidence = 0

        # -------------------------------------------------
        # Normalize confidence
        # -------------------------------------------------

        if confidence <= 1:

            confidence = confidence * 100

        confidence = round(
            max(0, min(confidence, 100)),
            2
        )

        # -------------------------------------------------
        # Save result
        # -------------------------------------------------

        save_emotion_result(

            session["user_email"],

            text,

            detected_emotion,

            confidence

        )

        # -------------------------------------------------
        # Update distress
        # -------------------------------------------------

        update_dynamic_distress(
            session["user_email"]
        )

        result = {

            "emotion": detected_emotion,

            "confidence": confidence,

            "text": text

        }

    return render_template(

        "emotion.html",

        result=result

    )


# =========================================================
# EMOTION HISTORY
# =========================================================

@app.route("/emotion-history")
def emotion_history():

    if "user_email" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("login")
        )

    emotions = get_all_emotions(
        session["user_email"]
    )

    return render_template(

        "emotion_history.html",

        emotions=emotions

    )


# =========================================================
# AI SUPPORT
# =========================================================

@app.route(
    "/ai-support",
    methods=["GET", "POST"]
)
def ai_support():

    if "user_email" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("login")
        )

    response = None
    detected_emotion = "Neutral"
    confidence = 0

    if request.method == "POST":

        message = request.form.get(
            "message",
            ""
        ).strip()

        if not message:

            flash(
                "Please enter a message.",
                "error"
            )

            return render_template(
                "ai_support.html"
            )

        # -------------------------------------------------
        # Emotion detection
        # -------------------------------------------------

        try:

            detected_emotion, confidence = detect_emotion(
                message
            )

        except Exception as error:

            print(
                "AI support emotion error:",
                error
            )

            detected_emotion = "Neutral"
            confidence = 0

        try:

            confidence = float(
                confidence
            )

        except (ValueError, TypeError):

            confidence = 0

        if confidence <= 1:

            confidence = confidence * 100

        confidence = round(
            max(0, min(confidence, 100)),
            2
        )

        # -------------------------------------------------
        # Dynamic supportive response
        # -------------------------------------------------

        emotion_lower = str(
            detected_emotion
        ).lower()

        if any(
            word in emotion_lower
            for word in [
                "critical",
                "distressed",
                "fear"
            ]
        ):

            response = (
                "I'm sorry that you are going through "
                "a difficult moment. Please consider "
                "connecting with a trusted person or "
                "qualified mental-health professional. "
                "If you are in immediate danger, contact "
                "your local emergency service."
            )

        elif any(
            word in emotion_lower
            for word in [
                "sad",
                "depressed"
            ]
        ):

            response = (
                "It sounds like you may be going through "
                "a difficult time. Try taking a short break, "
                "doing some slow breathing, and talking to "
                "someone you trust."
            )

        elif any(
            word in emotion_lower
            for word in [
                "angry",
                "stressed",
                "anxious"
            ]
        ):

            response = (
                "It seems that you may be feeling stressed "
                "or overwhelmed. Take a few slow breaths, "
                "step away from the situation if possible, "
                "and consider speaking with someone you trust."
            )

        elif "happy" in emotion_lower:

            response = (
                "It's great to see a positive emotional signal. "
                "Keep doing activities that support your wellbeing "
                "and continue checking in with yourself."
            )

        else:

            response = (
                "Thank you for sharing how you feel. "
                "Remember to take care of yourself, "
                "maintain healthy routines, and reach out "
                "to trusted people when you need support."
            )

        # -------------------------------------------------
        # Save emotion
        # -------------------------------------------------

        save_emotion_result(

            session["user_email"],

            message,

            detected_emotion,

            confidence

        )

        # -------------------------------------------------
        # Save AI conversation
        # -------------------------------------------------

        save_ai_conversation(

            session["user_email"],

            message,

            response,

            detected_emotion,

            confidence

        )

        # -------------------------------------------------
        # Update distress
        # -------------------------------------------------

        update_dynamic_distress(
            session["user_email"]
        )

    return render_template(

        "ai_support.html",

        response=response,

        detected_emotion=detected_emotion,

        confidence=confidence

    )


# =========================================================
# RESOURCES
# =========================================================

@app.route("/resources")
def resources():

    if "user_email" not in session:

        flash(
            "Please login first.",
            "error"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "resources.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out successfully.",
        "success"
    )

    return redirect(
        url_for("home")
    )


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "index.html"
    ), 404


@app.errorhandler(500)
def internal_server_error(error):

    return (
        """
        <div style="
            font-family: Arial;
            text-align: center;
            padding: 60px;
        ">

            <h1>MindSentinel</h1>

            <h2>Something went wrong</h2>

            <p>
                Please return to the dashboard
                and try again.
            </p>

            <a href="/dashboard">
                Back to Dashboard
            </a>

        </div>
        """,
        500
    )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )