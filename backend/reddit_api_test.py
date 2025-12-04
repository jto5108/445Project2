import praw

# ---- FILL THESE IN ----
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"
USER_AGENT = "Abington-463-MisinfoDetector/0.1 by YourName"

def test_reddit_api():
    try:
        reddit = praw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            user_agent=USER_AGENT
        )

        url = "https://www.reddit.com/r/news/comments/1c4ncgx/test_post/"  # replace with any post

        submission = reddit.submission(url=url)

        print("Title:", submission.title)
        print("Score:", submission.score)
        print("Number of comments:", submission.num_comments)

        submission.comments.replace_more(limit=0)

        print("\n--- FIRST 10 COMMENTS ---")
        for i, comment in enumerate(submission.comments[:10]):
            print(f"{i+1}. {comment.body[:100]}...")  # First 100 chars

    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    test_reddit_api()
