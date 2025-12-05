# predict_hashtag.py
# Usage: python predict_hashtag.py "#cyberpunk"

import sys
import joblib
import numpy as np
from scipy.sparse import hstack
from google_scraper import search_reddit_by_hashtag
from features import build_feature_matrix, TextVectorizer, clickbait_score

MODEL_PATH = "misinfo_logreg_model.joblib"
VECT_PATH = "tfidf_vectorizer.joblib"

def load_model():
    clf = joblib.load(MODEL_PATH)
    tfidf = joblib.load(VECT_PATH)
    vec = TextVectorizer()
    vec.tfidf = tfidf
    return clf, vec

def explain_prediction(prob, record):
    # Simple explanation: show clickbait score and matching keywords
    text = " ".join(filter(None, [record.get("title",""), record.get("snippet","")]))
    cb = clickbait_score(text)
    keywords = [k for k in ["confirmed","leaked","official","proof","cure","exposed","fake","scam","rumor"] if k in text.lower()]
    return {"clickbait": round(cb,3), "keywords": keywords}

def main():
    if len(sys.argv) < 2:
        print("Usage: python predict_hashtag.py '#hashtag'")
        sys.exit(1)
    hashtag = sys.argv[1]
    print("Searching Google for:", hashtag)
    records = search_reddit_by_hashtag(hashtag, num_results=10)
    if not records:
        print("No search results returned.")
        return

    clf, vec = load_model()
    X_text, X_eng, _ = build_feature_matrix(records, vectorizer=vec)
    X = hstack([X_text, X_eng])
    probs = clf.predict_proba(X)[:,1]  # probability of label==1

    # Print results
    for i, rec in enumerate(records):
        p = probs[i]*100
        explanation = explain_prediction(prob=probs[i], record=rec)
        print(f"\nRank #{rec.get('rank')}: {rec.get('title')}")
        print(f"URL: {rec.get('url')}")
        print(f"Subreddit: {rec.get('subreddit')}, Google rank: {rec.get('rank')}")
        print(f"Snippet: {rec.get('snippet')[:250]}")
        print(f"Estimated misinfo likelihood: {p:.1f}%")
        print(f"Explanation: clickbait={explanation['clickbait']}, keywords={explanation['keywords']}")
        print("-"*60)

if __name__ == "__main__":
    main()
