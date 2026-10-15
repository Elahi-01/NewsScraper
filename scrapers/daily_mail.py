"""
Daily Mail Archive scraper.
Navigates the sitemap archive (month → day → article links).
Inputs: keyword, start_date, end_date (as datetime.date objects).
Coverage: 1994-2026.
"""

import time
from datetime import datetime, date
import requests
from bs4 import BeautifulSoup

BASE = "https://www.dailymail.co.uk"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}


def _generate_month_urls(start_date: date, end_date: date) -> list:
    """
    Dynamically generate month archive URLs for the given date range.
    Format: https://www.dailymail.co.uk/home/sitemaparchive/month_YYYYMM.html
    Coverage starts from 1994.
    """
    urls = []
    y, m = start_date.year, start_date.month
    while (y < end_date.year) or (y == end_date.year and m <= end_date.month):
        urls.append(
            f"{BASE}/home/sitemaparchive/month_{y:04d}{m:02d}.html"
        )
        m += 1
        if m > 12:
            m = 1
            y += 1
    return urls


def _get_soup(url: str):
    """Fetch a URL and return a BeautifulSoup object, or None on 404."""
    r = requests.get(url, headers=HEADERS, timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return BeautifulSoup(r.text, "lxml")


def _extract_day_links_from_month(month_url: str) -> list:
    """Extract day-page links from a month archive page."""
    soup = _get_soup(month_url)
    if soup is None:
        return []

    day_links = []
    for a in soup.select("a[href*='day_'][href*='sitemaparchive']"):
        href = a["href"]
        if href.startswith("/"):
            href = BASE + href
        if href not in day_links:
            day_links.append(href)
    return day_links


def _scrape_day(day_url: str, keyword: str,
                start_date: date, end_date: date) -> list:
    """
    Scrape articles from a single day archive page.
    Filters by keyword (case-insensitive title match) and date range.
    """
    soup = _get_soup(day_url)
    if soup is None:
        return []

    # Parse the date from the page header
    current_date = None
    date_el = soup.select_one("h3, h2")
    if date_el:
        txt = date_el.get_text(strip=True)
        for fmt in ("%A, %d %B %Y", "%A %d %B %Y"):
            try:
                current_date = datetime.strptime(txt, fmt).date()
                break
            except ValueError:
                continue

    if not current_date:
        return []

    # Skip if outside the requested range
    if not (start_date <= current_date <= end_date):
        return []

    results = []
    keyword_lower = keyword.lower()

    for a in soup.select("li > a"):
        title = a.get_text(strip=True)
        href = a.get("href")
        if not title or not href:
            continue

        if keyword_lower not in title.lower():
            continue

        if href.startswith("/"):
            href = BASE + href

        results.append({
            "date": current_date.isoformat(),
            "title": title,
            "url": href,
        })

    return results


def search_daily_mail(keyword: str, start_date: date, end_date: date,
                      progress_callback=None) -> list:
    """
    Search the Daily Mail archive by keyword and date range.

    Args:
        keyword: Search term (case-insensitive title match).
        start_date: Start date (datetime.date).
        end_date: End date (datetime.date).
        progress_callback: Optional callable(str) for progress updates.

    Returns:
        List of dicts with keys: date, title, url
    """
    month_urls = _generate_month_urls(start_date, end_date)
    if not month_urls:
        return []

    all_results = []
    seen_day_urls = set()
    total_months = len(month_urls)

    for i, murl in enumerate(month_urls, 1):
        if progress_callback:
            progress_callback(f"Month {i}/{total_months}: {murl.split('month_')[-1]}")

        try:
            day_urls = _extract_day_links_from_month(murl)
        except Exception:
            continue

        for durl in day_urls:
            if durl in seen_day_urls:
                continue
            seen_day_urls.add(durl)

            try:
                results = _scrape_day(durl, keyword, start_date, end_date)
                all_results.extend(results)
            except Exception:
                continue

            time.sleep(1)
        time.sleep(1)

    return all_results
