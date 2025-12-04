import praw
import os

def get_reddit_client():
    return praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent="ClipCheckBot/0.1 by YourName"
    )

def fetch_submission(url):
    reddit = get_reddit_client()
    submission = reddit.submission(url=url)
    submission.comments.replace_more(limit=None)
    comments = [c.body for c in submission.comments.list()]
    return {
        "id": submission.id,
        "title": submission.title,
        "selftext": submission.selftext,
        "subreddit": str(submission.subreddit),
        "created_utc": submission.created_utc,
        "score": submission.score,
        "upvote_ratio": submission.upvote_ratio,
        "media": submission.media,
        "thumbnail": submission.thumbnail,
        "comments": comments
    }

def search_similar_posts(title, subreddit=None, limit=20):
    reddit = get_reddit_client()
    query = title.split(" ")
    query = " OR ".join(query)

    if subreddit:
        sub = reddit.subreddit(subreddit)
        results = sub.search(query, sort="relevance", limit=limit)
    else:
        results = reddit.subreddit("all").search(query, sort="relevance", limit=limit)

    out = []
    for r in results:
        out.append({
            "id": r.id,
            "title": r.title,
            "thumbnail": r.thumbnail,
            "selftext": r.selftext,
            "score": r.score
        })
    return out
