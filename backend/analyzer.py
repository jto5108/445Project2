from reddit_scraper import parse_submission, reddit_search_titles
from utils import analyze_comments_keywords, extract_keywords_from_text
import math

# Define keywords (extendable)
KEYWORDS = ["fake", "cap", "edited", "misleading", "not true", "out of context", "deepfake", "lies", "lying"]

def compute_similarity_score(title: str, similar_posts: list):
    """
    Simple textual similarity proxy: if many similar titles share keywords in common, raise similarity flag.
    We'll compute fraction of similar posts that share at least one keyword with the input title.
    Returns 0..1
    """
    title_keys = set(extract_keywords_from_text(title))
    if not title_keys:
        return 0.0
    hits = 0
    for p in similar_posts:
        t = p.get("title", "")
        if title_keys.intersection(set(extract_keywords_from_text(t))):
            hits += 1
    return hits / max(1, len(similar_posts))

def analyze_reddit_post(post_url: str):
    """
    Full pipeline:
      - fetch post & comments
      - comment-keyword evidence
      - search similar posts (title-based)
      - combine into final score
    """
    post = parse_submission(post_url)
    title = post.get("title", "")
    comments = post.get("comments", [])

    # 1) comment evidence
    comment_rate, comment_examples = analyze_comments_keywords(comments, KEYWORDS)

    # 2) similar posts evidence
    # Use first 6-8 words of the title for search to constrain results
    search_query = " ".join(title.split()[:6]) if title else ""
    similar = reddit_search_titles(search_query, limit=8) if search_query else []

    similarity_score = compute_similarity_score(title, similar)

    # 3) metadata heuristic: if post has many comments and low upvote ratio or low score, minor boost
    score_count = post.get("score", 0)
    upvote_ratio = post.get("upvote_ratio", 0.0)
    meta_score = 0.0
    if score_count < 20 and len(comments) > 10:
        meta_score = 0.1

    # Combine weighted
    # Weights tuned for classroom demo: comments (0.5), similarity (0.35), meta (0.15)
    final_raw = 0.5 * comment_rate + 0.35 * similarity_score + 0.15 * meta_score
    final = max(0.0, min(1.0, final_raw))

    result = {
        "post": {
            "id": post.get("id"),
            "title": title,
            "subreddit": post.get("subreddit"),
            "url": post.get("url"),
            "score": post.get("score"),
            "upvote_ratio": post.get("upvote_ratio"),
            "num_comments": len(comments)
        },
        "evidence": {
            "comment_flag_rate": round(comment_rate, 4),
            "comment_examples": comment_examples,
            "search_query": search_query,
            "similar_posts": similar
        },
        "score_percent": round(final * 100, 2)
    }
    return result
