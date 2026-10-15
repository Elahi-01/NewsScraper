"""
DIE ZEIT Archive scraper.
Navigates the ZEIT year-index pages (year → issues → articles).
Inputs: keywords (comma-separated), start_year, end_year.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_YEAR_INDEX = "https://www.zeit.de/{year}/index"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/123.0 Safari/537.36"
    )
}


def _get_issue_links_for_year(year: int, progress_callback=None) -> list:
    """Fetch issue index links for a given year."""
    url = BASE_YEAR_INDEX.format(year=year)
    if progress_callback:
        progress_callback(f"Year index: {url}")

    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    issue_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if f"/{year}/" in href and href.endswith("/index"):
            issue_links.append(urljoin("https://www.zeit.de", href))

    issue_links = sorted(set(issue_links))
    if progress_callback:
        progress_callback(f"  Found {len(issue_links)} issues for {year}")
    return issue_links


def _title_matches(title: str, keywords: list) -> bool:
    """Check if any keyword appears in the title (case-insensitive)."""
    t = title.lower()
    return any(kw.lower() in t for kw in keywords if kw.strip())


def _parse_issue_page(issue_url: str, year: int, keywords: list,
                      progress_callback=None) -> list:
    """Parse an issue index page and extract matching articles."""
    if progress_callback:
        progress_callback(f"    Issue page: {issue_url}")

    r = requests.get(issue_url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    issue_part = issue_url.rstrip("/").split("/")[-2]
    main = soup.find("main") or soup

    rows = []
    for block in main.find_all(["article", "div", "li"]):
        a = block.find("a", href=True)
        if not a:
            continue

        title = a.get_text(strip=True)
        if not title:
            continue

        if not _title_matches(title, keywords):
            continue

        href = urljoin("https://www.zeit.de", a["href"])

        # Try to extract date from a <time> element
        time_el = block.find("time")
        if time_el and time_el.get("datetime"):
            date_text = time_el["datetime"][:10]  # Take YYYY-MM-DD part
        elif time_el:
            date_text = time_el.get_text(strip=True)
        else:
            date_text = ""

        rows.append({
            "date": date_text,
            "title": title,
            "url": href,
        })

    if progress_callback:
        progress_callback(f"      -> {len(rows)} matches in this issue")
    return rows


def search_zeit(keywords: str, start_year: int, end_year: int,
                progress_callback=None) -> list:
    """
    Search the DIE ZEIT archive by keywords and year range.

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

    all_results = []

    for year in range(start_year, end_year + 1):
        try:
            issue_links = _get_issue_links_for_year(year, progress_callback)
        except Exception as e:
            if progress_callback:
                progress_callback(f"Failed to load year {year}: {e}")
            continue

        for issue_url in issue_links:
            try:
                rows = _parse_issue_page(
                    issue_url, year, keyword_list, progress_callback
                )
                all_results.extend(rows)
            except Exception as e:
                if progress_callback:
                    progress_callback(f"  Failed issue {issue_url}: {e}")

    return all_results
