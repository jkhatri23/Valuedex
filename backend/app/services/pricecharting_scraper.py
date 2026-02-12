"""
PriceCharting Scraper - Get REAL historical price data from PriceCharting.com

This scrapes actual eBay sold data aggregated by PriceCharting.
Provides real historical prices for Pokemon cards across all PSA grades.
"""

import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class PriceChartingScraper:
    """Scrape historical price data from PriceCharting.com"""
    
    BASE_URL = "https://www.pricecharting.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        })
        self._cache: Dict[str, Dict] = {}
    
    def _normalize_for_url(self, name: str) -> str:
        """Convert card/set name to URL-friendly format."""
        # Lowercase
        name = name.lower()
        # URL-encode apostrophes (Blaine's -> blaine%27s) - PriceCharting keeps them
        name = name.replace("'", "%27")
        name = name.replace("'", "%27")  # Handle curly apostrophes too
        # Replace other special chars with dashes
        name = re.sub(r'[^a-z0-9%]+', '-', name)
        # Remove leading/trailing dashes
        name = name.strip('-')
        return name
    
    def _build_card_url(self, card_name: str, set_name: str, card_number: str = None) -> str:
        """Build PriceCharting URL for a Pokemon card."""
        # Map common set name variations to PriceCharting slugs
        SET_NAME_MAP = {
            "base": "base-set",
            "base set": "base-set",
            "jungle": "jungle",
            "fossil": "fossil",
            "team rocket": "team-rocket",
            "gym heroes": "gym-heroes",
            "gym challenge": "gym-challenge",
            "neo genesis": "neo-genesis",
            "neo discovery": "neo-discovery",
            "neo revelation": "neo-revelation",
            "neo destiny": "neo-destiny",
            "legendary collection": "legendary-collection",
            "base set 2": "base-set-2",
            "expedition": "expedition-base-set",
            "aquapolis": "aquapolis",
            "skyridge": "skyridge",
        }
        
        # Normalize set name
        set_lower = set_name.lower().strip()
        set_slug = SET_NAME_MAP.get(set_lower, self._normalize_for_url(set_name))
        
        if not set_slug.startswith('pokemon-'):
            set_slug = f"pokemon-{set_slug}"
        
        # Normalize card name  
        card_slug = self._normalize_for_url(card_name)
        
        # Add card number if provided
        if card_number:
            card_slug = f"{card_slug}-{card_number}"
        
        return f"{self.BASE_URL}/game/{set_slug}/{card_slug}"
    
    def search_card(self, card_name: str, set_name: str = None, card_number: str = None) -> List[Dict]:
        """Find Pokemon card URLs on PriceCharting using direct URL construction."""
        if not set_name:
            set_name = "Base Set"
        
        cache_key = f"search_{card_name}_{set_name}_{card_number}"
        if cache_key in self._cache:
            return self._cache[cache_key].get("data", [])
        
        results = []
        
        # Get the English set slug only
        set_slug = self._get_set_slug(set_name)
        card_slug = self._normalize_for_url(card_name)
        
        # Try common URL patterns for Pokemon cards
        possible_urls = []
        
        # If we have the actual card number, try it first
        if card_number:
            num = card_number.split('/')[0].strip()
            possible_urls.append(f"{self.BASE_URL}/game/{set_slug}/{card_slug}-{num}")
        
        # Then try common card numbers as fallback
        for num in [6, 4, 1, 2, 3, 5, 7, 8, 9, 10, 15, 20]:
            url = f"{self.BASE_URL}/game/{set_slug}/{card_slug}-{num}"
            if url not in possible_urls:
                possible_urls.append(url)
        
        # Also try without number
        url_no_num = f"{self.BASE_URL}/game/{set_slug}/{card_slug}"
        if url_no_num not in possible_urls:
            possible_urls.append(url_no_num)
        
        # Test each URL
        for url in possible_urls:
            try:
                response = self.session.get(url, timeout=10, allow_redirects=True)
                # Check if we got redirected to a search page (meaning URL doesn't exist)
                if 'search-products' in response.url:
                    continue
                # Skip Japanese cards - only use English card prices
                if 'japanese' in response.url.lower():
                    logger.debug(f"Skipping Japanese card URL: {response.url}")
                    continue
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'lxml')
                    title = soup.select_one('h1')
                    
                    if title:
                        title_text = title.get_text(strip=True)
                        # Skip if title indicates Japanese card
                        if 'japanese' in title_text.lower():
                            logger.debug(f"Skipping Japanese card: {title_text}")
                            continue
                        # Check if it's the right card (be more lenient with name matching)
                        card_name_simple = card_name.lower().replace("'", "").replace("'", "")
                        title_simple = title_text.lower().replace("'", "").replace("'", "")
                        if card_name_simple in title_simple:
                            is_first_ed = '1st' in title_text.lower() or 'first' in title_text.lower()
                            results.append({
                                "name": title_text,
                                "url": response.url,  # Use final URL after redirects
                                "is_first_edition": is_first_ed,
                            })
                            logger.info(f"Found card: {title_text} at {response.url}")
                            break  # Found one, stop looking
            except Exception as e:
                continue
        
        # If direct URL attempts failed, try search-based fallback
        if not results:
            logger.info(f"Direct URL failed for {card_name}, trying search fallback...")
            search_results = self._search_via_website(card_name, set_name)
            if search_results:
                results = search_results
        
        self._cache[cache_key] = {"data": results, "time": time.time()}
        return results
    
    def _search_via_website(self, card_name: str, set_name: str = None) -> List[Dict]:
        """Search for a card using PriceCharting's search page as a fallback."""
        try:
            # Build search query
            search_query = f"pokemon {card_name}"
            if set_name:
                search_query += f" {set_name}"
            
            search_url = f"{self.BASE_URL}/search-products?q={search_query.replace(' ', '+')}&type=prices"
            logger.debug(f"Searching via URL: {search_url}")
            
            response = self.session.get(search_url, timeout=15)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'lxml')
            results = []
            
            # Find search results - they're typically in table rows or links
            # PriceCharting uses various selectors for results
            result_links = soup.select('table.products a, .offer a, a[href*="/game/pokemon-"]')
            
            card_name_lower = card_name.lower().replace("'", "").replace("'", "")
            
            for link in result_links[:20]:  # Check first 20 results
                href = link.get('href', '')
                text = link.get_text(strip=True).lower()
                
                # Skip Japanese cards
                if 'japanese' in href.lower() or 'japanese' in text:
                    continue
                
                # Check if this looks like the right card
                text_simple = text.replace("'", "").replace("'", "")
                if card_name_lower in text_simple and '/game/pokemon-' in href:
                    # Build full URL if relative
                    if href.startswith('/'):
                        full_url = f"{self.BASE_URL}{href}"
                    else:
                        full_url = href
                    
                    # Verify this is the right card by checking set name if provided
                    if set_name:
                        set_lower = set_name.lower().replace(" ", "-")
                        if set_lower not in href.lower() and set_lower.replace("-", "") not in href.lower():
                            # Set doesn't match, but might still be right card
                            # Only skip if we have a better match
                            continue
                    
                    is_first_ed = '1st' in text or 'first' in text
                    results.append({
                        "name": link.get_text(strip=True),
                        "url": full_url,
                        "is_first_edition": is_first_ed,
                    })
                    logger.info(f"Found via search: {link.get_text(strip=True)} at {full_url}")
                    
                    # Return first good match
                    if results:
                        break
            
            return results
            
        except Exception as e:
            logger.warning(f"Search fallback failed: {e}")
            return []
    
    def _get_set_slug(self, set_name: str) -> str:
        """Get the PriceCharting set slug for a set name."""
        # Comprehensive mapping of set names to PriceCharting URL slugs
        SET_NAME_MAP = {
            # Base era
            "base": "pokemon-base-set",
            "base set": "pokemon-base-set",
            "jungle": "pokemon-jungle",
            "fossil": "pokemon-fossil",
            "base set 2": "pokemon-base-set-2",
            # Team Rocket era
            "team rocket": "pokemon-team-rocket",
            "team rocket returns": "pokemon-team-rocket-returns",
            # Gym era
            "gym heroes": "pokemon-gym-heroes",
            "gym challenge": "pokemon-gym-challenge",
            # Neo era
            "neo genesis": "pokemon-neo-genesis",
            "neo discovery": "pokemon-neo-discovery",
            "neo revelation": "pokemon-neo-revelation",
            "neo destiny": "pokemon-neo-destiny",
            # Legendary/e-Card era
            "legendary collection": "pokemon-legendary-collection",
            "expedition": "pokemon-expedition-base-set",
            "expedition base set": "pokemon-expedition-base-set",
            "aquapolis": "pokemon-aquapolis",
            "skyridge": "pokemon-skyridge",
            # Ruby & Sapphire era
            "ruby & sapphire": "pokemon-ruby-sapphire",
            "ruby and sapphire": "pokemon-ruby-sapphire",
            "sandstorm": "pokemon-sandstorm",
            "dragon": "pokemon-dragon",
            "team magma vs team aqua": "pokemon-team-magma-vs-team-aqua",
            "hidden legends": "pokemon-hidden-legends",
            "firered & leafgreen": "pokemon-firered-leafgreen",
            "team rocket returns": "pokemon-team-rocket-returns",
            "deoxys": "pokemon-deoxys",
            "emerald": "pokemon-emerald",
            "unseen forces": "pokemon-unseen-forces",
            "delta species": "pokemon-delta-species",
            "legend maker": "pokemon-legend-maker",
            "holon phantoms": "pokemon-holon-phantoms",
            "crystal guardians": "pokemon-crystal-guardians",
            "dragon frontiers": "pokemon-dragon-frontiers",
            "power keepers": "pokemon-power-keepers",
            # Diamond & Pearl era
            "diamond & pearl": "pokemon-diamond-pearl",
            "diamond and pearl": "pokemon-diamond-pearl",
            "mysterious treasures": "pokemon-mysterious-treasures",
            "secret wonders": "pokemon-secret-wonders",
            "great encounters": "pokemon-great-encounters",
            "majestic dawn": "pokemon-majestic-dawn",
            "legends awakened": "pokemon-legends-awakened",
            "stormfront": "pokemon-stormfront",
            # Platinum era
            "platinum": "pokemon-platinum",
            "rising rivals": "pokemon-rising-rivals",
            "supreme victors": "pokemon-supreme-victors",
            "arceus": "pokemon-arceus",
            # HeartGold SoulSilver era
            "heartgold soulsilver": "pokemon-heartgold-soulsilver",
            "heartgold & soulsilver": "pokemon-heartgold-soulsilver",
            "unleashed": "pokemon-unleashed",
            "undaunted": "pokemon-undaunted",
            "triumphant": "pokemon-triumphant",
            "call of legends": "pokemon-call-of-legends",
            # Black & White era
            "black & white": "pokemon-black-white",
            "black and white": "pokemon-black-white",
            "emerging powers": "pokemon-emerging-powers",
            "noble victories": "pokemon-noble-victories",
            "next destinies": "pokemon-next-destinies",
            "dark explorers": "pokemon-dark-explorers",
            "dragons exalted": "pokemon-dragons-exalted",
            "dragon vault": "pokemon-dragon-vault",
            "boundaries crossed": "pokemon-boundaries-crossed",
            "plasma storm": "pokemon-plasma-storm",
            "plasma freeze": "pokemon-plasma-freeze",
            "plasma blast": "pokemon-plasma-blast",
            "legendary treasures": "pokemon-legendary-treasures",
            # XY era
            "xy": "pokemon-xy",
            "flashfire": "pokemon-flashfire",
            "furious fists": "pokemon-furious-fists",
            "phantom forces": "pokemon-phantom-forces",
            "primal clash": "pokemon-primal-clash",
            "roaring skies": "pokemon-roaring-skies",
            "ancient origins": "pokemon-ancient-origins",
            "breakthrough": "pokemon-breakthrough",
            "breakpoint": "pokemon-breakpoint",
            "fates collide": "pokemon-fates-collide",
            "steam siege": "pokemon-steam-siege",
            "evolutions": "pokemon-evolutions",
            # Sun & Moon era
            "sun & moon": "pokemon-sun-moon",
            "sun and moon": "pokemon-sun-moon",
            "guardians rising": "pokemon-guardians-rising",
            "burning shadows": "pokemon-burning-shadows",
            "shining legends": "pokemon-shining-legends",
            "crimson invasion": "pokemon-crimson-invasion",
            "ultra prism": "pokemon-ultra-prism",
            "forbidden light": "pokemon-forbidden-light",
            "celestial storm": "pokemon-celestial-storm",
            "dragon majesty": "pokemon-dragon-majesty",
            "lost thunder": "pokemon-lost-thunder",
            "team up": "pokemon-team-up",
            "unbroken bonds": "pokemon-unbroken-bonds",
            "unified minds": "pokemon-unified-minds",
            "hidden fates": "pokemon-hidden-fates",
            "cosmic eclipse": "pokemon-cosmic-eclipse",
            # Sword & Shield era
            "sword & shield": "pokemon-sword-shield",
            "sword and shield": "pokemon-sword-shield",
            "rebel clash": "pokemon-rebel-clash",
            "darkness ablaze": "pokemon-darkness-ablaze",
            "champions path": "pokemon-champions-path",
            "vivid voltage": "pokemon-vivid-voltage",
            "shining fates": "pokemon-shining-fates",
            "battle styles": "pokemon-battle-styles",
            "chilling reign": "pokemon-chilling-reign",
            "evolving skies": "pokemon-evolving-skies",
            "celebrations": "pokemon-celebrations",
            "fusion strike": "pokemon-fusion-strike",
            "brilliant stars": "pokemon-brilliant-stars",
            "astral radiance": "pokemon-astral-radiance",
            "pokemon go": "pokemon-pokemon-go",
            "lost origin": "pokemon-lost-origin",
            "silver tempest": "pokemon-silver-tempest",
            "crown zenith": "pokemon-crown-zenith",
            # Scarlet & Violet era
            "scarlet & violet": "pokemon-scarlet-violet",
            "scarlet and violet": "pokemon-scarlet-violet",
            "paldea evolved": "pokemon-paldea-evolved",
            "obsidian flames": "pokemon-obsidian-flames",
            "151": "pokemon-151",
            "paradox rift": "pokemon-paradox-rift",
            "paldean fates": "pokemon-paldean-fates",
            "temporal forces": "pokemon-temporal-forces",
            "twilight masquerade": "pokemon-twilight-masquerade",
            "shrouded fable": "pokemon-shrouded-fable",
            "stellar crown": "pokemon-stellar-crown",
            "surging sparks": "pokemon-surging-sparks",
            # Promos
            "black star promos": "pokemon-black-star-promos",
            "wizards black star promos": "pokemon-wizards-black-star-promos",
            "swsh black star promos": "pokemon-swsh-black-star-promos",
            "sv black star promos": "pokemon-sv-black-star-promos",
        }
        set_lower = set_name.lower().strip()
        if set_lower in SET_NAME_MAP:
            return SET_NAME_MAP[set_lower]
        slug = self._normalize_for_url(set_name)
        if not slug.startswith('pokemon-'):
            slug = f"pokemon-{slug}"
        return slug
    
    def get_card_prices(self, url: str) -> Dict:
        """Get current prices for a card from its PriceCharting page using actual sales data."""
        try:
            # Use actual sales history for more accurate pricing
            sales_by_grade = self.get_sales_history(url)
            
            prices = {}
            
            for grade, sales in sales_by_grade.items():
                if not sales:
                    continue
                
                # Sort by date descending to get recent sales
                sorted_sales = sorted(sales, key=lambda x: x.get("date", ""), reverse=True)
                
                # Use median of recent sales (up to last 10) for stability
                recent_prices = [s["price"] for s in sorted_sales[:10]]
                if recent_prices:
                    recent_prices.sort()
                    mid = len(recent_prices) // 2
                    if len(recent_prices) % 2 == 0:
                        median_price = (recent_prices[mid-1] + recent_prices[mid]) / 2
                    else:
                        median_price = recent_prices[mid]
                    
                    # Map grade name to key
                    if grade == "Ungraded":
                        prices["ungraded"] = round(median_price, 2)
                    else:
                        prices[grade] = round(median_price, 2)
            
            # If no prices from sales history, try to scrape displayed price
            if not prices:
                logger.info(f"No sales history found, trying to scrape displayed price from {url}")
                prices = self._scrape_displayed_price(url)
            
            logger.info(f"Extracted prices: {prices}")
            return prices
            
        except Exception as e:
            logger.error(f"Failed to get prices: {e}")
            return {}
    
    def _scrape_displayed_price(self, url: str) -> Dict:
        """Scrape the displayed price from the page when sales history is unavailable."""
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return {}
            
            html = response.text
            prices = {}
            
            # Try multiple patterns used by PriceCharting
            # Pattern 1: Look for price in the main price display
            price_patterns = [
                r'class="price"[^>]*>\s*\$([0-9,.]+)',
                r'Ungraded[^$]*\$([0-9,.]+)',
                r'Loose[^$]*\$([0-9,.]+)',
                r'id="used_price"[^>]*>\s*\$([0-9,.]+)',
                r'data-price="([0-9,.]+)"',
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    try:
                        price = float(match.group(1).replace(',', ''))
                        if price > 0 and price != 6.00:  # Skip subscription price
                            prices["ungraded"] = round(price, 2)
                            break
                    except ValueError:
                        continue
            
            # Try to get graded prices
            for grade in range(1, 11):
                patterns = [
                    rf'PSA\s*{grade}[^$]*\$([0-9,.]+)',
                    rf'Grade\s*{grade}[^$]*\$([0-9,.]+)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match:
                        try:
                            price = float(match.group(1).replace(',', ''))
                            if price > 0:
                                prices[f"PSA {grade}"] = round(price, 2)
                                break
                        except ValueError:
                            continue
            
            return prices
            
        except Exception as e:
            logger.warning(f"Failed to scrape displayed price: {e}")
            return {}
    
    def _filter_outliers(self, sales: List[Dict], grade: str) -> List[Dict]:
        """
        Filter outliers using IQR method only.
        Works for any card regardless of value.
        """
        if len(sales) < 4:
            return sales
        
        prices = sorted([s["price"] for s in sales])
        
        # Calculate IQR
        q1_idx = len(prices) // 4
        q3_idx = (3 * len(prices)) // 4
        q1 = prices[q1_idx]
        q3 = prices[q3_idx]
        iqr = q3 - q1
        
        # IQR bounds (use 2.5x for tolerance - keeps most real data)
        lower_bound = max(10, q1 - 2.5 * iqr)  # Never go below $10
        upper_bound = q3 + 2.5 * iqr
        
        # Filter
        filtered = [s for s in sales if lower_bound <= s["price"] <= upper_bound]
        
        if len(filtered) < len(sales):
            removed = len(sales) - len(filtered)
            logger.info(f"{grade}: Removed {removed} outliers, kept {len(filtered)} (${lower_bound:.0f}-${upper_bound:.0f})")
        
        return filtered
    
    def get_sales_history(self, url: str) -> Dict[str, List[Dict]]:
        """
        Extract REAL sales history from PriceCharting page.
        Returns dict of grade -> list of sales with dates and prices.
        """
        cache_key = f"sales_{url}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() - cached["time"] < 1800:  # 30 min cache
                return cached["data"]
        
        try:
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Find all date cells (each represents a sale)
            date_cells = soup.select('td.date')
            logger.info(f"Found {len(date_cells)} sale entries on page")
            
            all_sales = []
            
            for date_cell in date_cells:
                date_str = date_cell.get_text(strip=True)
                
                # Get parent row
                row = date_cell.find_parent('tr')
                if not row:
                    continue
                
                row_text = row.get_text(' ', strip=True)
                
                # Find price
                price_match = re.search(r'\$([0-9,]+\.\d{2})', row_text)
                if not price_match:
                    continue
                
                price = float(price_match.group(1).replace(',', ''))
                
                # Skip subscription price (exactly $6.00) and negative prices
                if price == 6.00 or price <= 0:
                    continue
                
                # Determine PSA grade
                grade = "Ungraded"
                row_upper = row_text.upper()
                
                for g in range(10, 0, -1):
                    if f"PSA {g}" in row_upper or f"PSA{g}" in row_upper:
                        grade = f"PSA {g}"
                        break
                
                # Skip CGC/BGS for consistency
                if "CGC" in row_upper or "BGS" in row_upper:
                    continue
                
                all_sales.append({
                    "date": date_str,
                    "price": price,
                    "grade": grade,
                    "source": "pricecharting_ebay",
                })
            
            # Group by grade
            by_grade = defaultdict(list)
            for sale in all_sales:
                by_grade[sale["grade"]].append(sale)
            
            # Apply IQR outlier filtering to each grade
            result = {}
            for grade, sales in by_grade.items():
                filtered = self._filter_outliers(sales, grade)
                if filtered:
                    result[grade] = sorted(filtered, key=lambda x: x["date"])
            
            self._cache[cache_key] = {"data": result, "time": time.time()}
            
            logger.info(f"Parsed {len(all_sales)} sales, kept {sum(len(v) for v in result.values())} after filtering")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get sales history: {e}")
            return {}
    
    def get_price_history(self, url: str) -> Tuple[List[Dict], str]:
        """Legacy method - use get_sales_history for full grade breakdown."""
        sales = self.get_sales_history(url)
        
        # Return ungraded sales as default
        ungraded = sales.get("Ungraded", [])
        if ungraded:
            return ungraded, "ungraded"
        
        # Fallback to any available grade
        for grade, sales_list in sales.items():
            if sales_list:
                return sales_list, grade
        
        return [], "none"
    
    def get_card_history(
        self, 
        card_name: str, 
        set_name: str = None,
        prefer_unlimited: bool = True
    ) -> Dict:
        """
        Get complete price data for a card including history.
        
        Returns:
            {
                "card_name": str,
                "set_name": str,
                "current_prices": {grade: price},
                "history": [{date, price, source}],
                "history_type": str,  # What the history represents
            }
        """
        # Search for the card
        results = self.search_card(card_name, set_name)
        
        if not results:
            logger.warning(f"No results for {card_name} {set_name}")
            return {}
        
        # Find best match (prefer unlimited if specified)
        best_result = None
        for r in results:
            if prefer_unlimited and not r.get("is_first_edition"):
                best_result = r
                break
        
        if not best_result:
            best_result = results[0]
        
        url = best_result["url"]
        logger.info(f"Getting data from: {url}")
        
        # Get current prices
        current_prices = self.get_card_prices(url)
        
        # Get history
        history, history_type = self.get_price_history(url)
        
        return {
            "card_name": card_name,
            "set_name": set_name,
            "url": url,
            "current_prices": current_prices,
            "history": history,
            "history_type": history_type,
            "data_points": len(history),
        }


# Singleton
pricecharting_scraper = PriceChartingScraper()


def get_historical_prices(card_name: str, set_name: str = None) -> List[Dict]:
    """Convenience function to get just the price history."""
    data = pricecharting_scraper.get_card_history(card_name, set_name)
    return data.get("history", [])

