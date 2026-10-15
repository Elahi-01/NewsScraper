"""
Wall Street Journal Archive scraper.
Uses the WSJ news archive (year → month → day → articles).
Uses Selenium for day pages (JS-rendered content).
Inputs: keyword, start_year, end_year.
"""

import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://www.wsj.com"
YEARS_URL = f"{BASE}/news/archive/years"
REQ_SLEEP = 1.5
SEL_SLEEP = 4

_session = requests.Session()
_session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    )
})


def _get_soup_requests(url: str) -> BeautifulSoup:
    """Fetch a URL with requests and return a BeautifulSoup object."""
    r = _session.get(url, timeout=30)
    r.raise_for_status()
    time.sleep(REQ_SLEEP)
    return BeautifulSoup(r.text, "lxml")


def _get_month_urls(start_year: int, end_year: int,
                    progress_callback=None) -> list:
    """Get month archive URLs for the given year range."""
    if progress_callback:
        progress_callback(f"Loading WSJ archive years {start_year}-{end_year}...")

    soup = _get_soup_requests(YEARS_URL)
    month_urls = set()

    for a in soup.select("a[href^='/news/archive/']"):
        href = a.get("href", "").strip()
        parts = href.strip("/").split("/")
        if len(parts) == 4 and parts[2].isdigit():
            y = int(parts[2])
            if start_year <= y <= end_year:
                month_urls.add(urljoin(BASE, href))

    month_urls = sorted(month_urls)
    if progress_callback:
        progress_callback(f"Found {len(month_urls)} month URLs")
    return month_urls


def _get_day_urls(month_url: str) -> list:
    """Get day archive URLs from a month page."""
    soup = _get_soup_requests(month_url)
    day_urls = set()

    for a in soup.select("a[href^='/news/archive/']"):
        href = a.get("href", "").strip()
        parts = href.strip("/").split("/")
        if len(parts) == 5 and all(p.isdigit() for p in parts[2:5]):
            day_urls.add(urljoin(BASE, href))

    return sorted(day_urls)


def _make_driver():
    """Create a headless Chrome WebDriver instance."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("window-size=1400,900")
    return webdriver.Chrome(options=opts)


def _get_articles_one_day(driver, day_url: str, keyword_lower: str) -> list:
    """Render a day page with Selenium and extract matching articles."""
    driver.get(day_url)
    time.sleep(SEL_SLEEP)
    soup = BeautifulSoup(driver.page_source, "lxml")

    y, m, d = day_url.rstrip("/").split("/")[-3:]
    date_str = f"{y}-{m}-{d}"

    rows = []
    for h in soup.select("h2, h3"):
        a = h.find("a")
        if not a:
            continue
        title = a.get_text(strip=True)
        url = a.get("href", "")
        if not title or not url.startswith("https://www.wsj.com"):
            continue

        text_to_search = (title + " " + url).lower()
        if keyword_lower in text_to_search:
            rows.append({
                "date": date_str,
                "title": title,
                "url": url,
            })
    return rows


def search_wsj(keyword: str, start_year: int, end_year: int,
               progress_callback=None) -> list:
    """
    Search the Wall Street Journal archive by keyword and year range.
    Requires Selenium (Chrome) for rendering day archive pages.

    Args:
        keyword: Search term (case-insensitive match in title/URL).
        start_year: Start year (integer).
        end_year: End year (integer).
        progress_callback: Optional callable(str) for progress updates.

    Returns:
        List of dicts with keys: date, title, url
    """
    keyword_lower = keyword.lower().strip()
    if not keyword_lower:
        raise ValueError("Keyword cannot be empty.")

    month_urls = _get_month_urls(start_year, end_year, progress_callback)

    driver = _make_driver()
    all_results = []

    try:
        for m_url in month_urls:
            if progress_callback:
                progress_callback(f"Processing month: {m_url}")

            try:
                day_urls = _get_day_urls(m_url)
            except Exception as e:
                if progress_callback:
                    progress_callback(f"Error on month {m_url}: {e}")
                continue

            for d_url in day_urls:
                try:
                    rows = _get_articles_one_day(driver, d_url, keyword_lower)
                    all_results.extend(rows)
                    if progress_callback and rows:
                        progress_callback(
                            f"  {d_url.split('/')[-1]}: {len(rows)} matches"
                        )
                except Exception as e:
                    if progress_callback:
                        progress_callback(f"  Error on day {d_url}: {e}")
    finally:
        driver.quit()

    return all_results
