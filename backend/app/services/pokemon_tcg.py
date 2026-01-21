"""Pokemon TCG API service for card search and images."""

import logging
import time
import requests
from typing import List, Dict, Optional
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PokemonTCGService:
    """Service to search Pokemon cards and get high-quality images from pokemontcg.io"""
    
    BASE_URL = "https://api.pokemontcg.io/v2"
    CACHE_TTL = 3600  # Cache for 1 hour
    
    def __init__(self):
        self.api_key = settings.pricecharting_api_key or settings.pokemon_tcg_api_key or ""
        self.headers = {"Content-Type": "application/json"}
        if self.api_key:
            self.headers["X-Api-Key"] = self.api_key
        self._cache: Dict[str, Dict] = {}  # {key: {"data": ..., "time": ...}}
    
    def _get_cached(self, key: str) -> Optional[any]:
        """Get cached data if not expired."""
        if key in self._cache:
            cached = self._cache[key]
            if time.time() - cached["time"] < self.CACHE_TTL:
                return cached["data"]
        return None
    
    def _set_cached(self, key: str, data: any):
        """Set cached data with timestamp."""
        self._cache[key] = {"data": data, "time": time.time()}

    def search_cards(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search for Pokemon cards by name.
        Returns cards with high-quality images from Pokemon TCG API.
        """
        cache_key = f"search_{query}_{limit}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            logger.info(f"Pokemon TCG cache hit for '{query}'")
            return cached
        
        try:
            # Search by name
            params = {
                "q": f"name:{query}*",
                "pageSize": limit,
                "orderBy": "-set.releaseDate"  # Most recent first
            }
            
            response = requests.get(
                f"{self.BASE_URL}/cards",
                params=params,
                headers=self.headers,
                timeout=15  # Increased timeout for reliability
            )
            response.raise_for_status()
            data = response.json()
            cards = data.get("data", [])
            
            results = []
            for card in cards:
                results.append(self._format_card(card))
            
            self._set_cached(cache_key, results)
            logger.info(f"Pokemon TCG API returned {len(results)} cards for '{query}'")
            return results
            
        except Exception as e:
            logger.warning(f"Pokemon TCG API search error: {e}")
            return []
    
    def get_card_by_id(self, card_id: str) -> Optional[Dict]:
        """Get a specific card by its Pokemon TCG ID (e.g., 'base1-4')."""
        cache_key = f"card_{card_id}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/cards/{card_id}",
                headers=self.headers,
                timeout=5  # Reduced timeout
            )
            response.raise_for_status()
            data = response.json()
            card = data.get("data")
            
            if card:
                result = self._format_card(card)
                self._set_cached(cache_key, result)
                return result
            return None
            
        except Exception as e:
            logger.warning(f"Pokemon TCG API get card error: {e}")
            return None
    
    def search_card_for_image(self, card_name: str, set_name: Optional[str] = None) -> Optional[str]:
        """
        Search for a card and return its image URL.
        Useful for getting images when we only have name/set from eBay.
        """
        cache_key = f"image_{card_name}_{set_name}"
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            # Build search query
            query_parts = [f"name:\"{card_name}\""]
            if set_name:
                # Try to match set name
                query_parts.append(f"set.name:\"{set_name}\"")
            
            params = {
                "q": " ".join(query_parts),
                "pageSize": 1
            }
            
            response = requests.get(
                f"{self.BASE_URL}/cards",
                params=params,
                headers=self.headers,
                timeout=3  # Very short timeout for image lookup
            )
            response.raise_for_status()
            data = response.json()
            cards = data.get("data", [])
            
            if cards:
                images = cards[0].get("images", {})
                image_url = images.get("large") or images.get("small")
                if image_url:
                    self._set_cached(cache_key, image_url)
                    return image_url
            
            # Try without set name if no results
            if set_name:
                return self.search_card_for_image(card_name, None)
            
            return None
            
        except Exception as e:
            logger.warning(f"Pokemon TCG API image search timeout/error: {e}")
            return None
    
    def _format_card(self, card: Dict) -> Dict:
        """Format card data from Pokemon TCG API."""
        images = card.get("images", {})
        set_info = card.get("set", {})
        tcgplayer = card.get("tcgplayer", {})
        
        # Extract price from tcgplayer data
        price = 0.0
        if tcgplayer and "prices" in tcgplayer:
            prices = tcgplayer["prices"]
            for price_type in ["holofoil", "normal", "reverseHolofoil", "1stEditionHolofoil"]:
                if price_type in prices:
                    price_data = prices[price_type]
                    price = price_data.get("market") or price_data.get("mid") or 0
                    if price:
                        break
        
        # Extract release year
        release_year = None
        release_date = set_info.get("releaseDate", "")
        if release_date:
            try:
                release_year = int(release_date.split("/")[0])
            except:
                pass
        
        return {
            "id": card.get("id"),
            "name": card.get("name"),
            "set_name": set_info.get("name", "Unknown"),
            "set_id": set_info.get("id"),
            "rarity": card.get("rarity"),
            "artist": card.get("artist"),
            "card_number": card.get("number"),
            "release_year": release_year,
            "image_url": images.get("large") or images.get("small"),
            "image_small": images.get("small"),
            "image_large": images.get("large"),
            "tcgplayer_url": tcgplayer.get("url"),
            "current_price": round(price, 2) if price else 0,
            "types": card.get("types", []),
            "hp": card.get("hp"),
            "supertype": card.get("supertype"),
        }


pokemon_tcg_service = PokemonTCGService()

