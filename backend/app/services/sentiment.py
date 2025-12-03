import logging
import threading
import time
from typing import Optional

from pytrends.request import TrendReq

logger = logging.getLogger(__name__)


class MarketSentimentService:
    """
    Wrapper around Google Trends (pytrends) to calculate a simple
    market sentiment score (0-100) for a card / keyword.
    """

    def __init__(self):
        self.pytrends = TrendReq(hl="en-US", tz=360)
        self.cache = {}
        self.cache_ttl = 60 * 60 * 6  # 6 hours
        self.lock = threading.Lock()

    def _fetch_interest(self, term: str) -> Optional[float]:
        """
        Query Google Trends for the given term and return the most recent
        interest score (0-100). Returns None if data cannot be fetched.
        """
        try:
            self.pytrends.build_payload([term], timeframe="today 3-m")
            data = self.pytrends.interest_over_time()
            if data.empty:
                return None

            # Column name can be sanitized by pytrends; grab first column
            column = [col for col in data.columns if col != "isPartial"]
            if not column:
                return None

            series = data[column[0]]
            value = float(series.iloc[-1])
            if value == 0 and series.mean() > 0:
                value = float(series.mean())
            return round(value, 2)
        except Exception as exc:
            logger.warning("Failed to fetch Google Trends data for %s: %s", term, exc)
            return None

    def get_sentiment_score(self, card_name: Optional[str]) -> float:
        """Return a sentiment score for the card (0-100, default 50)."""
        if not card_name:
            return 50.0

        key = card_name.lower().strip()
        if not key:
            return 50.0

        now = time.time()

        with self.lock:
            cached = self.cache.get(key)
            if cached and now - cached["ts"] < self.cache_ttl:
                return cached["value"]

        score = self._fetch_interest(card_name) or 50.0

        with self.lock:
            self.cache[key] = {"value": score, "ts": now}

        return score


sentiment_service = MarketSentimentService()


