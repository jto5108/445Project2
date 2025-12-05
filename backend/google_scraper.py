# google_scraper.py
# Fetch Google search results (top reddit posts) for a given hashtag.
# NOTE: Google frequently changes markup and may block scraping.
# Use sparingly and prefer Google Custom Search API for production.

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
import time
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
GOOGLE_SEARCH_URL = "https://www.google.com/search"

def _clean_google_link(href: str) -> str | None:
    """
    Google often wraps links like /url?q=<real_url>&sa=...
    This extracts the q parameter.
    """
    if not href:
        return None
    if href.startswith("/url?"):
        qs = parse_qs(href[5:])
        q = qs.get("q", [])
        if q:
            return q[0]
    if href.startswith("http"):
        return href
    return None

def _extract_snippet(gitem):
    s = gitem.find("div", class_="IsZvec")
    if s:
        # snippet may be inside a <span> or <div>
        txt = s.get_text(separator=" ").strip()
        return txt
    return ""

def search_reddit_by_hashtag(hashtag: str, num_results: int = 10, pause: float = 1.0):
    """
    Query Google for `site:reddit.com "<hashtag>"` and return top results.
    Returns list of dicts: {rank, title, snippet, url, subreddit, date}
    """
    q = f'site:reddit.com "{hashtag.strip("#")}"'
    params = {"q": q, "num": str(num_results)}
    r = requests.get(GOOGLE_SEARCH_URL, params=params, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    results = []
    rank = 0

    # Google markup uses divs with class 'g' for results; fallback to searching <a> tags
    g_items = soup.find_all("div", class_="g")
    if not g_items:
        # fallback: find anchors directly
        anchors = soup.find_all("a")
        for a in anchors:
            href = a.get("href")
            real = _clean_google_link(href)
            if real and "reddit.com" in real:
                title = a.get_text(strip=True)
                snippet = ""  # we will attempt to find snippet near anchor
                rank += 1
                results.append({"rank": rank, "title": title, "snippet": snippet, "url": real})
                if rank >= num_results:
                    break
    else:
        for gi in g_items:
            # get anchor
            a = gi.find("a", href=True)
            if not a:
                continue
            href = a["href"]
            real = _clean_google_link(href)
            if not real or "reddit.com" not in real:
                continue
            title = a.get_text(strip=True)
            snippet = _extract_snippet(gi)
            # try to extract date in snippet using common patterns like "3 days ago" or "Jan 1, 2024"
            date_match = None
            date_search = re.search(r'\b(?:\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b|\b\d{4}\b|\bago\b)', snippet)
            if date_search:
                date_match = date_search.group(0)
            # try to extract subreddit from URL path
            subreddit = None
            try:
                parsed = urlparse(real)
                parts = parsed.path.split("/")
                # path like /r/<subreddit>/comments/<postid>/
                if "r" in parts:
                    idx = parts.index("r")
                    if idx + 1 < len(parts):
                        subreddit = parts[idx + 1]
            except Exception:
                subreddit = None

            rank += 1
            results.append({
                "rank": rank,
                "title": title,
                "snippet": snippet,
                "url": real,
                "subreddit": subreddit,
                "date_snippet": date_match
            })
            if rank >= num_results:
                break

    # polite pause
    time.sleep(pause)
    return results

if __name__ == "__main__":
    # quick demo
    posts = search_reddit_by_hashtag("#cyberpunk", num_results=5)
    for p in posts:
        print(p)
