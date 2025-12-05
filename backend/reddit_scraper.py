# reddit_scraper.py
import requests
import time
from urllib.parse import quote, urlparse, urlunparse

# Use your Reddit username for User-Agent
DEFAULT_HEADERS = {
    "User-Agent": "python:misinfo_clip_detector:0.1 (by /u/Present_Rice_5748)"
}
REQUEST_TIMEOUT = 10  # seconds

def normalize_reddit_url(url: str) -> str:
    """
    Normalize a Reddit post URL:
    - Remove query parameters and fragments
    - Ensure trailing slash
    """
    parsed = urlparse(url)
    cleaned = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    if not cleaned.endswith("/"):
        cleaned += "/"
    return cleaned

def _to_json_url(post_url: str) -> str:
    """Ensure the URL ends with .json for Reddit API access."""
    normalized = normalize_reddit_url(post_url)
    if not normalized.endswith(".json"):
        normalized += ".json"
    return normalized

def fetch_submission_json(post_url: str, headers=None):
    """Fetch a Reddit submission and return JSON."""
    headers = headers or DEFAULT_HEADERS
    json_url = _to_json_url(post_url)
    r = requests.get(json_url, headers=headers, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()

def parse_submission(post_url: str):
    """
    Returns a dict with submission metadata and flattened comments.
    """
    data = fetch_submission_json(post_url)
    
    # Submission info
    post = data[0]["data"]["children"][0]["data"]
    out = {
        "id": post.get("id"),
        "title": post.get("title", ""),
        "selftext": post.get("selftext", ""),
        "subreddit": post.get("subreddit", ""),
        "created_utc": post.get("created_utc"),
        "score": post.get("score", 0),
        "upvote_ratio": post.get("upvote_ratio", 0.0),
        "url": post.get("url"),
        "thumbnail": post.get("thumbnail")
    }

    # Flatten comments
    comments_raw = data[1]["data"]["children"]
    comments = []

    def _gather(cnode):
        if not cnode or "data" not in cnode:
            return
        d = cnode["data"]
        if d.get("body"):
            comments.append(d["body"])
        replies = d.get("replies")
        if replies and isinstance(replies, dict):
            for ch in replies.get("data", {}).get("children", []):
                _gather(ch)

    for c in comments_raw:
        _gather(c)

    out["comments"] = comments
    return out

def reddit_search_titles(query: str, limit=10, headers=None):
    """Search Reddit posts by title and return a list of post metadata."""
    headers = headers or DEFAULT_HEADERS
    q = quote(query)
    url = f"https://www.reddit.com/search.json?q={q}&sort=new&limit={limit}"
    r = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    res = r.json().get("data", {}).get("children", [])
    
    out = []
    for item in res:
        d = item.get("data", {})
        out.append({
            "id": d.get("id"),
            "title": d.get("title"),
            "subreddit": d.get("subreddit"),
            "url": "https://www.reddit.com" + d.get("permalink", ""),
            "score": d.get("score", 0)
        })
    # Be polite with Reddit
    time.sleep(0.5)
    return out

# Example usage:
if __name__ == "__main__":
    test_links = [
        "https://www.reddit.com/r/whatcarshouldIbuy/comments/1pdijcc/can_i_go_off_this/?utm_source=share&utm_medium=web3x",
        "https://www.reddit.com/r/cyberpunkgame/comments/1pe31dp/realistically_what_is_the_expected_release/?utm_source=share&utm_medium=web3x"
    ]
    for link in test_links:
        print("Normalized URL:", normalize_reddit_url(link))
        print("JSON URL:", _to_json_url(link))
        submission = parse_submission(link)
        print("Title:", submission["title"])
        print("Number of comments:", len(submission["comments"]))
        print("-" * 40)
