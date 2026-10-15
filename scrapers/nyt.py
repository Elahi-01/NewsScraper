"""
New York Times Article Search scraper.
Uses the NYT Article Search API v2.
Inputs: keyword, begin_date (YYYYMMDD), end_date (YYYYMMDD), sort order.
Supports smart date-range splitting for large historical ranges.
"""

import os
import time
import requests

API_KEY = os.getenv("NYT_API_KEY", "")
BASE_URL = "https://api.nytimes.com/svc/search/v2/articlesearch.json"


def _search_nyt_range(keyword: str, begin_date: str, end_date: str,
                      sort: str = "best", max_pages: int = 100,
                      sleep_sec: float = 12, progress_callback=None) -> list:
    """Fetch articles for a single date range from the NYT API."""
    all_results = []

    for page in range(max_pages):
        params = {
            "q": keyword,
            "sort": sort,
            "page": page,
            "api-key": API_KEY,
            "begin_date": begin_date,
            "end_date": end_date,
        }

        r = requests.get(BASE_URL, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()

        if progress_callback:
            progress_callback(f"Range {begin_date}-{end_date}, page {page}")

        if "response" not in data or "docs" not in data["response"]:
            break

        docs = data["response"]["docs"]
        if not docs:
            break

        for d in docs:
            all_results.append({
                "date": d.get("pub_date", "")[:10],
                "title": d.get("headline", {}).get("main", ""),
                "url": d.get("web_url", ""),
            })

        time.sleep(sleep_sec)

    return all_results


def _build_custom_ranges(begin_date: str, end_date: str) -> list:
    """
    Split a large date range into smaller blocks:
    - 1850-1949: 50-year blocks
    - 1950-2000: 10-year blocks
    - 2000+: 5-year blocks
    """
    by, bm, bd = int(begin_date[:4]), int(begin_date[4:6]), int(begin_date[6:8])
    ey, em, ed = int(end_date[:4]), int(end_date[4:6]), int(end_date[6:8])

    ranges = []

    # 1850-1949 portion (50-year step)
    if ey >= 1850:
        cur_start = max(by, 1850)
        while cur_start <= min(1949, ey):
            block_end_year = min(ey, cur_start + 49, 1949)
            b = f"{cur_start:04d}{bm:02d}{bd:02d}"
            e = f"{block_end_year:04d}{em:02d}{ed:02d}"
            ranges.append((b, e))
            cur_start = block_end_year + 1
            if block_end_year >= ey or block_end_year >= 1949:
                break

    # 1950-2000 portion (10-year step)
    if ey >= 1950:
        cur_start = max(by, 1950)
        while cur_start <= min(2000, ey):
            block_end_year = min(ey, cur_start + 9, 2000)
            b = f"{cur_start:04d}{bm:02d}{bd:02d}"
            e = f"{block_end_year:04d}{em:02d}{ed:02d}"
            ranges.append((b, e))
            cur_start = block_end_year + 1
            if block_end_year >= ey or block_end_year >= 2000:
                break

    # 2000+ portion (5-year step)
    if ey > 2000:
        cur_start = max(by, 2000)
        while cur_start <= ey:
            block_end_year = min(ey, cur_start + 4)
            b = f"{cur_start:04d}{bm:02d}{bd:02d}"
            e = f"{block_end_year:04d}{em:02d}{ed:02d}"
            ranges.append((b, e))
            cur_start = block_end_year + 1

    # Clamp to [begin_date, end_date]
    cleaned = []
    for b, e in ranges:
        if e < begin_date or b > end_date:
            continue
        b2 = max(b, begin_date)
        e2 = min(e, end_date)
        if not cleaned or cleaned[-1][1] < b2:
            cleaned.append((b2, e2))
        else:
            cleaned[-1] = (cleaned[-1][0], max(cleaned[-1][1], e2))

    return cleaned


def search_nyt(keyword: str, begin_date: str, end_date: str,
               sort: str = "best", use_splits: bool = True,
               max_pages: int = 100, sleep_sec: float = 12,
               progress_callback=None) -> list:
    """
    Search the New York Times Article Search API.

    Args:
        keyword: Search term.
        begin_date: Start date as YYYYMMDD string.
        end_date: End date as YYYYMMDD string.
        sort: Sort order — 'best', 'newest', 'oldest', 'relevance'.
        use_splits: If True, split large date ranges into smaller blocks.
        max_pages: Max API pages to fetch per range block (max 100).
        sleep_sec: Seconds to sleep between API calls (rate limit).
        progress_callback: Optional callable(str) for progress updates.

    Returns:
        List of dicts with keys: date, title, url
    """
    if not API_KEY:
        raise ValueError("NYT_API_KEY environment variable is not set. "
                         "Get one at https://developer.nytimes.com/")

    if use_splits:
        ranges = _build_custom_ranges(begin_date, end_date)
    else:
        ranges = [(begin_date, end_date)]

    all_results = []
    for b, e in ranges:
        res = _search_nyt_range(
            keyword=keyword,
            begin_date=b,
            end_date=e,
            sort=sort,
            max_pages=max_pages,
            sleep_sec=sleep_sec,
            progress_callback=progress_callback,
        )
        all_results.extend(res)

    # Deduplicate by URL
    seen = set()
    unique = []
    for r in all_results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)

    return unique
