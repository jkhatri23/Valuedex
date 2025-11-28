import logging
from typing import Optional, List

import requests

from app.config import get_settings


logger = logging.getLogger(__name__)


class EbayPriceService:
    """
    Lightweight client around eBay Finding Service (sandbox) to fetch recent sold prices.
    Uses findCompletedItems to estimate an average market value for a search query.
    """

    BASE_URL = "https://svcs.ebay.com/services/search/FindingService/v1"
    SERVICE_VERSION = "1.13.0"

    def __init__(self):
        settings = get_settings()
        self.app_id = settings.ebay_app_id
        self.enabled = bool(self.app_id)

    def _build_params(self, query: str) -> dict:
        return {
            "OPERATION-NAME": "findCompletedItems",
            "SERVICE-VERSION": self.SERVICE_VERSION,
            "SECURITY-APPNAME": self.app_id,
            "RESPONSE-DATA-FORMAT": "JSON",
            "REST-PAYLOAD": "",
            "keywords": query,
            "itemFilter(0).name": "SoldItemsOnly",
            "itemFilter(0).value": "true",
            "itemFilter(1).name": "Condition",
            "itemFilter(1).value": "Used",
            "paginationInput.entriesPerPage": "25",
            "categoryId": "183454",  # Pokemon TCG cards
        }

    def _extract_prices(self, response_json: dict) -> List[float]:
        try:
            items = (
                response_json["findCompletedItemsResponse"][0]
                ["searchResult"][0]["item"]
            )
        except (KeyError, IndexError, TypeError):
            return []

        prices: List[float] = []
        for item in items:
            try:
                price_str = (
                    item["sellingStatus"][0]["currentPrice"][0]["__value__"]
                )
                prices.append(float(price_str))
            except (KeyError, IndexError, TypeError, ValueError):
                continue
        return prices

    def _get_average_for_query(self, query: str) -> Optional[float]:
        """Internal helper to fetch an average price for an arbitrary eBay query."""
        if not self.enabled:
            return None

        try:
            response = requests.get(
                self.BASE_URL,
                params=self._build_params(query),
                timeout=10,
            )
            response.raise_for_status()
            prices = self._extract_prices(response.json())
            if not prices:
                return None
            # Simple trimmed mean to reduce outliers
            prices.sort()
            trimmed = prices[1:-1] if len(prices) > 2 else prices
            if not trimmed:
                trimmed = prices
            return round(sum(trimmed) / len(trimmed), 2)
        except requests.exceptions.RequestException as exc:
            logger.warning("EbayPriceService request failed: %s", exc)
        except Exception as exc:
            logger.error("Unexpected error in EbayPriceService: %s", exc)

        return None

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


