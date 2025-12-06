# google_scraper.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote_plus
import time
import re

def search_reddit_by_hashtag(hashtag: str, num_results: int = 10, pause: float = 3.0):
    """
    Scrape DuckDuckGo search results for Reddit posts with a given hashtag.
    Returns list of dicts: {rank, title, url, snippet, subreddit, date_snippet}

    Note: Switched from Google to DuckDuckGo to avoid CAPTCHA blocking.
    """
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Remove webdriver flag
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    # Build search query - search for hashtag content on Reddit via DuckDuckGo
    search_term = hashtag.strip("#")
    query = f'site:reddit.com {search_term}'
    search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"

    try:
        driver.get(search_url)
        time.sleep(pause)  # wait for page to load

        soup = BeautifulSoup(driver.page_source, "html.parser")

        results = []
        rank = 0

        # DuckDuckGo uses class "result" for search results
        search_results = soup.find_all("div", class_="result")

        for result_div in search_results[:num_results]:
            try:
                # Find title link
                title_link = result_div.find("a", class_="result__a")
                if not title_link:
                    continue

                href = title_link.get("href", "")
                if not href:
                    continue

                # DuckDuckGo wraps URLs - extract the actual Reddit URL
                if "uddg=" in href:
                    import urllib.parse
                    match = re.search(r'uddg=([^&]+)', href)
                    if match:
                        href = urllib.parse.unquote(match.group(1))

                if not href or "reddit.com" not in href:
                    continue

                title = title_link.get_text(strip=True)
                if not title:
                    continue

                # Find snippet
                snippet = ""
                snippet_div = result_div.find("a", class_="result__snippet")
                if snippet_div:
                    snippet = snippet_div.get_text(separator=" ").strip()[:300]

                # Extract subreddit from URL
                subreddit = None
                try:
                    parsed = urlparse(href)
                    parts = parsed.path.split("/")
                    if "r" in parts:
                        idx = parts.index("r")
                        if idx + 1 < len(parts):
                            subreddit = parts[idx + 1]
                except:
                    subreddit = "unknown"

                # Extract date if present in snippet
                date_match = None
                if snippet:
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
            except Exception as e:
                continue

        return results

    finally:
        driver.quit()

if __name__ == "__main__":
    posts = search_reddit_by_hashtag("#politics", num_results=5)
    for p in posts:
        print(p)
