import base64
import logging
import time
from datetime import datetime, timezone
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
    def _search_browse_api(
        self,
        query: str,
        *,
        filter_override: Optional[str] = None,
        sort_override: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """Call Browse search endpoint and return list of item summaries."""
        token = self._get_access_token()
        if not token:
            return []

        base_params = {
            "q": query,
            "limit": str(limit),
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        filter_candidates = (
            [filter_override]
            if filter_override
            else [
                "conditions:{USED},buyingOptions:{SOLD},priceCurrency:USD",
                "conditions:{USED},priceCurrency:USD",
                "conditions:{USED}",
            ]
        )
        sort_candidates = (
            [sort_override]
            if sort_override
            else ["NEWLY_LISTED", "-price"]
        )

        attempts = 0
        max_attempts = 20

        for filter_value in filter_candidates:
            for sort_value in sort_candidates:
                if attempts >= max_attempts:
                    logger.warning(
                        "Browse API attempt limit reached (%s) for query '%s'",
                        max_attempts,
                        query,
                    )
                    return []
                
                attempts += 1
                params = dict(base_params)
                params["filter"] = filter_value
                params["sort"] = sort_value
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
                    logger.warning(
                        "Browse API request failed (%s) with filter=%s sort=%s: %s",
                        exc.response.status_code if exc.response else "HTTPError",
                        filter_value,
                        sort_value,
                        exc,
                    )
                except requests.exceptions.RequestException as exc:
                    logger.warning("Browse API request failed: %s", exc)
                except Exception as exc:
                    logger.error("Unexpected error calling Browse API: %s", exc)

        return []

    # ------------------------------------------------------------------ #
    # Title/grade helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(text.lower().split())

    def _has_grade_token(self, title: str, grade_label: str) -> bool:
        """
        Require explicit grade tokens like 'psa 7', 'psa7', or 'psa-7'.
        """
        title_norm = self._normalize(title)
        grade_norm = self._normalize(grade_label)
        psa_token = grade_norm.replace(" ", "")
        candidates = {
            grade_norm,
            psa_token,
            grade_norm.replace(" ", "-"),
            psa_token.replace("-", ""),
        }
        return any(token in title_norm for token in candidates)

    def _title_matches(
        self,
        title: str,
        card_name: str,
        set_name: Optional[str],
        grade_label: str,
    ) -> bool:
        title_norm = self._normalize(title)
        if not self._has_grade_token(title_norm, grade_label):
            return False

        card_norm = self._normalize(card_name)
        if card_norm and card_norm not in title_norm:
            return False

        if set_name:
            set_norm = self._normalize(set_name)
            if set_norm and set_norm not in title_norm:
                return False

        return True

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
        max_listings: int = 3,
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
        graded_items = [
            i
            for i in items
            if "PSA" in (i.get("title", "") or "").upper()
            and self._title_matches(i.get("title") or "", card_name, set_name, grade_label)
        ]
        return self._extract_listings(
            graded_items,
            card_name,
            set_name,
            grade_label,
            max_listings=max_listings,
        )

    def _extract_listings(
        self,
        items: List[Dict],
        card_name: str,
        set_name: Optional[str],
        grade_label: str,
        max_listings: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict]:
        listings: List[Dict] = []
        subset = items if max_listings is None else items[:max_listings]
        for item in subset:
            try:
                price_info = item.get("price") or {}
                currency = price_info.get("currency")
                value = price_info.get("value")
                if currency != "USD" or value is None:
                    continue

                end_date_raw = item.get("itemEndDate") or item.get("itemCreationDate")
                parsed_end = None
                if end_date_raw:
                    try:
                        parsed_end = datetime.fromisoformat(
                            end_date_raw.replace("Z", "+00:00")
                        )
                        if parsed_end.tzinfo:
                            parsed_end = parsed_end.astimezone(timezone.utc).replace(tzinfo=None)
                    except ValueError:
                        parsed_end = None

                if start_date and parsed_end and parsed_end < start_date:
                    continue
                if end_date and parsed_end and parsed_end > end_date:
                    continue

                listings.append(
                    {
                        "price": float(value),
                        "end_date": end_date_raw,
                        "title": item.get("title"),
                        "item_id": item.get("itemId"),
                    }
                )
            except (ValueError, TypeError):
                continue

        return listings

    def get_historical_listings_for_grade(
        self,
        card_name: str,
        set_name: Optional[str],
        grade_label: str,
        start_date: datetime,
        end_date: datetime,
        max_listings: int = 200,
    ) -> List[Dict]:
        """
        Fetch sold listings within a specific time window for a graded card.
        """
        if not self.enabled:
            return []

        start_iso = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_iso = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        query_components = [card_name]
        if set_name:
            query_components.append(set_name)
        query_components.append(grade_label)
        query_components.append("pokemon card")
        query = " ".join(filter(None, query_components))

        filter_str = (
            "conditions:{USED},buyingOptions:{SOLD},priceCurrency:USD,"
            f"itemEndDate:[{start_iso}..{end_iso}]"
        )

        items = self._search_browse_api(
            query,
            filter_override=filter_str,
            sort_override=None,
            limit=max_listings,
        )

        graded_items = [
            i
            for i in items
            if "PSA" in (i.get("title", "") or "").upper()
            and self._title_matches(i.get("title") or "", card_name, set_name, grade_label)
        ]
        return self._extract_listings(
            graded_items,
            card_name,
            set_name,
            grade_label,
            start_date=start_date.replace(tzinfo=None),
            end_date=end_date.replace(tzinfo=None),
        )

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


