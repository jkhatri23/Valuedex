import base64
import logging
import time
from typing import Optional, List, Dict

import requests

from app.config import get_settings


logger = logging.getLogger(__name__)


class EbayPriceService:
    """
    Lightweight client around eBay's Browse API to estimate market value for
    card/grade combinations.

    We previously used the legacy Finding API, but eBay now recommends Browse as the
    alternative. This client:
      - Fetches an OAuth client-credentials token
      - Calls /buy/browse/v1/item_summary/search with the query
      - Computes a trimmed mean of returned listing prices
    """

    BROWSE_BASE_URL = "https://api.ebay.com"
    OAUTH_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
    OAUTH_SCOPE = "https://api.ebay.com/oauth/api_scope"

    def __init__(self):
        settings = get_settings()
        self.app_id = settings.ebay_app_id
        self.cert_id = settings.ebay_cert_id
        self.enabled = bool(self.app_id)
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0.0

        if self.enabled and not self.cert_id:
            logger.warning("EBAY_APP_ID is set but EBAY_CERT_ID is missing; Browse API calls will fail.")

    # ------------------------------------------------------------------ #
    # OAuth helpers
    # ------------------------------------------------------------------ #
    def _get_access_token(self) -> Optional[str]:
        """Fetch (or reuse) an OAuth token for the Browse API."""
        if not self.enabled or not self.cert_id:
            return None

        if self._access_token and time.time() < self._token_expiry:
            return self._access_token

        basic = base64.b64encode(f"{self.app_id}:{self.cert_id}".encode()).decode()
        headers = {
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "client_credentials",
            "scope": self.OAUTH_SCOPE,
        }

        try:
            resp = requests.post(self.OAUTH_TOKEN_URL, headers=headers, data=data, timeout=10)
            resp.raise_for_status()
            payload = resp.json()
            token = payload.get("access_token")
            expires_in = payload.get("expires_in", 0)
            if token:
                self._access_token = token
                self._token_expiry = time.time() + max(int(expires_in) - 60, 0)
                return token
        except Exception as exc:
            logger.error("Failed to obtain eBay OAuth token: %s", exc)
            self._access_token = None
            self._token_expiry = 0

        return None

    # ------------------------------------------------------------------ #
    # Browse search helpers
    # ------------------------------------------------------------------ #
    def _search_browse_api(self, query: str) -> List[Dict]:
        """Call Browse search endpoint and return list of item summaries."""
        token = self._get_access_token()
        if not token:
            return []

        params = {
            "q": query,
            "limit": "50",
            "sort": "-price",
            # Filter for Used / collectible cards. This keeps PSA slabs + NM cards.
            "filter": "conditions:{USED}",
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            resp = requests.get(
                f"{self.BROWSE_BASE_URL}/buy/browse/v1/item_summary/search",
                params=params,
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("itemSummaries", [])
        except requests.exceptions.HTTPError as exc:
            logger.warning("Browse API request failed (%s): %s", exc.response.status_code if exc.response else "HTTPError", exc)
        except requests.exceptions.RequestException as exc:
            logger.warning("Browse API request failed: %s", exc)
        except Exception as exc:
            logger.error("Unexpected error calling Browse API: %s", exc)
        return []

    def _get_average_for_query(self, query: str) -> Optional[float]:
        """Internal helper to fetch an average price for an arbitrary eBay query."""
        if not self.enabled:
            return None

        items = self._search_browse_api(query)
        prices: List[float] = []
        for item in items:
            try:
                price_info = item.get("price") or {}
                currency = price_info.get("currency")
                value = price_info.get("value")
                if currency != "USD" or value is None:
                    continue
                prices.append(float(value))
            except (ValueError, TypeError):
                continue
        if not prices:
            return None
        prices.sort()
        trimmed = prices[1:-1] if len(prices) > 2 else prices
        if not trimmed:
            trimmed = prices
        return round(sum(trimmed) / len(trimmed), 2)

    def get_average_price(self, card_name: str, set_name: Optional[str] = None) -> Optional[float]:
        """
        Average loose/market price for an ungraded card based on recent sold listings.
        """
        if not self.enabled:
            return None

        query_components = [card_name]
        if set_name:
            query_components.append(set_name)
        query_components.append("pokemon card")
        query = " ".join(filter(None, query_components))
        return self._get_average_for_query(query)

    def get_listing_prices_for_grade(
        self,
        card_name: str,
        set_name: Optional[str],
        grade_label: str,
        max_listings: int = 15,
    ) -> List[Dict]:
        """
        Return individual listing prices (and end dates) for a given grade.
        """
        if not self.enabled:
            return []

        query_components = [card_name]
        if set_name:
            query_components.append(set_name)
        query_components.append(grade_label)
        query_components.append("pokemon card")
        query = " ".join(filter(None, query_components))

        items = self._search_browse_api(query)
        listings: List[Dict] = []

        for item in items[:max_listings]:
            try:
                price_info = item.get("price") or {}
                currency = price_info.get("currency")
                value = price_info.get("value")
                if currency != "USD" or value is None:
                    continue

                end_date = item.get("itemEndDate") or item.get("itemCreationDate")
                listings.append(
                    {
                        "price": float(value),
                        "end_date": end_date,
                        "title": item.get("title"),
                        "item_id": item.get("itemId"),
                    }
                )
            except (ValueError, TypeError):
                continue

        return listings

    def get_average_price_for_grade(
        self,
        card_name: str,
        set_name: Optional[str],
        grade_label: str,
    ) -> Optional[float]:
        """
        Average sold price for a specific graded condition (e.g. 'PSA 9').

        This just tightens the keyword query by including the grade label, so
        you'll typically want to pass values like 'Near Mint', 'PSA 8', etc.
        """
        if not self.enabled:
            return None

        query_components = [card_name]
        if set_name:
            query_components.append(set_name)
        query_components.append(grade_label)
        query_components.append("pokemon card")
        query = " ".join(filter(None, query_components))
        return self._get_average_for_query(query)


ebay_price_service = EbayPriceService()


