"""
Los Angeles Times Sitemap scraper.
Navigates the LA Times sitemap (year → month → articles).
Inputs: keywords (comma-separated), start_year, end_year.
"""

import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://www.latimes.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0 Safari/537.36"
    )
}

MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}


def _get_soup(url: str) -> BeautifulSoup:
    """Fetch a URL and return a parsed BeautifulSoup object."""
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def _get_available_years() -> list:
    """Get list of years available on the LA Times sitemap."""
    url = f"{BASE}/sitemap"
    soup = _get_soup(url)
    years = []
    for a in soup.select("a"):
        text = a.get_text(strip=True)
        if text.isdigit() and len(text) == 4:
            years.append(int(text))
    return sorted(set(years))


def _get_month_links(year: int) -> list:
    """Get month page URLs for a given year."""
    url = f"{BASE}/sitemap/{year}"
    soup = _get_soup(url)
    months = []
    for a in soup.select("a"):
        text = a.get_text(strip=True).lower()
        if text in MONTH_MAP:
            month_num = MONTH_MAP[text]
            month_url = urljoin(BASE, a.get("href", ""))
            months.append((month_num, month_url))
    return months


def _extract_date_from_url(url: str) -> str:
    """Try to extract a YYYY-MM-DD date from the article URL path."""
    parts = url.split("/")
    for i in range(len(parts) - 2):
        if (
            parts[i].isdigit() and len(parts[i]) == 4
            and parts[i + 1].isdigit()
            and parts[i + 2].isdigit()
        ):
            y = int(parts[i])
            m = int(parts[i + 1])
            d = int(parts[i + 2])
            if 1 <= m <= 12 and 1 <= d <= 31:
                return f"{y:04d}-{m:02d}-{d:02d}"
    return ""


def _get_articles_from_month(month_url: str, year: int, month_num: int) -> list:
    """Extract article links from a month sitemap page."""
    soup = _get_soup(month_url)
    articles = []

    for a in soup.select("main a, article a, li a"):
        title = a.get_text(strip=True)
        href = a.get("href")
        if not href or not title:
            continue

        link = urljoin(BASE, href)
        if not link.startswith(BASE):
            continue

        article_date = _extract_date_from_url(link)

        articles.append({
            "date": article_date if article_date else f"{year:04d}-{month_num:02d}-00",
            "title": title,
            "url": link,
        })
    return articles


def _filter_by_keywords(rows: list, keywords: list) -> list:
    """Filter articles by keywords (any word match in title or URL)."""
    all_terms = []
    for k in keywords:
        all_terms.extend(k.lower().split())

    filtered = []
    for r in rows:
        text = f"{r['title']} {r['url']}".lower()
        if any(term in text for term in all_terms):
            filtered.append(r)
    return filtered


def search_latimes(keywords: str, start_year: int, end_year: int,
                   progress_callback=None) -> list:
    """
    Search the LA Times sitemap archive by keywords and year range.

    Args:
        keywords: Comma-separated keywords string.
        start_year: Start year (integer).
        end_year: End year (integer).
        progress_callback: Optional callable(str) for progress updates.

    Returns:
        List of dicts with keys: date, title, url
    """
    keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
    if not keyword_list:
        raise ValueError("At least one keyword is required.")

    # Get available years
    if progress_callback:
        progress_callback("Fetching available years from LA Times sitemap...")

    available_years = _get_available_years()

    all_rows = []
    for y in range(start_year, end_year + 1):
        if y not in available_years:
            if progress_callback:
                progress_callback(f"Year {y} not available, skipping.")
            continue

        if progress_callback:
            progress_callback(f"Fetching year {y}...")

        try:
            month_links = _get_month_links(y)
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error loading year {y}: {e}")
            continue

        for month_num, month_url in month_links:
            if progress_callback:
                progress_callback(f"  Year {y}, month {month_num}...")

            try:
                rows = _get_articles_from_month(month_url, y, month_num)
                all_rows.extend(rows)
            except Exception as e:
                if progress_callback:
                    progress_callback(f"  Error on month {month_num}: {e}")
            time.sleep(1.5)

    # Filter by keywords
    matched = _filter_by_keywords(all_rows, keyword_list)
    return matched
