# test_google_scraper.py
from backend.google_scraper import search_reddit_by_hashtag

hashtag = "#politics"  # replace with any hashtag
posts = search_reddit_by_hashtag(hashtag, num_results=5)

print(f"Posts found for {hashtag}:")
for i, p in enumerate(posts, 1):
    print(f"Rank {i}:")
    print(f"Title: {p['title']}")
    print(f"URL: {p['url']}")
    print(f"Snippet: {p['snippet']}")
    print(f"Subreddit: {p['subreddit']}")
    print("-" * 50)
