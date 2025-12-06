# google_scraper.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import time
import re

def search_reddit_by_hashtag(hashtag: str, num_results: int = 10, pause: float = 2.0):
    """
    Scrape Google search results for Reddit posts with a given hashtag.
    Returns list of dicts: {rank, title, url, snippet, subreddit, date_snippet}
    """
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    query = f'site:reddit.com "{hashtag.strip("#")}"'
    search_url = f"https://www.google.com/search?q={query}&num={num_results}"
    driver.get(search_url)
    time.sleep(pause)  # wait for page to load

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    results = []
    rank = 0

    g_items = soup.find_all("div", class_="g")
    for gi in g_items:
        try:
            # get anchor and URL
            a_tag = gi.find("a", href=True)
            if not a_tag:
                continue
            href = a_tag["href"]
            if not href or "reddit.com" not in href:
                continue

            title = a_tag.get_text(strip=True)

            # get snippet text
            snippet_tag = gi.find("div", class_="IsZvec")
            snippet = snippet_tag.get_text(separator=" ").strip() if snippet_tag else ""

            # extract subreddit from URL
            subreddit = None
            try:
                parsed = urlparse(href)
                parts = parsed.path.split("/")
                if "r" in parts:
                    idx = parts.index("r")
                    if idx + 1 < len(parts):
                        subreddit = parts[idx + 1]
            except Exception:
                subreddit = None

            # extract date from snippet (common patterns)
            date_match = None
            date_search = re.search(r'\b(?:\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b|\b\d{4}\b|\bago\b)', snippet)
            if date_search:
                date_match = date_search.group(0)

            rank += 1
            results.append({
                "rank": rank,
                "title": title,
                "url": href,
                "snippet": snippet,
                "subreddit": subreddit,
                "date_snippet": date_match
            })

            if rank >= num_results:
                break
        except Exception:
            continue

    return results

if __name__ == "__main__":
    posts = search_reddit_by_hashtag("#politics", num_results=5)
    for p in posts:
        print(p)
