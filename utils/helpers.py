"""
Shared helpers: newspaper configuration registry and result normalization.
"""

import pandas as pd

# ──────────────────────────────────────────────
# Newspaper Configuration Registry
# Central config for the UI — describes each scraper's inputs, descriptions,
# icons, and other metadata. Adding a new scraper only requires a new entry here
# and the corresponding module in scrapers/.
# ──────────────────────────────────────────────

NEWSPAPER_CONFIG = {
    "New York Times": {
        "key": "nyt",
        "emoji": "🗽",
        "color": "#1A1A1A",
        "accent": "#567B95",
        "country": "🇺🇸 United States",
        "description": (
            "Search the New York Times archive via the official Article Search API. "
            "Covers articles from 1851 to present. Large date ranges are automatically "
            "split into smaller blocks to handle API pagination limits."
        ),
        "fields": ["keyword", "begin_date", "end_date", "sort"],
        "field_labels": {
            "keyword": "Search Keyword",
            "begin_date": "Start Date (YYYYMMDD)",
            "end_date": "End Date (YYYYMMDD)",
            "sort": "Sort Order",
        },
        "field_types": {
            "keyword": "text",
            "begin_date": "text_date_yyyymmdd",
            "end_date": "text_date_yyyymmdd",
            "sort": "select",
        },
        "field_defaults": {
            "keyword": "",
            "begin_date": "20200101",
            "end_date": "20251231",
            "sort": "best",
        },
        "field_options": {
            "sort": ["best", "newest", "oldest", "relevance"],
        },
        "requires_api_key": "NYT_API_KEY",
        "api_signup_url": "https://developer.nytimes.com/",
        "notes": "Rate limited to ~5 requests/minute. Large searches may take time.",
    },
    "Daily Mail": {
        "key": "daily_mail",
        "emoji": "📰",
        "color": "#003580",
        "accent": "#0054A6",
        "country": "🇬🇧 United Kingdom",
        "description": (
            "Search the Daily Mail sitemap archive. Navigates month and day archive "
            "pages, filtering article titles by keyword. Coverage: 1994–present."
        ),
        "fields": ["keyword", "start_date", "end_date"],
        "field_labels": {
            "keyword": "Search Keyword",
            "start_date": "Start Date",
            "end_date": "End Date",
        },
        "field_types": {
            "keyword": "text",
            "start_date": "date",
            "end_date": "date",
        },
        "field_defaults": {
            "keyword": "",
            "start_date": "2020-01-01",
            "end_date": "2025-12-31",
        },
        "requires_api_key": None,
        "notes": "Fetches from HTML archive pages. May take a while for large date ranges.",
    },
    "Los Angeles Times": {
        "key": "latimes",
        "emoji": "🌴",
        "color": "#000000",
        "accent": "#D4A843",
        "country": "🇺🇸 United States",
        "description": (
            "Search the LA Times sitemap archive by year range and keywords. "
            "Navigates the sitemap hierarchy (year → month → articles) and filters "
            "by keyword matches in article titles and URLs."
        ),
        "fields": ["keywords", "start_year", "end_year"],
        "field_labels": {
            "keywords": "Keywords (comma-separated)",
            "start_year": "Start Year",
            "end_year": "End Year",
        },
        "field_types": {
            "keywords": "text",
            "start_year": "year",
            "end_year": "year",
        },
        "field_defaults": {
            "keywords": "",
            "start_year": 2020,
            "end_year": 2025,
        },
        "requires_api_key": None,
        "notes": "Keyword matching is done on article titles and URLs. Multiple keywords separated by commas.",
    },
    "The Wall Street Journal": {
        "key": "wsj",
        "emoji": "📊",
        "color": "#0274B6",
        "accent": "#0274B6",
        "country": "🇺🇸 United States",
        "description": (
            "Search the WSJ news archive by year range and keyword. "
            "Uses Selenium (headless Chrome) to render JavaScript-heavy day pages. "
            "Coverage: 1997–present."
        ),
        "fields": ["keyword", "start_year", "end_year"],
        "field_labels": {
            "keyword": "Search Keyword",
            "start_year": "Start Year",
            "end_year": "End Year",
        },
        "field_types": {
            "keyword": "text",
            "start_year": "year",
            "end_year": "year",
        },
        "field_defaults": {
            "keyword": "",
            "start_year": 2020,
            "end_year": 2025,
        },
        "requires_api_key": None,
        "notes": "Requires Selenium + Chrome. Day pages are JS-rendered, so this scraper is slower.",
    },
    "DIE ZEIT": {
        "key": "zeit",
        "emoji": "🇩🇪",
        "color": "#1D1D1B",
        "accent": "#C8102E",
        "country": "🇩🇪 Germany",
        "description": (
            "Search the DIE ZEIT weekly newspaper archive. Navigates the year index "
            "to find weekly issues, then searches article titles for keyword matches. "
            "Best for German-language keyword searches."
        ),
        "fields": ["keywords", "start_year", "end_year"],
        "field_labels": {
            "keywords": "Keywords (comma-separated)",
            "start_year": "Start Year",
            "end_year": "End Year",
        },
        "field_types": {
            "keywords": "text",
            "start_year": "year",
            "end_year": "year",
        },
        "field_defaults": {
            "keywords": "",
            "start_year": 2020,
            "end_year": 2025,
        },
        "requires_api_key": None,
        "notes": "German-language newspaper. Keywords are matched in article titles (case-insensitive).",
    },
    "The Guardian": {
        "key": "guardian",
        "emoji": "🛡️",
        "color": "#052962",
        "accent": "#0D6AA8",
        "country": "🇬🇧 United Kingdom",
        "description": (
            "Search The Guardian via the official Content API. "
            "Supports date range filtering and pagination. "
            "Returns article headlines with publication dates."
        ),
        "fields": ["keyword", "from_date", "to_date", "page_size", "max_pages"],
        "field_labels": {
            "keyword": "Search Keyword",
            "from_date": "From Date",
            "to_date": "To Date",
            "page_size": "Results Per Page",
            "max_pages": "Max Pages",
        },
        "field_types": {
            "keyword": "text",
            "from_date": "date",
            "to_date": "date",
            "page_size": "number",
            "max_pages": "number",
        },
        "field_defaults": {
            "keyword": "",
            "from_date": "2020-01-01",
            "to_date": "2025-12-31",
            "page_size": 50,
            "max_pages": 10,
        },
        "requires_api_key": "GUARDIAN_API_KEY",
        "api_signup_url": "https://open-platform.theguardian.com/access/",
        "notes": "Free API key available. Max 200 results per page, up to 50 pages.",
    },
}


def normalize_results(results: list, newspaper_name: str) -> pd.DataFrame:
    """
    Normalize scraper results into a standard DataFrame.

    All scrapers return List[dict] with keys: date, title, url.
    This function adds the newspaper name and ensures consistent columns.

    Args:
        results: List of dicts from any scraper.
        newspaper_name: Name of the newspaper source.

    Returns:
        pandas DataFrame with columns: Date, Title, URL, Newspaper
    """
    if not results:
        return pd.DataFrame(columns=["Date", "Title", "URL", "Newspaper"])

    df = pd.DataFrame(results)

    # Ensure required columns exist
    for col in ["date", "title", "url"]:
        if col not in df.columns:
            df[col] = ""

    df["newspaper"] = newspaper_name

    # Rename to display-friendly columns
    df = df.rename(columns={
        "date": "Date",
        "title": "Title",
        "url": "URL",
        "newspaper": "Newspaper",
    })

    # Keep only the standard columns
    df = df[["Date", "Title", "URL", "Newspaper"]]

    # Drop exact duplicates
    df = df.drop_duplicates(subset=["Title", "URL"])

    return df
