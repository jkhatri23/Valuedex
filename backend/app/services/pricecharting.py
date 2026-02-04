"""PriceCharting API service for Pokemon card data."""

import requests
from typing import List, Dict, Optional
from app.config import get_settings

settings = get_settings()


class PriceChartingService:
    BASE_URL = "https://www.pricecharting.com/api"
    
    def __init__(self):
        self.api_key = settings.pricecharting_api_key or ""
        self._cache: Dict = {}
    
    def search_cards(self, query: str, limit: int = 20) -> List[Dict]:
        """Search for Pokemon cards."""
        cache_key = f"search_{query}_{limit}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        if not self.api_key:
            return []
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/products",
                params={"t": self.api_key, "q": f"{query} pokemon"},
                timeout=15
            )
            response.raise_for_status()
            products = response.json().get("products", [])
            
            results = []
            for p in products[:limit]:
                results.append({
                    "id": str(p.get("id", "")),
                    "product-name": p.get("product-name", ""),
                    "console-name": p.get("console-name", "Pokemon Cards"),
                    "loose-price": float(p.get("loose-price", 0)) / 100.0,
                    "cib-price": float(p.get("cib-price", 0)) / 100.0,
                    "new-price": float(p.get("new-price", 0)) / 100.0,
                    "image": p.get("image", ""),
                })
            
            self._cache[cache_key] = results
            return results
        except Exception:
            return []
    
    def get_card_by_id(self, card_id: str) -> Optional[Dict]:
        """Get card details by ID."""
        cache_key = f"card_{card_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        product = self.get_card_prices(card_id)
        if not product:
            return self._find_in_cache(card_id)
        
        result = {
            "id": str(product.get("id", card_id)),
            "product-name": product.get("product-name", ""),
            "console-name": product.get("console-name", "Pokemon Cards"),
            "loose-price": float(product.get("loose-price", 0)) / 100.0,
            "cib-price": float(product.get("cib-price", 0)) / 100.0,
            "new-price": float(product.get("new-price", 0)) / 100.0,
            "image": product.get("image", ""),
            "rarity": product.get("rarity"),
            "artist": product.get("artist"),
            "number": product.get("product-id", product.get("id")),
            "set_release": product.get("release-date"),
        }
        
        self._cache[cache_key] = result
        return result
    
    def get_card_prices(self, product_id: str) -> Dict:
        """Get price data for a card."""
        if not self.api_key:
            return {}
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/product",
                params={"t": self.api_key, "id": product_id},
                timeout=15
            )
            response.raise_for_status()
            return response.json()
        except Exception:
            return {}
    
    def _find_in_cache(self, card_id: str) -> Optional[Dict]:
        """Find card in search cache."""
        for key, data in self._cache.items():
            if key.startswith("search_") and isinstance(data, list):
                for card in data:
                    if card.get("id") == card_id:
                        return card
        return None


pricecharting_service = PriceChartingService()
