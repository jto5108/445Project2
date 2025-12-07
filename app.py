#!/usr/bin/env python3
"""
Flask web application for ClipCheck - Reddit Misinformation Detection
"""
import os
import sys
from flask import Flask, render_template, request, jsonify
import joblib
import numpy as np
from scipy.sparse import hstack
from datetime import datetime, timedelta
import hashlib

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.google_scraper import search_reddit_by_hashtag
from backend.features import build_feature_matrix, TextVectorizer, clickbait_score

app = Flask(__name__)

# Model paths
MODEL_PATH = os.path.join("backend", "misinfo_logreg_model.joblib")
VECT_PATH = os.path.join("backend", "tfidf_vectorizer.joblib")

# Global model cache
_model_cache = {}

# Cache for scraping results (hashtag -> {data, timestamp})
# Results expire after 1 hour
_scrape_cache = {}
CACHE_EXPIRY_HOURS = 1

def get_cached_scrape(hashtag):
    """Get cached scraping results if available and not expired"""
    if hashtag in _scrape_cache:
        cache_entry = _scrape_cache[hashtag]
        age = datetime.now() - cache_entry['timestamp']
        if age < timedelta(hours=CACHE_EXPIRY_HOURS):
            return cache_entry['data']
    return None

def set_cached_scrape(hashtag, data):
    """Cache scraping results with timestamp"""
    _scrape_cache[hashtag] = {
        'data': data,
        'timestamp': datetime.now()
    }

def load_model():
    """Load the trained model and vectorizer"""
    if 'clf' not in _model_cache:
        try:
            clf = joblib.load(MODEL_PATH)
            tfidf = joblib.load(VECT_PATH)
            vec = TextVectorizer()
            vec.tfidf = tfidf
            _model_cache['clf'] = clf
            _model_cache['vec'] = vec
        except FileNotFoundError:
            raise FileNotFoundError(
                "Model files not found. Please run 'python backend/train_model.py' first."
            )
    return _model_cache['clf'], _model_cache['vec']


