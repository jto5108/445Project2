# reddit_scraper.py
import praw
import time

# Use your Reddit username in the user_agent
REDDIT_CLIENT_ID = "YOUR_CLIENT_ID"
REDDIT_CLIENT_SECRET = "YOUR_CLIENT_SECRET"
REDDIT_USER_AGENT = "misinfo_clip_detector by /u/Present_Rice_5748"

# Initialize PRAW Reddit instance
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT,
    check_for_async=False
)

def normalize_url(url: str) -> str:
    """Ensure the URL is in canonical Reddit format."""
    if "reddit.com" not in url:
        raise ValueError("Invalid Reddit URL")
    # Remove tracking parameters
    url = url.split("?")[0]
    # Ensure it ends with '/'
    if not url.endswith("/"):
        url += "/"
    return url

def fetch_submission(post_url: str):
    """
    Fetch submission metadata and top-level comments.
    Returns dict: id, title, selftext, subreddit, score, upvote_ratio, url, comments: [..]
    """
    normalized_url = normalize_url(post_url)
    try:
        submission = reddit.submission(url=normalized_url)
    except Exception as e:
        print(f"Error fetching submission: {e}")
        return None

    # Fetch top-level comments
    submission.comments.replace_more(limit=None)
    comments = [c.body for c in submission.comments.list()]

    out = {
        "id": submission.id,
        "title": submission.title,
        "selftext": submission.selftext,
        "subreddit": submission.subreddit.display_name,
        "score": submission.score,
        "upvote_ratio": getattr(submission, "upvote_ratio", 0.0),
        "url": submission.url,
        "num_comments": submission.num_comments,
        "comments": comments
    }
    return out

def reddit_search_titles(query: str, limit=10):
    """
    Search Reddit by title using PRAW. Returns list of dicts.
    """
    posts = []
    for submission in reddit.subreddit("all").search(query, sort="new", limit=limit):
        posts.append({
            "id": submission.id,
            "title": submission.title,
            "subreddit": submission.subreddit.display_name,
            "url": submission.url,
            "score": submission.score
        })
        time.sleep(0.2)  # polite
    return posts

# -------------------------
# Example usage
# -------------------------
if __name__ == "__main__":
    test_links = [
        "https://www.reddit.com/r/whatcarshouldIbuy/comments/1pdijcc/can_i_go_off_this/",
        "https://www.reddit.com/r/cyberpunkgame/comments/1pe31dp/realistically_what_is_the_expected_release/"
    ]

    for link in test_links:
        print("Normalized URL:", normalize_url(link))
        submission = fetch_submission(link)
        if submission:
            print("Title:", submission["title"])
            print("Subreddit:", submission["subreddit"])
            print("Comments fetched:", len(submission["comments"]))
        else:
            print("Failed to fetch submission")
        print("-" * 50)
