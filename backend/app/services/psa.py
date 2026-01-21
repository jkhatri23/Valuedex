"""PSA (Professional Sports Authenticator) API service for graded card prices."""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)


class PSAService:
    """
    Service to fetch graded card prices from PSA's API.
    Provides accurate historical price data for PSA graded cards.
    """
    
    BASE_URL = "https://api.psacard.com/publicapi"
    
    def __init__(self):
        settings = get_settings()
        self.api_token = settings.psa_api_token or ""
        self.enabled = bool(self.api_token)
        self._cache: Dict[str, Dict] = {}
        
        if self.enabled:
            logger.info("PSA API enabled")
        else:
            logger.warning("PSA API not enabled - set PSA_API_TOKEN in .env")
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make authenticated request to PSA API."""
        if not self.enabled:
            return None
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=15,
            )
            
            if response.status_code == 401:
                logger.error("PSA API authentication failed - check token")
                return None
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"PSA API request failed: {e}")
            return None
    
    def get_price_guide(self, cert_number: str = None, card_name: str = None, 
                        set_name: str = None, grade: int = None) -> Optional[Dict]:
        """
        Get PSA price guide data for a card.
        Can search by cert number or card details.
        """
        cache_key = f"price_{cert_number}_{card_name}_{set_name}_{grade}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() - cached["time"] < 3600:  # 1 hour cache
                return cached["data"]
        
        # Try cert lookup first if provided
        if cert_number:
            data = self._make_request(f"cert/GetByCertNumber/{cert_number}")
            if data:
                self._cache[cache_key] = {"data": data, "time": time.time()}
                return data
        
        # Search by card details
        params = {}
        if card_name:
            params["cardName"] = card_name
        if set_name:
            params["setName"] = set_name
        if grade:
            params["grade"] = grade
        
        data = self._make_request("priceguide/GetPrices", params)
        if data:
            self._cache[cache_key] = {"data": data, "time": time.time()}
        
        return data
    
    def search_cards(self, query: str, category: str = "Pokemon") -> List[Dict]:
        """Search for cards in PSA's database."""
        cache_key = f"search_{query}_{category}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() - cached["time"] < 1800:
                return cached["data"]
        
        params = {
            "searchTerm": query,
            "category": category,
        }
        
        data = self._make_request("priceguide/SearchPriceGuide", params)
        
        if data and isinstance(data, list):
            self._cache[cache_key] = {"data": data, "time": time.time()}
            return data
        
        return []
    
    def get_price_history(self, card_name: str, set_name: str = None, 
                          grade: int = 10, months: int = 12) -> List[Dict]:
        """
        Get historical price data for a PSA graded card.
        Returns price points over time.
        """
        cache_key = f"history_{card_name}_{set_name}_{grade}_{months}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() - cached["time"] < 3600:
                logger.info(f"PSA price history cache hit for {card_name}")
                return cached["data"]
        
        logger.info(f"Fetching PSA price history for {card_name} PSA {grade}")
        
        # Search for the card first
        search_query = f"{card_name}"
        if set_name:
            search_query += f" {set_name}"
        
        cards = self.search_cards(search_query)
        
        if not cards:
            logger.warning(f"No PSA data found for {card_name}")
            return []
        
        # Find best match
        best_match = None
        for card in cards:
            card_title = (card.get("name") or card.get("cardName") or "").lower()
            if card_name.lower() in card_title:
                if set_name and set_name.lower() in card_title:
                    best_match = card
                    break
                elif not best_match:
                    best_match = card
        
        if not best_match:
            best_match = cards[0] if cards else None
        
        if not best_match:
            return []
        
        # Get price data for this card
        card_id = best_match.get("id") or best_match.get("cardId")
        
        # Try to get historical prices
        history_data = self._make_request(f"priceguide/GetPriceHistory", {
            "cardId": card_id,
            "grade": grade,
            "months": months,
        })
        
        if history_data and isinstance(history_data, list):
            result = []
            for point in history_data:
                result.append({
                    "date": point.get("date") or point.get("priceDate"),
                    "price": float(point.get("price") or point.get("avgPrice") or 0),
                    "volume": point.get("salesCount") or point.get("volume"),
                    "source": "psa_official",
                    "grade": f"PSA {grade}",
                })
            
            self._cache[cache_key] = {"data": result, "time": time.time()}
            return result
        
        # Fallback: get current prices for different grades
        prices_data = self.get_price_guide(card_name=card_name, set_name=set_name, grade=grade)
        
        if prices_data:
            # Return current price as single point
            current_price = (
                prices_data.get("price") or 
                prices_data.get("avgPrice") or 
                prices_data.get(f"psa{grade}Price") or
                0
            )
            
            if current_price:
                return [{
                    "date": datetime.now().isoformat(),
                    "price": float(current_price),
                    "volume": None,
                    "source": "psa_official",
                    "grade": f"PSA {grade}",
                }]
        
        return []
    
    def get_all_grades_prices(self, card_name: str, set_name: str = None) -> Dict[str, Dict]:
        """
        Get current PSA prices for all grades (1-10) of a card.
        """
        cache_key = f"all_grades_{card_name}_{set_name}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() - cached["time"] < 1800:
                return cached["data"]
        
        logger.info(f"Fetching PSA prices for all grades: {card_name}")
        
        result = {}
        
        # Search for the card
        search_query = f"{card_name}"
        if set_name:
            search_query += f" {set_name}"
        
        cards = self.search_cards(search_query)
        
        if not cards:
            return {}
        
        # Find best match
        best_match = None
        for card in cards:
            card_title = (card.get("name") or card.get("cardName") or "").lower()
            if card_name.lower() in card_title:
                if set_name and set_name.lower() in card_title:
                    best_match = card
                    break
                elif not best_match:
                    best_match = card
        
        if not best_match and cards:
            best_match = cards[0]
        
        if not best_match:
            return {}
        
        # Extract prices for each grade
        for grade in range(1, 11):
            grade_key = f"PSA {grade}"
            price_field = f"psa{grade}" if grade < 10 else "psa10"
            
            price = best_match.get(price_field) or best_match.get(f"grade{grade}Price")
            
            if price:
                result[grade_key] = {
                    "price": float(price),
                    "source": "psa_official",
                }
        
        # Also check for specific price fields
        if best_match.get("prices"):
            for price_entry in best_match["prices"]:
                grade = price_entry.get("grade")
                price = price_entry.get("price") or price_entry.get("avgPrice")
                if grade and price:
                    result[f"PSA {grade}"] = {
                        "price": float(price),
                        "source": "psa_official",
                    }
        
        self._cache[cache_key] = {"data": result, "time": time.time()}
        return result


psa_service = PSAService()

