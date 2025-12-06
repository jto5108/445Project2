# test_features.py
from backend.features import build_feature_matrix
from backend.google_scraper import search_reddit_by_hashtag

posts = search_reddit_by_hashtag("#politics", num_results=3)
X_text, X_eng, vec = build_feature_matrix(posts)

print("TF-IDF shape:", X_text.shape)
print("Other features shape:", X_eng.shape)
