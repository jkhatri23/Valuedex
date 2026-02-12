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
        
        self._cache[cache_key] = {"data": results, "time": time.time()}
        return results
    
    def _get_set_slug(self, set_name: str) -> str:
        """Get the PriceCharting set slug for a set name."""
        SET_NAME_MAP = {
            "base": "pokemon-base-set",
            "base set": "pokemon-base-set",
            "jungle": "pokemon-jungle",
            "fossil": "pokemon-fossil",
            "team rocket": "pokemon-team-rocket",
            "gym heroes": "pokemon-gym-heroes",
            "gym challenge": "pokemon-gym-challenge",
            "neo genesis": "pokemon-neo-genesis",
            "neo discovery": "pokemon-neo-discovery",
            "neo revelation": "pokemon-neo-revelation",
            "neo destiny": "pokemon-neo-destiny",
            "legendary collection": "pokemon-legendary-collection",
            "base set 2": "pokemon-base-set-2",
            "expedition": "pokemon-expedition-base-set",
            "aquapolis": "pokemon-aquapolis",
            "skyridge": "pokemon-skyridge",
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
            
            logger.info(f"Extracted prices from sales data: {prices}")
            return prices
            
        except Exception as e:
            logger.error(f"Failed to get prices: {e}")
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

