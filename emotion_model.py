# =========================================================
# MINDSENTINEL - EMOTION DETECTION MODEL
# =========================================================

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


# =========================================================
# TRAINING DATA
# =========================================================

texts = [

    # HAPPY
    "I am very happy today",
    "I feel great",
    "I am feeling wonderful",
    "I am excited",
    "Today is a beautiful day",
    "I feel good and positive",
    "I am enjoying my life",
    "I am feeling happy",
    "Everything is going well",
    "I feel amazing",

    # SAD
    "I am feeling sad",
    "I feel very lonely",
    "I am unhappy",
    "I feel depressed",
    "I am crying",
    "Nothing makes me happy",
    "I feel hopeless",
    "I feel very low",
    "I feel empty",
    "I don't feel good",

    # ANGRY
    "I am very angry",
    "This makes me angry",
    "I hate this situation",
    "I am frustrated",
    "I am irritated",
    "I feel angry and upset",
    "I am mad",
    "I feel furious",
    "This situation is annoying",
    "I am extremely frustrated",

    # FEAR / ANXIETY
    "I am scared",
    "I feel afraid",
    "I am frightened",
    "I am very worried",
    "I am nervous",
    "I feel unsafe",
    "I am anxious about everything",
    "I feel anxious",
    "I am panicking",
    "I am worried about my future",

    # NEUTRAL
    "I am okay",
    "I am fine",
    "Everything is normal",
    "Nothing special today",
    "I am doing my work",
    "Today is a normal day",
    "I don't feel anything special",
    "I am doing okay",
    "My day is normal",
    "Everything is fine"
]


labels = [

    # HAPPY
    "Happy", "Happy", "Happy", "Happy", "Happy",
    "Happy", "Happy", "Happy", "Happy", "Happy",

    # SAD
    "Sad", "Sad", "Sad", "Sad", "Sad",
    "Sad", "Sad", "Sad", "Sad", "Sad",

    # ANGRY
    "Angry", "Angry", "Angry", "Angry", "Angry",
    "Angry", "Angry", "Angry", "Angry", "Angry",

    # FEAR
    "Fear", "Fear", "Fear", "Fear", "Fear",
    "Fear", "Fear", "Fear", "Fear", "Fear",

    # NEUTRAL
    "Neutral", "Neutral", "Neutral", "Neutral", "Neutral",
    "Neutral", "Neutral", "Neutral", "Neutral", "Neutral"
]


# =========================================================
# TEXT VECTORIZATION
# =========================================================

vectorizer = TfidfVectorizer(
    lowercase=True,
    stop_words="english",
    ngram_range=(1, 2)
)


X = vectorizer.fit_transform(texts)


# =========================================================
# MACHINE LEARNING MODEL
# =========================================================

model = LogisticRegression(
    max_iter=1000
)


model.fit(X, labels)


# =========================================================
# EMOTION DETECTION FUNCTION
# =========================================================

def detect_emotion(text):

    """
    Detect emotion from user text.

    Returns:
        emotion
        confidence
    """

    if not text:

        return "Neutral", 0.0


    # Convert text to numerical features

    text_vector = vectorizer.transform([text])


    # Predict emotion

    prediction = model.predict(text_vector)[0]


    # Calculate confidence

    probabilities = model.predict_proba(text_vector)[0]

    confidence = max(probabilities) * 100


    return prediction, round(confidence, 2)


# =========================================================
# TEST MODEL
# =========================================================

if __name__ == "__main__":

    user_text = input(
        "Enter how you are feeling: "
    )


    emotion, confidence = detect_emotion(
        user_text
    )


    print("\n--------------------------------")

    print(
        "Detected Emotion:",
        emotion
    )

    print(
        "Confidence:",
        confidence,
        "%"
    )

    print("--------------------------------")