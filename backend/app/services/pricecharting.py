import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.config import get_settings
import time

settings = get_settings()

class PriceChartingService:
    BASE_URL = "https://www.pricecharting.com/api"
    
    def __init__(self):
        self.api_key = settings.pricecharting_api_key
        self.use_real_api = bool(self.api_key and self.api_key.strip())
        
    def search_cards(self, query: str, limit: int = 20) -> List[Dict]:
        """Search for Pokemon cards using PriceCharting API"""
        if not self.use_real_api:
            print(f"[INFO] No API key found - using mock data for: {query}")
            return self._get_mock_search_results(query)
        
        try:
            url = f"{self.BASE_URL}/products"
            params = {
                "q": query,
                "t": "pokemon-cards",  # Product type
                "apikey": self.api_key
            }
            
            print(f"[API] Searching PriceCharting for: {query}")
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if "products" in data:
                products = data["products"]
                print(f"[API] Found {len(products)} cards from PriceCharting")
                
                # Transform to our format
                results = []
                for product in products[:limit]:
                    results.append({
                        "id": product.get("id", ""),
                        "product-name": product.get("product-name", ""),
                        "console-name": product.get("console-name", "Pokemon Cards"),
                        "loose-price": float(product.get("loose-price", 0) or 0),
                        "cib-price": float(product.get("cib-price", 0) or 0),
                        "new-price": float(product.get("new-price", 0) or 0),
                        "image": self._get_card_image(product.get("product-name", ""))
                    })
                return results
            else:
                print(f"[API] No products found, using mock data")
                return self._get_mock_search_results(query)
                
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] PriceCharting API error: {e}")
            print(f"[INFO] Falling back to mock data")
            return self._get_mock_search_results(query)
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            return self._get_mock_search_results(query)
    
    def get_card_prices(self, product_id: str) -> Dict:
        """Get detailed price data for a specific card"""
        if not self.use_real_api:
            return self._get_mock_price_data()
        
        try:
            # Get product details
            url = f"{self.BASE_URL}/product"
            params = {
                "t": "pokemon-cards",
                "id": product_id,
                "apikey": self.api_key
            }
            
            print(f"[API] Fetching price details for: {product_id}")
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            print(f"[API] Retrieved price data successfully")
            return data
            
        except Exception as e:
            print(f"[ERROR] Failed to fetch price data: {e}")
            return self._get_mock_price_data()
    
    def _get_card_image(self, card_name: str) -> str:
        """Generate Pokemon TCG image URL based on card name"""
        # Try to match with Pokemon TCG API images
        card_lower = card_name.lower()
        
        # Map common cards to their image URLs
        image_map = {
            "charizard": "https://images.pokemontcg.io/base1/4_hires.png",
            "pikachu": "https://images.pokemontcg.io/base1/58_hires.png",
            "blastoise": "https://images.pokemontcg.io/base1/2_hires.png",
            "venusaur": "https://images.pokemontcg.io/base1/15_hires.png",
            "mewtwo": "https://images.pokemontcg.io/base1/10_hires.png",
            "mew": "https://images.pokemontcg.io/base1/53_hires.png",
            "gyarados": "https://images.pokemontcg.io/base1/6_hires.png",
            "alakazam": "https://images.pokemontcg.io/base1/1_hires.png",
            "machamp": "https://images.pokemontcg.io/base1/8_hires.png",
            "magneton": "https://images.pokemontcg.io/base1/9_hires.png",
        }
        
        # Check for known cards
        for pokemon, url in image_map.items():
            if pokemon in card_lower:
                return url
        
        # Default placeholder
        return "https://images.pokemontcg.io/base1/58.png"
    
    def _get_mock_search_results(self, query: str) -> List[Dict]:
        """Comprehensive mock data for testing without API key"""
        mock_cards = [
            # Base Set
            {
                "id": "charizard-base-set-holo",
                "product-name": "Charizard Holo",
                "console-name": "Base Set",
                "loose-price": 350.00,
                "cib-price": 450.00,
                "new-price": 550.00,
                "image": "https://images.pokemontcg.io/base1/4_hires.png"
            },
            {
                "id": "pikachu-base-set",
                "product-name": "Pikachu",
                "console-name": "Base Set",
                "loose-price": 5.00,
                "cib-price": 8.00,
                "new-price": 12.00,
                "image": "https://images.pokemontcg.io/base1/58_hires.png"
            },
            {
                "id": "blastoise-base-set-holo",
                "product-name": "Blastoise Holo",
                "console-name": "Base Set",
                "loose-price": 120.00,
                "cib-price": 180.00,
                "new-price": 250.00,
                "image": "https://images.pokemontcg.io/base1/2_hires.png"
            },
            {
                "id": "venusaur-base-set-holo",
                "product-name": "Venusaur Holo",
                "console-name": "Base Set",
                "loose-price": 100.00,
                "cib-price": 150.00,
                "new-price": 220.00,
                "image": "https://images.pokemontcg.io/base1/15_hires.png"
            },
            {
                "id": "mewtwo-base-set-holo",
                "product-name": "Mewtwo Holo",
                "console-name": "Base Set",
                "loose-price": 45.00,
                "cib-price": 70.00,
                "new-price": 95.00,
                "image": "https://images.pokemontcg.io/base1/10_hires.png"
            },
            {
                "id": "alakazam-base-set-holo",
                "product-name": "Alakazam Holo",
                "console-name": "Base Set",
                "loose-price": 35.00,
                "cib-price": 55.00,
                "new-price": 75.00,
                "image": "https://images.pokemontcg.io/base1/1_hires.png"
            },
            {
                "id": "gyarados-base-set-holo",
                "product-name": "Gyarados Holo",
                "console-name": "Base Set",
                "loose-price": 40.00,
                "cib-price": 60.00,
                "new-price": 85.00,
                "image": "https://images.pokemontcg.io/base1/6_hires.png"
            },
            # Add more popular cards
            {
                "id": "lugia-neo-genesis",
                "product-name": "Lugia Holo",
                "console-name": "Neo Genesis",
                "loose-price": 180.00,
                "cib-price": 250.00,
                "new-price": 380.00,
                "image": "https://images.pokemontcg.io/base1/10_hires.png"
            },
            {
                "id": "espeon-ex",
                "product-name": "Espeon ex",
                "console-name": "EX Series",
                "loose-price": 85.00,
                "cib-price": 120.00,
                "new-price": 175.00,
                "image": "https://images.pokemontcg.io/base1/58_hires.png"
            },
            {
                "id": "umbreon-ex",
                "product-name": "Umbreon ex",
                "console-name": "EX Series",
                "loose-price": 95.00,
                "cib-price": 135.00,
                "new-price": 195.00,
                "image": "https://images.pokemontcg.io/base1/58_hires.png"
            },
        ]
        
        # Filter by query
        if query:
            query_lower = query.lower()
            filtered = [c for c in mock_cards if query_lower in c["product-name"].lower()]
            if filtered:
                return filtered
        
        # Return all if no match or no query
        return mock_cards if not query else mock_cards[:5]
    
    def _get_mock_price_data(self) -> Dict:
        """Mock price history data with realistic trends"""
        # Generate 12 months of price history
        base_price = 350.00
        prices = []
        current_date = datetime.now()
        
        for i in range(12):
            date = current_date - timedelta(days=(12-i) * 30)
            # Add some realistic variance
            variance = 0.85 + (i / 12) * 0.25  # Slight upward trend
            price = base_price * variance
            prices.append({
                "date": date.strftime("%Y-%m-%d"),
                "price": round(price, 2)
            })
        
        return {
            "product-name": "Pokemon Card",
            "console-name": "Pokemon Cards",
            "prices": prices
        }

# Create a singleton instance
pricecharting_service = PriceChartingService()