@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Real-time analysis: Scrape, train, predict - all on-demand with fresh data.
    No pre-trained model needed - everything happens when user clicks analyze.
    """
    try:
        data = request.get_json()
        if not data or 'hashtag' not in data:
            return jsonify({"error": "No hashtag provided"}), 400

        hashtag = data['hashtag'].strip()
        if not hashtag:
            return jsonify({"error": "Please provide a hashtag"}), 400

        if not hashtag.startswith('#'):
            hashtag = '#' + hashtag

        app.logger.info(f"=== Starting real-time analysis for: {hashtag} ===")

        # STEP 1: Scrape user's requested posts (with caching)
        app.logger.info("STEP 1: Scraping user's requested posts...")
        cached_user_posts = get_cached_scrape(hashtag)
        if cached_user_posts:
            user_posts = cached_user_posts
            app.logger.info(f"Using cached results for {hashtag}")
        else:
            user_posts = search_reddit_by_hashtag(hashtag, num_results=10)
            if user_posts:
                set_cached_scrape(hashtag, user_posts)
                app.logger.info(f"Scraped and cached {len(user_posts)} posts for {hashtag}")

        if not user_posts:
            return jsonify({"error": f"No Reddit posts found for {hashtag}. Try another hashtag."}), 404

        app.logger.info(f"Found {len(user_posts)} posts for user query")

        # STEP 2: Scrape fresh training data (with caching)
        app.logger.info("STEP 2: Scraping fresh training data...")
        training_posts = []
        training_labels = []

        # Scrape misinformation-prone hashtags for positive examples
        for train_tag in ["#conspiracy", "#leaked", "#exposed"]:
            try:
                cached_posts = get_cached_scrape(train_tag)
                if cached_posts:
                    posts = cached_posts
                    app.logger.info(f"  Using cached data for {train_tag}")
                else:
                    posts = search_reddit_by_hashtag(train_tag, num_results=10)
                    if posts:
                        set_cached_scrape(train_tag, posts)
                        app.logger.info(f"  Scraped and cached {len(posts)} from {train_tag}")
                training_posts.extend(posts)
                training_labels.extend([1] * len(posts))  # Label as misinformation
            except Exception as e:
                app.logger.warning(f"  Failed to scrape {train_tag}: {e}")

        # Scrape normal hashtags for negative examples
        for train_tag in ["#gaming", "#technology", "#help"]:
            try:
                cached_posts = get_cached_scrape(train_tag)
                if cached_posts:
                    posts = cached_posts
                    app.logger.info(f"  Using cached data for {train_tag}")
                else:
                    posts = search_reddit_by_hashtag(train_tag, num_results=10)
                    if posts:
                        set_cached_scrape(train_tag, posts)
                        app.logger.info(f"  Scraped and cached {len(posts)} from {train_tag}")
                training_posts.extend(posts)
                training_labels.extend([0] * len(posts))  # Label as normal
            except Exception as e:
                app.logger.warning(f"  Failed to scrape {train_tag}: {e}")

        # If we got NO training data at all, use minimal fallback
        if len(training_posts) == 0:
            app.logger.warning("No training data scraped - using minimal fallback")
            training_posts = [
                {"title": "BREAKING NEWS: Miracle cure CONFIRMED!!!", "snippet": "They don't want you to know", "subreddit": "conspiracy", "rank": 1},
                {"title": "Secret documents LEAKED - government coverup", "snippet": "PROOF inside", "subreddit": "conspiracy", "rank": 1},
                {"title": "How to build a gaming PC", "snippet": "Discussion and advice", "subreddit": "buildapc", "rank": 1},
                {"title": "Best monitor for productivity?", "snippet": "Looking for recommendations", "subreddit": "monitors", "rank": 1},
            ]
            training_labels = [1, 1, 0, 0]

        training_labels = np.array(training_labels)
        app.logger.info(f"Total training samples: {len(training_posts)}")

        # STEP 3: Train model on fresh data
        app.logger.info("STEP 3: Training model on fresh data...")
        X_text, X_eng, vectorizer = build_feature_matrix(training_posts, vectorizer=None)
        X_all = hstack([X_text, X_eng])

        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import train_test_split

        # Split data for validation
        if len(training_posts) >= 10:
            X_train, X_test, y_train, y_test = train_test_split(
                X_all, training_labels, test_size=0.2, random_state=42, stratify=training_labels
            )
            clf = LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')
            clf.fit(X_train, y_train)

            train_acc = clf.score(X_train, y_train)
            test_acc = clf.score(X_test, y_test)
            app.logger.info(f"Model trained - Train accuracy: {train_acc * 100:.1f}%, Test accuracy: {test_acc * 100:.1f}%")

            # Retrain on all data for prediction
            clf.fit(X_all, training_labels)
        else:
            # Not enough data for split, just train on all
            clf = LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')
            clf.fit(X_all, training_labels)
            train_acc = clf.score(X_all, training_labels)
            test_acc = train_acc
            app.logger.info(f"Model trained - accuracy: {train_acc * 100:.1f}% (no test split - insufficient data)")

        # STEP 4: Predict on user's posts
        app.logger.info("STEP 4: Predicting misinformation likelihood...")
        X_text_user, X_eng_user, _ = build_feature_matrix(user_posts, vectorizer=vectorizer)
        X_user = hstack([X_text_user, X_eng_user])
        probs = clf.predict_proba(X_user)[:, 1]

        # STEP 5: Build results
        posts = []
        for i, rec in enumerate(user_posts):
            misinfo_score = float(probs[i] * 100)

            text = " ".join(filter(None, [rec.get("title", ""), rec.get("snippet", "")]))
            cb_score = clickbait_score(text)

            keywords = [k for k in ["confirmed", "leaked", "official", "proof", "cure",
                                   "exposed", "fake", "scam", "rumor", "conspiracy", "hoax"]
                       if k in text.lower()]

            posts.append({
                "rank": rec.get("rank", i + 1),
                "title": rec.get("title", ""),
                "url": rec.get("url", ""),
                "snippet": rec.get("snippet", "")[:250],
                "subreddit": rec.get("subreddit", ""),
                "date": rec.get("date_snippet", ""),
                "misinfo_score": round(misinfo_score, 1),
                "clickbait_score": round(cb_score, 3),
                "keywords": keywords,
                "risk_level": "high" if misinfo_score >= 70 else "medium" if misinfo_score >= 40 else "low"
            })

        # Statistics
        avg_score = float(np.mean(probs) * 100)
        max_score = float(np.max(probs) * 100)
        min_score = float(np.min(probs) * 100)
        high_risk_count = sum(1 for p in posts if p["misinfo_score"] >= 70)
        medium_risk_count = sum(1 for p in posts if 40 <= p["misinfo_score"] < 70)
        low_risk_count = sum(1 for p in posts if p["misinfo_score"] < 40)

        response = {
            "hashtag": hashtag,
            "total_posts": len(posts),
            "posts": posts,
            "statistics": {
                "avg_misinfo_score": round(avg_score, 1),
                "max_misinfo_score": round(max_score, 1),
                "min_misinfo_score": round(min_score, 1),
                "high_risk_count": high_risk_count,
                "medium_risk_count": medium_risk_count,
                "low_risk_count": low_risk_count
            },
            "training_info": {
                "samples_scraped": len(training_posts),
                "train_accuracy": f"{train_acc * 100:.1f}%",
                "test_accuracy": f"{test_acc * 100:.1f}%"
            }
        }

        app.logger.info(f"=== Analysis complete for {hashtag} ===")
        return jsonify(response), 200

    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        load_model()
        return jsonify({"status": "healthy", "model_loaded": True}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


if __name__ == '__main__':
    # Check if models exist
    if not os.path.exists(MODEL_PATH) or not os.path.exists(VECT_PATH):
        print("WARNING: Model files not found!")
        print(f"Please run: python backend/train_model.py")
        print("This will generate the required model files.\n")

    # Configure debug mode via environment variable (default: False for production)
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    # Run the Flask app on port 5001 (port 5000 is used by macOS AirPlay)
    print("\n" + "="*60)
    print("Starting ClipCheck Server...")
    print("="*60)
    print("Server running at: http://localhost:5001")
    print("Also available at: http://127.0.0.1:5001")
    print(f"Debug mode: {'ON' if debug_mode else 'OFF'}")
    print(f"Cache expiry: {CACHE_EXPIRY_HOURS} hour(s)")
    print("\nPress CTRL+C to stop the server")
    print("="*60 + "\n")
    app.run(debug=debug_mode, host='0.0.0.0', port=5001)
