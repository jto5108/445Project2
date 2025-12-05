# train_model.py
# Trains a LogisticRegression model on synthetic data (demo).
# Replace synthetic data with human-labeled CSV for production.

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion
from scipy.sparse import hstack
from features import build_feature_matrix, TextVectorizer

# Create synthetic training examples (title + snippet) labeled by heuristics
POSITIVE_TITLES = [
    "New study CONFIRMS coffee cures cancer",
    "Official leak: Tesla Model X release TOMORROW!!!",
    "They don't want you to know this secret to lose weight",
    "Proof that the vaccine is fake",
    "X company exposed as a scam"
]

NEGATIVE_TITLES = [
    "How do I choose a car for commuting?",
    "Best graphics settings for Cyberpunk 2077",
    "Fan art release thread",
    "Help diagnosing a small oil leak",
    "Community discussion: favorite game soundtrack"
]

def make_records(titles, label):
    recs = []
    for t in titles:
        recs.append({
            "title": t,
            "snippet": t,  # for synthetic, use same
            "url": "",
            "subreddit": "news" if label==1 else "general",
            "rank": 1
        })
    labels = [label]*len(titles)
    return recs, labels

def main():
    pos_recs, pos_labels = make_records(POSITIVE_TITLES, 1)
    neg_recs, neg_labels = make_records(NEGATIVE_TITLES, 0)
    records = pos_recs + neg_recs
    y = np.array(pos_labels + neg_labels)

    # Build vectorizer and features
    X_text, X_eng, vectorizer = build_feature_matrix(records, vectorizer=None)
    # Combine sparse text features with dense engineered features
    X = hstack([X_text, X_eng])

    # Train logistic regression
    clf = LogisticRegression(max_iter=1000)
    clf.fit(X, y)

    # Save model and vectorizer
    joblib.dump(clf, "misinfo_logreg_model.joblib")
    joblib.dump(vectorizer.tfidf, "tfidf_vectorizer.joblib")
    print("Trained demo model saved: misinfo_logreg_model.joblib")
    print("TF-IDF saved: tfidf_vectorizer.joblib")

if __name__ == "__main__":
    main()
