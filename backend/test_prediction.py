# test_prediction.py
import joblib
from scipy.sparse import hstack
from backend.features import build_feature_matrix, TextVectorizer
from backend.google_scraper import search_reddit_by_hashtag

posts = search_reddit_by_hashtag("#politics", num_results=3)

# Load model
clf = joblib.load("backend/misinfo_logreg_model.joblib")
vec = TextVectorizer()
vec.tfidf = joblib.load("backend/tfidf_vectorizer.joblib")

# Build features
X_text, X_eng, _ = build_feature_matrix(posts, vectorizer=vec)
X = hstack([X_text, X_eng])

# Predict probabilities
probs = clf.predict_proba(X)[:,1]

for i, p in enumerate(posts):
    print(f"Title: {p['title']}")
    print(f"Predicted likelihood of misinformation: {probs[i]*100:.2f}%")
    print("-"*50)
