# features.py
# Feature extraction: TF-IDF + engineered features.

import re
import math
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# Subreddit risk mapping (extendable)
SUBREDDIT_RISK = {
    "conspiracy": 1.0,
    "the_donald": 0.9,
    "politics": 0.6,
    "news": 0.3,
    "science": 0.1,
    # default for unknown subreddit
    "__default__": 0.4
}

# keywords indicating possible misinformation
MISINFO_KEYWORDS = [
    "confirmed", "leaked", "official", "exposed", "cure", "proof", "guaranteed",
    "secret", "unreleased", "tomorrow", "rumor", "scam", "fake", "hoax",
    "they don't want you", "wake up", "conspiracy"
]

def clickbait_score(text: str) -> float:
    """
    Simple clickbait heuristics:
    - fraction of ALL CAPS words
    - exclamation density
    - presence of sensational words
    """
    if not text:
        return 0.0
    words = re.findall(r"[A-Za-z']+", text)
    if not words:
        return 0.0
    all_caps = sum(1 for w in words if w.isupper() and len(w) > 1)
    cap_frac = all_caps / len(words)
    exclam = text.count("!")
    exclam_score = min(1.0, exclam / 3.0)
    sens_words = sum(1 for kw in MISINFO_KEYWORDS if kw in text.lower())
    sens_score = min(1.0, sens_words / 3.0)
    return 0.5 * cap_frac + 0.3 * exclam_score + 0.2 * sens_score

def keyword_flags(text: str):
    text_l = text.lower() if text else ""
    flags = [1 if kw in text_l else 0 for kw in MISINFO_KEYWORDS]
    return flags

def subreddit_risk(subreddit: str):
    if not subreddit:
        return SUBREDDIT_RISK["__default__"]
    return SUBREDDIT_RISK.get(subreddit.lower(), SUBREDDIT_RISK["__default__"])

def rank_score(rank: int):
    if not rank or rank <= 0:
        return 0.0
    return 1.0 / rank

# TF-IDF wrapper (trained during training)
class TextVectorizer:
    def __init__(self):
        self.tfidf = TfidfVectorizer(ngram_range=(1,2), max_features=4000)

    def fit(self, texts):
        self.tfidf.fit(texts)
        return self

    def transform(self, texts):
        return self.tfidf.transform(texts)

    def save(self, path):
        joblib.dump(self.tfidf, path)

    def load(self, path):
        self.tfidf = joblib.load(path)
        return self

def build_feature_matrix(records, vectorizer=None):
    """
    records: list of dicts with keys: title, snippet, url, subreddit, rank
    returns: (X_text_sparse, X_engineered_np)
    """
    texts = []
    for r in records:
        text = " ".join(filter(None, [r.get("title",""), r.get("snippet","")]))
        texts.append(text)

    if vectorizer is None:
        vectorizer = TextVectorizer()
        vectorizer.fit(texts)

    X_text = vectorizer.transform(texts)

    # engineered features
    eng = []
    for i, r in enumerate(records):
        text = texts[i]
        cb = clickbait_score(text)
        kw_flags = keyword_flags(text)
        sr = subreddit_risk(r.get("subreddit"))
        rs = rank_score(r.get("rank"))
        # date feature is not always present; ignore for now or add later
        eng_row = [cb, sr, rs] + kw_flags
        eng.append(eng_row)
    X_eng = np.array(eng, dtype=float)
    return X_text, X_eng, vectorizer
