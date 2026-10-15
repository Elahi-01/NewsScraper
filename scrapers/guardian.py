"""
The Guardian Content API scraper.
Uses the Guardian Open Platform API.
Inputs: keyword, from_date, to_date (YYYY-MM-DD), page_size, max_pages.
"""

import os
import requests
from datetime import datetime

API_KEY = os.getenv("GUARDIAN_API_KEY", "")
BASE_URL = "https://content.guardianapis.com/search"


def search_guardian(keyword: str, from_date: str = "", to_date: str = "",
                    page_size: int = 50, max_pages: int = 10,
                    progress_callback=None) -> list:
    """
    Search The Guardian Content API.

    Args:
        keyword: Search term.
        from_date: Start date as YYYY-MM-DD (optional).
        to_date: End date as YYYY-MM-DD (optional).
        page_size: Results per page (10-200).
        max_pages: Maximum pages to fetch.
        progress_callback: Optional callable(str) for progress updates.

    Returns:
        List of dicts with keys: date, title, url
    """
    if not API_KEY:
        raise ValueError("GUARDIAN_API_KEY environment variable is not set. "
                         "Get one at https://open-platform.theguardian.com/access/")

    params = {
        "q": keyword,
        "api-key": API_KEY,
        "show-fields": "headline",
        "page-size": page_size,
        "order-by": "newest",
    }
    if from_date:
        params["from-date"] = from_date
    if to_date:
        params["to-date"] = to_date

    all_results = []
    page = 1

    while page <= max_pages:
        params["page"] = page

        if progress_callback:
            progress_callback(f"Fetching page {page}/{max_pages}...")

        resp = requests.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        response = data.get("response", {})
        results = response.get("results", [])
        if not results:
            break

        for item in results:
            date_raw = item.get("webPublicationDate", "")
            title = item.get("fields", {}).get("headline", "")
            article_url = item.get("webUrl", "")

            # Parse date to YYYY-MM-DD
            if date_raw:
                try:
                    dt = datetime.fromisoformat(
                        date_raw.replace("Z", "+00:00")
                    )
                    date_str = dt.date().isoformat()
                except Exception:
                    date_str = date_raw[:10]
            else:
                date_str = ""

            all_results.append({
                "date": date_str,
                "title": title,
                "url": article_url,
            })

        total_pages = response.get("pages", page)
        if page >= total_pages:
            break
        page += 1

    if progress_callback:
        progress_callback(f"Fetched {len(all_results)} articles total.")

    return all_results
