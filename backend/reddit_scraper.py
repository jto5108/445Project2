# reddit_scraper.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time

# Constants
DEFAULT_HEADERS = {
    "User-Agent": "python:misinfo_clip_detector:0.1 (by /u/Present_Rice_5748)"
}
REQUEST_TIMEOUT = 10  # seconds
PUSHSHIFT_LIMIT = 500  # max comments per request


# -----------------------------
# URL Utilities
# -----------------------------
def clean_url(post_url: str) -> str:
    """Normalize a Reddit URL to standard form ending with /."""
    if not post_url.startswith("http"):
        post_url = "https://" + post_url
    parsed = urlparse(post_url)
    path = parsed.path.rstrip("/")
    return f"https://www.reddit.com{path}/"


def extract_post_id(post_url: str) -> str:
    """Extract the Reddit post ID (e.g., '1pdijcc') from a URL."""
    parts = post_url.strip("/").split("/")
    # Reddit URL format: /r/subreddit/comments/post_id/title/
    try:
        idx = parts.index("comments")
        return parts[idx + 1]
    except (ValueError, IndexError):
        raise ValueError(f"Invalid Reddit URL: {post_url}")


# -----------------------------
# Pushshift Comments
# -----------------------------
def fetch_pushshift_comments(post_id: str):
    """
    Fetch comments for a post using Pushshift API.
    Returns a list of comment strings.
    """
    url = f"https://api.pushshift.io/reddit/comment/search/?link_id=t3_{post_id}&limit={PUSHSHIFT_LIMIT}"
    r = requests.get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    data = r.json().get("data", [])
    comments = [c.get("body", "") for c in data]
    return comments


# -----------------------------
# Old Reddit HTML scraping
# -----------------------------
def scrape_old_reddit_submission(post_url: str):
    """
    Scrape post metadata (title, selftext, subreddit, score, etc.) from old.reddit.com
    """
    old_url = post_url.replace("www.reddit.com", "old.reddit.com")
    r = requests.get(old_url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # Title
    title_tag = soup.find("a", class_="title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # Selftext (optional)
    selftext_tag = soup.find("div", class_="expando")
    selftext = selftext_tag.get_text(strip=True) if selftext_tag else ""

    # Subreddit
    subreddit_tag = soup.find("a", class_="subreddit")
    subreddit = subreddit_tag.get_text(strip=True) if subreddit_tag else ""

    # Score (upvotes)
    score_tag = soup.find("div", class_="score unvoted")
    try:
        score = int(score_tag.get_text(strip=True).replace(" points", ""))
    except (ValueError, AttributeError):
        score = 0

    # Upvote ratio not available in old HTML
    upvote_ratio = None

    return {
        "title": title,
        "selftext": selftext,
        "subreddit": subreddit,
        "score": score,
        "upvote_ratio": upvote_ratio,
        "url": post_url
    }


# -----------------------------
# Combined function
# -----------------------------
def get_reddit_post(post_url: str):
    """
    Fetch metadata + comments for a Reddit post.
    Returns dict with 'post' and 'comments' keys.
    """
    post_url = clean_url(post_url)
    post_id = extract_post_id(post_url)

    # Scrape post metadata
    try:
        post_data = scrape_old_reddit_submission(post_url)
    except Exception as e:
        print(f"Error scraping post metadata: {e}")
        post_data = {}

    # Fetch comments from Pushshift
    try:
        comments = fetch_pushshift_comments(post_id)
    except Exception as e:
        print(f"Error fetching comments: {e}")
        comments = []

    return {
        "post": post_data,
        "comments": comments
    }


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    test_links = [
        "https://www.reddit.com/r/whatcarshouldIbuy/comments/1pdijcc/can_i_go_off_this/",
        "https://www.reddit.com/r/cyberpunkgame/comments/1pe31dp/realistically_what_is_the_expected_release/"
    ]

    for link in test_links:
        print("Normalized URL:", clean_url(link))
        try:
            data = get_reddit_post(link)
            print("Title:", data["post"].get("title"))
            print("Subreddit:", data["post"].get("subreddit"))
            print("Comments fetched:", len(data["comments"]))
            print("-" * 50)
        except Exception as e:
            print(f"Error processing {link}: {e}")
