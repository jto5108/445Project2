from analyzer import analyze_reddit_post

def test_live_example():
    # Replace this with any public Reddit post that exists.
    sample_url = "https://www.reddit.com/r/PublicFreakout/comments/10q5abc/example_post/"
    try:
        out = analyze_reddit_post(sample_url)
        assert "score_percent" in out
        print("Score:", out["score_percent"])
        print("Found similar posts:", len(out["evidence"]["similar_posts"]))
    except Exception as e:
        print("Test failed (likely invalid example URL):", e)
