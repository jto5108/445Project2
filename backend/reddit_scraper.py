import requests
from urllib.parse import urlparse
import time

# Default user-agent for polite requests
DEFAULT_HEADERS = {"User-Agent": "MisinfoClipDetector/0.1 (by u/yourname)"}
REQUEST_TIMEOUT = 10  # seconds

def _to_json_url(post_url: str) -> str:
    # Accept either full comments URL or post permalink
    if post_url.endswith(".json"):
        return post_url
    if post_url.endswith("/"):
        post_url = post_url[:-1]
    return post_url + ".json"

def fetch_submission_json(post_url: str, headers=None):
    headers = headers or DEFAULT_HEADERS
    json_url = _to_json_url(post_url)
    r = requests.get(json_url, headers=headers, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()

def parse_submission(post_url: str):
    """
    Returns a dict: {id, title, selftext, subreddit, created_utc, score, upvote_ratio, url, thumbnail, comments: [..]}
    """
    data = fetch_submission_json(post_url)
    # data[0] = submission listing, data[1] = comments
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

    # Comments: may be nested, we flatten first-level + deeper replies
    comments_raw = data[1]["data"]["children"]
    comments = []
    def _gather(cnode):
        if not cnode or "data" not in cnode:
            return
        d = cnode["data"]
        if d.get("body"):
            comments.append(d["body"])
        # handle replies (may be dict or "more")
        replies = d.get("replies")
        if replies and isinstance(replies, dict):
            for ch in replies.get("data", {}).get("children", []):
                _gather(ch)

    for c in comments_raw:
        _gather(c)

    out["comments"] = comments
    return out

def reddit_search_titles(query: str, limit=10, headers=None):
    """
    Use reddit search endpoint (no OAuth). Return list of dicts with title, subreddit, url, score.
    """
    headers = headers or DEFAULT_HEADERS
    import urllib.parse
    q = urllib.parse.quote(query)
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
    # be polite with Reddit
    time.sleep(0.5)
    return out
