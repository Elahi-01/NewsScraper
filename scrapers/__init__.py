# scrapers package
# Each module exposes a search_*() function returning List[dict]
# with normalized keys: date, title, url

from .nyt import search_nyt
from .daily_mail import search_daily_mail
from .latimes import search_latimes
from .wsj import search_wsj
from .zeit import search_zeit
from .guardian import search_guardian

__all__ = [
    "search_nyt",
    "search_daily_mail",
    "search_latimes",
    "search_wsj",
    "search_zeit",
    "search_guardian",
]
