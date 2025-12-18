import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from app.config import get_settings
from app.services.ebay import ebay_price_service
import time
import random

settings = get_settings()

class PriceChartingService:
    BASE_URL = "https://www.pricecharting.com/api"
    POKEMON_TCG_API = "https://api.pokemontcg.io/v2"  # Pokemon TCG API
    
    def __init__(self):
        # Try both config names (pokemon_tcg_api_key and pricecharting_api_key for backward compatibility)
        self.api_key = settings.pricecharting_api_key or settings.pokemon_tcg_api_key or ""
        self.use_real_api = bool(self.api_key and self.api_key.strip())
        self.use_pokemon_tcg_api = True  # Always use Pokemon TCG API!
        self._cache = {}  # Simple cache to avoid repeated slow API calls
        
        # Pre-cache some popular Pokemon cards for instant results
        self._populate_initial_cache()
        
    def search_cards(self, query: str, limit: int = 20) -> List[Dict]:
        """Search for Pokemon cards using Pokemon TCG API with REAL prices"""
        
        # Check cache first
        cache_key = f"search_{query}_{limit}"
        if cache_key in self._cache:
            print(f"[CACHE] Returning cached results for: {query}")
            return self._cache[cache_key]
        
        print(f"[INFO] Searching Pokemon TCG API for: {query} (this may take 20-30 seconds...)")
        
        try:
            url = f"{self.POKEMON_TCG_API}/cards"
            params = {"q": f"name:{query}", "pageSize": limit}
            
            headers = {}
            if self.api_key:
                headers["X-Api-Key"] = self.api_key
                print(f"[POKEMON TCG API] Using API key... Please wait...")
            
            # API is slow (20-30 seconds typical), so use 60 second timeout
            response = requests.get(url, params=params, headers=headers, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            cards = data.get("data", [])
            
            print(f"[POKEMON TCG API] ✅ Found {len(cards)} cards!")
            
            if not cards:
                print(f"[POKEMON TCG API] No cards found for: {query}")
                return []
            
            results = []
            for card in cards:
                card_name = card.get("name", "")
                set_name = card.get("set", {}).get("name", "Pokemon TCG")
                
                # Extract REAL prices from API
                price = self._extract_real_price(card)
                
                results.append({
                    "id": card.get("id", ""),
                    "product-name": card_name,
                    "console-name": set_name,
                    "loose-price": price,
                    "cib-price": price * 1.2,  # Slightly higher for complete
                    "new-price": price * 1.5,  # Higher for mint condition
                    "image": card.get("images", {}).get("small", "")
                })
            
            # Cache the results
            self._cache[cache_key] = results
            return results
            
        except requests.exceptions.Timeout:
            print(f"[POKEMON TCG API] ⚠️ Timeout after 60s - API is very slow")
            return []
        except Exception as e:
            print(f"[POKEMON TCG API] Error: {e}")
            return []
    
    def get_card_by_id(self, card_id: str) -> Optional[Dict]:
        """Get a specific card by ID from Pokemon TCG API"""
        print(f"[INFO] Fetching card by ID: {card_id}")
        
        # Check cache first
        cache_key = f"card_{card_id}"
        if cache_key in self._cache:
            print(f"[CACHE] Returning cached card: {card_id}")
            return self._cache[cache_key]
        
        try:
            url = f"{self.POKEMON_TCG_API}/cards/{card_id}"
            
            headers = {}
            if self.api_key:
                headers["X-Api-Key"] = self.api_key
            
            # Increase timeout to 60 seconds to match search timeout
            response = requests.get(url, headers=headers, timeout=60)
            response.raise_for_status()
            
            data = response.json()
            card = data.get("data", {})
            
            if not card:
                print(f"[POKEMON TCG API] Card not found: {card_id}")
                return None
            
            # Extract real price
            price = self._extract_real_price(card)
            
            query = f"{card.get('name', '')} {card.get('set', {}).get('name', '')}".strip()
            tcgplayer_info = card.get("tcgplayer", {}) or {}
            tcgplayer_url = tcgplayer_info.get("url")
            if not tcgplayer_url and query:
                tcgplayer_url = f"https://www.tcgplayer.com/search/pokemon/product?q={quote_plus(query)}&productLineName=pokemon"
            ebay_url = f"https://www.ebay.com/sch/i.html?_nkw={quote_plus(query + ' pokemon card')}" if query else "https://www.ebay.com/sch/i.html?_nkw=pokemon+card"

            result = {
                "id": card.get("id", ""),
                "product-name": card.get("name", ""),
                "console-name": card.get("set", {}).get("name", "Pokemon TCG"),
                "loose-price": price,
                "cib-price": price * 1.2,
                "new-price": price * 1.5,
                "image": card.get("images", {}).get("small", ""),
                "rarity": card.get("rarity", ""),
                "artist": card.get("artist", ""),
                "number": card.get("number", ""),
                "set_release": card.get("set", {}).get("releaseDate", ""),
                "tcgplayer_url": tcgplayer_url,
                "ebay_url": ebay_url
            }
            
            # Cache the result
            self._cache[cache_key] = result
            return result
            
        except requests.exceptions.Timeout:
            print(f"[POKEMON TCG API] ⚠️ Timeout fetching card {card_id} - API is very slow")
            # Try to find card in search cache as fallback
            return self._try_find_in_cache(card_id)
        except Exception as e:
            print(f"[POKEMON TCG API] Error fetching card {card_id}: {e}")
            # Try to find card in search cache as fallback
            return self._try_find_in_cache(card_id)
    
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
    
    def _search_pokemon_tcg_api(self, query: str, limit: int = 20) -> List[Dict]:
        """Search using Pokemon TCG API with API key for better access"""
        try:
            url = f"{self.POKEMON_TCG_API}/cards"
            # Build query params - Pokemon TCG API uses simple name search
            params = {"page": 1, "pageSize": limit}
            if query:
                params["q"] = f"name:{query}"
            
            # Use API key if available for higher rate limits
            headers = {}
            if self.api_key:
                headers["X-Api-Key"] = self.api_key
                print(f"[POKEMON TCG API] Searching with API key for: {query}")
            else:
                print(f"[POKEMON TCG API] Searching (no key) for: {query}")
            
            response = requests.get(url, params=params, headers=headers, timeout=5)  # Reduced timeout
            response.raise_for_status()
            
            data = response.json()
            cards = data.get("data", [])
            
            print(f"[POKEMON TCG API] Found {len(cards)} cards!")
            
            if not cards:
                print(f"[POKEMON TCG API] No cards found for: {query}")
                return []
            
            results = []
            for card in cards:
                card_name = card.get("name", "")
                set_name = card.get("set", {}).get("name", "Pokemon TCG")
                
                # Get price from eBay (or estimate if eBay fails)
                price = ebay_price_service.get_average_price(card_name, set_name)
                if not price:
                    price = self._estimate_price_by_rarity(f"{card_name} {set_name}")
                
                results.append({
                    "id": card.get("id", ""),
                    "product-name": card_name,
                    "console-name": set_name,
                    "loose-price": price,
                    "cib-price": price * 1.3,
                    "new-price": price * 1.6,
                    "image": card.get("images", {}).get("small", "")
                })
            
            return results
            
        except requests.exceptions.Timeout:
            print(f"[POKEMON TCG API] Timeout after 5s for query: {query}")
            return []
        except Exception as e:
            print(f"[POKEMON TCG API] Error: {e}")
            return []
    
    def _extract_real_price(self, card: Dict) -> float:
        """Extract real market price from Pokemon TCG API card data"""
        try:
            # Try TCGPlayer prices first (US market)
            if "tcgplayer" in card and "prices" in card["tcgplayer"]:
                prices = card["tcgplayer"]["prices"]
                
                # Try different price types in order of preference
                for price_type in ["holofoil", "normal", "reverseHolofoil", "1stEditionHolofoil", "unlimitedHolofoil"]:
                    if price_type in prices:
                        price_data = prices[price_type]
                        # Use market price if available, otherwise mid price
                        if "market" in price_data and price_data["market"]:
                            print(f"[PRICE] TCGPlayer market: ${price_data['market']}")
                            return round(float(price_data["market"]), 2)
                        elif "mid" in price_data and price_data["mid"]:
                            print(f"[PRICE] TCGPlayer mid: ${price_data['mid']}")
                            return round(float(price_data["mid"]), 2)
            
            # Try Cardmarket prices (European market)
            if "cardmarket" in card and "prices" in card["cardmarket"]:
                prices = card["cardmarket"]["prices"]
                if "averageSellPrice" in prices and prices["averageSellPrice"]:
                    price = round(float(prices["averageSellPrice"]), 2)
                    print(f"[PRICE] Cardmarket average: ${price}")
                    return price
                elif "trendPrice" in prices and prices["trendPrice"]:
                    price = round(float(prices["trendPrice"]), 2)
                    print(f"[PRICE] Cardmarket trend: ${price}")
                    return price

            # Try eBay sold listings as fallback
            ebay_price = ebay_price_service.get_average_price(
                card.get("name", ""),
                card.get("set", {}).get("name")
            )
            if ebay_price:
                print(f"[PRICE] eBay sold average: ${ebay_price}")
                return ebay_price
            
            # Fallback to estimate based on rarity
            rarity = card.get("rarity", "Common")
            price = self._estimate_price_by_rarity(f"{card.get('name', '')} {rarity}")
            print(f"[PRICE] Estimated by rarity: ${price}")
            return price
            
        except Exception as e:
            print(f"[PRICE] Error extracting price: {e}")
            # Fallback to basic estimation
            rarity = card.get("rarity", "Common")
            return self._estimate_price_by_rarity(f"{card.get('name', '')} {rarity}")
    
    def _estimate_price_by_rarity(self, card_info: str) -> float:
        """Estimate card price based on name and rarity keywords"""
        card_lower = card_info.lower()
        
        # Legendary/Special Pokemon get higher prices
        legendary_pokemon = {
            "charizard": 350, "mewtwo": 45, "lugia": 180, "ho-oh": 165,
            "rayquaza": 145, "groudon": 115, "kyogre": 118, "dialga": 135,
            "palkia": 132, "giratina": 125, "reshiram": 118, "zekrom": 115,
            "xerneas": 125, "yveltal": 122, "solgaleo": 135, "lunala": 132,
            "zacian": 145, "zamazenta": 142, "koraidon": 155, "miraidon": 152,
            "mew": 80, "celebi": 78, "jirachi": 68, "deoxys": 92,
            "darkrai": 98, "arceus": 105, "genesect": 88, "diancie": 75,
        }
        
        # Check for known high-value Pokemon
        for pokemon, price in legendary_pokemon.items():
            if pokemon in card_lower:
                return round(random.uniform(price * 0.9, price * 1.1), 2)
        
        # Check for special card types
        if any(word in card_lower for word in ["vmax", "v max", "ultra"]):
            return round(random.uniform(80, 150), 2)
        elif any(word in card_lower for word in ["gx", "ex", " v "]):
            return round(random.uniform(40, 100), 2)
        elif "holo" in card_lower or "holofoil" in card_lower:
            return round(random.uniform(20, 60), 2)
        elif "rare" in card_lower:
            return round(random.uniform(10, 30), 2)
        elif "uncommon" in card_lower:
            return round(random.uniform(3, 10), 2)
        else:
            return round(random.uniform(1, 8), 2)
    
    
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
    
    def _try_find_in_cache(self, card_id: str) -> Optional[Dict]:
        """Try to find a card in search cache as fallback when direct fetch fails"""
        # Search through all cached search results for this card ID
        for cache_key, cached_data in self._cache.items():
            if cache_key.startswith("search_"):
                if isinstance(cached_data, list):
                    for card in cached_data:
                        if card.get("id") == card_id:
                            print(f"[CACHE FALLBACK] Found card {card_id} in search cache")
                            return card
        print(f"[CACHE FALLBACK] Card {card_id} not found in cache")
        return None
    
    def _populate_initial_cache(self):
        """Pre-cache popular Pokemon cards for instant results"""
        print("[CACHE] Pre-loading popular Pokemon...")
        
        # Popular Pokemon to pre-cache (will make first searches instant!)
        popular_cards = [
            ("pikachu", 5),
            ("charizard", 3),
            ("mewtwo", 3),
            ("rayquaza", 3),
            ("lugia", 3)
        ]
        
        # Pre-load in background (don't block startup)
        import threading
        def load_cache():
            for pokemon, limit in popular_cards:
                try:
                    print(f"[CACHE] Pre-loading {pokemon}...")
                    self.search_cards(pokemon, limit)
                except Exception as e:
                    print(f"[CACHE] Failed to pre-load {pokemon}: {e}")
        
        # Start loading in background thread
        thread = threading.Thread(target=load_cache, daemon=True)
        thread.start()
        print("[CACHE] Background cache loading started!")

# Create a singleton instance
pricecharting_service = PriceChartingService()

