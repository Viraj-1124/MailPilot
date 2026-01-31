from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def subject_similarity(subject1, subject2):
    # ---------- Safety checks ----------
    if not subject1 or not subject2:
        return 0.0

    subject1 = subject1.strip().lower()
    subject2 = subject2.strip().lower()

    if len(subject1) < 3 or len(subject2) < 3:
        return 0.0

    texts = [subject1, subject2]

    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf = vectorizer.fit_transform(texts)

        similarity = cosine_similarity(
            tfidf[0:1], tfidf[1:2]
        )[0][0]

        return similarity * 100

    except ValueError:
        # Handles empty vocabulary cases safely
        return 0.0