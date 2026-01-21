import base64
import logging
import re
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Tuple

import requests

from app.config import get_settings


logger = logging.getLogger(__name__)


# Standard PSA grades for Pokemon cards
PSA_GRADES = ["PSA 10", "PSA 9", "PSA 8", "PSA 7", "PSA 6", "PSA 5", "PSA 4", "PSA 3", "PSA 2", "PSA 1"]
# Rarity keywords to detect in listings
RARITY_KEYWORDS = {
    "secret rare": "Secret Rare",
    "ultra rare": "Ultra Rare",
    "full art": "Ultra Rare",
    "alt art": "Ultra Rare",
    "alternate art": "Ultra Rare",
    "illustration rare": "Ultra Rare",
    "special art": "Ultra Rare",
    "holo rare": "Holo Rare",
    "holo": "Holo Rare",
    "reverse holo": "Reverse Holo",
    "rare": "Rare",
    "uncommon": "Uncommon",
    "common": "Common",
    "promo": "Promo",
    "1st edition": "1st Edition",
    "first edition": "1st Edition",
    "shadowless": "Shadowless",
}


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
        self.enabled = bool(self.app_id and self.cert_id)
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0.0
        self._history_cache: Dict[str, Dict] = {}  # Cache for price history
        self._price_cache: Dict[str, Dict] = {}  # Cache for current prices

        if self.app_id and not self.cert_id:
            logger.warning("EBAY_APP_ID is set but EBAY_CERT_ID is missing; Browse API calls will fail.")
        
        if self.enabled:
            logger.info("eBay API enabled with App ID: %s...", self.app_id[:20] if self.app_id else "None")
        else:
            logger.warning("eBay API NOT enabled - check EBAY_APP_ID and EBAY_CERT_ID in .env")

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
            logger.info("Requesting eBay OAuth token...")
            resp = requests.post(self.OAUTH_TOKEN_URL, headers=headers, data=data, timeout=10)
            resp.raise_for_status()
            payload = resp.json()
            token = payload.get("access_token")
            expires_in = payload.get("expires_in", 0)
            if token:
                self._access_token = token
                self._token_expiry = time.time() + max(int(expires_in) - 60, 0)
                logger.info("eBay OAuth token obtained successfully (expires in %s seconds)", expires_in)
                return token
            else:
                logger.error("eBay OAuth response missing access_token: %s", payload)
        except requests.exceptions.HTTPError as exc:
            logger.error("eBay OAuth HTTP error: %s - Response: %s", exc, exc.response.text if exc.response else "No response")
            self._access_token = None
            self._token_expiry = 0
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

    def build_price_history(
        self,
        card_name: str,
        set_name: Optional[str] = None,
        grade: Optional[str] = None,
        months_back: int = 12,
    ) -> List[Dict]:
        """
        Build price history from ACTUAL eBay sold/completed listings.
        Returns real transaction data with quality filtering.
        """
        if not self.enabled:
            logger.warning("eBay service not enabled for price history")
            return []

        # Check cache first
        cache_key = f"history_v2_{card_name}_{set_name}_{grade}_{months_back}"
        if cache_key in self._history_cache:
            cached = self._history_cache[cache_key]
            if time.time() - cached["time"] < 1800:  # 30 min cache
                logger.info(f"Price history cache hit for {card_name}")
                return cached["data"]

        logger.info(f"Fetching eBay sold data for {card_name} ({set_name}) grade={grade}")
        
        # Build precise search query for UNLIMITED edition only (most consistent)
        query_components = [f'"{card_name}"']
        if set_name:
            query_components.append(f'"{set_name}"')
        if grade and grade != "Near Mint":
            query_components.append(grade)
        
        # Strict exclusions - be aggressive to get clean data
        exclusions = "-lot -bundle -collection -binder -repack -mystery -bulk -1st -first -shadowless -proxy -fake -damaged"
        query_components.append("pokemon card unlimited")
        query_components.append(exclusions)
        query = " ".join(filter(None, query_components))
        
        all_listings: List[Dict] = []
        
        # Fetch from eBay
        filter_options = [
            "priceCurrency:USD,deliveryCountry:US",
            "priceCurrency:USD",
        ]
        
        for filter_str in filter_options:
            for sort in ["price", "-price", "NEWLY_LISTED"]:
                items = self._search_browse_api(
                    query,
                    filter_override=filter_str,
                    sort_override=sort,
                    limit=100,
                )
                
                if items:
                    for item in items:
                        listing = self._extract_listing_with_date(item, card_name, set_name, grade)
                        if listing and listing not in all_listings:
                            all_listings.append(listing)
                    
                    logger.info(f"Got {len(items)} items (sort={sort})")
            
            if len(all_listings) >= 30:
                break
        
        if not all_listings:
            logger.warning(f"No eBay listings found for {card_name}")
            return []
        
        logger.info(f"Found {len(all_listings)} total eBay listings")
        
        # Build price history with quality filtering
        price_history = self._build_real_price_history(all_listings, months_back)
        
        # Cache the result
        self._history_cache[cache_key] = {"data": price_history, "time": time.time()}
        
        logger.info(f"Built price history with {len(price_history)} data points")
        return price_history

    def _build_real_price_history(
        self,
        listings: List[Dict],
        months_back: int = 12,
    ) -> List[Dict]:
        """
        Build price history from ACTUAL eBay data.
        Filters to UNLIMITED edition only for consistent pricing.
        """
        from collections import defaultdict
        
        if not listings:
            return []
        
        # Filter to UNLIMITED edition only (most common, most consistent pricing)
        unlimited_listings = [l for l in listings if l.get("edition") == "unlimited"]
        
        # If not enough unlimited, use all but note it
        if len(unlimited_listings) >= 5:
            listings = unlimited_listings
            logger.info(f"Using {len(listings)} UNLIMITED edition listings")
        else:
            logger.info(f"Only {len(unlimited_listings)} unlimited, using all {len(listings)} listings")
        
        # Filter extreme outliers using IQR
        all_prices = sorted([l["price"] for l in listings if l.get("price", 0) > 0])
        if len(all_prices) >= 4:
            q1 = all_prices[len(all_prices) // 4]
            q3 = all_prices[3 * len(all_prices) // 4]
            iqr = q3 - q1
            min_price = max(q1 - 1.5 * iqr, 1)
            max_price = q3 + 1.5 * iqr
            
            filtered = [l for l in listings if min_price <= l.get("price", 0) <= max_price]
            if len(filtered) >= 3:
                listings = filtered
            logger.info(f"After IQR filter: {len(listings)} listings (${min_price:.0f}-${max_price:.0f})")
        
        # Group by week
        weekly_data: Dict[str, List[Dict]] = defaultdict(list)
        for listing in listings:
            if listing.get("date"):
                week_start = listing["date"] - timedelta(days=listing["date"].weekday())
                week_key = week_start.strftime("%Y-%m-%d")
                weekly_data[week_key].append(listing)
        
        # Build result with REAL prices (median per week)
        result = []
        for week_key in sorted(weekly_data.keys()):
            week_listings = weekly_data[week_key]
            prices = sorted([l["price"] for l in week_listings])
            
            # Use median price
            median_price = prices[len(prices) // 2]
            
            # Get editions in this week
            editions = list(set(l.get("edition", "unknown") for l in week_listings))
            
            result.append({
                "date": f"{week_key}T00:00:00",
                "price": round(median_price, 2),
                "volume": len(prices),
                "min_price": round(min(prices), 2),
                "max_price": round(max(prices), 2),
                "source": "ebay_sold",
                "editions": editions,
            })
        
        # If we don't have weekly data, show individual points
        if len(result) < 3:
            result = []
            for listing in sorted(listings, key=lambda x: x.get("date", datetime.now())):
                if listing.get("date"):
                    result.append({
                        "date": listing["date"].strftime("%Y-%m-%dT%H:%M:%S"),
                        "price": round(listing["price"], 2),
                        "volume": 1,
                        "source": "ebay_sold",
                        "edition": listing.get("edition", "unknown"),
                        "title": listing.get("title", "")[:60],
                    })
        
        return result


    def _extract_listing_with_date(
        self,
        item: Dict,
        card_name: str,
        set_name: Optional[str],
        grade: Optional[str],
    ) -> Optional[Dict]:
        """Extract price and date from a listing item with strict filtering."""
        try:
            price_info = item.get("price", {})
            if price_info.get("currency") != "USD":
                return None
            
            value = price_info.get("value")
            if not value:
                return None
            
            price = float(value)
            if price <= 0:
                return None
            
            title = item.get("title", "")
            title_lower = title.lower()
            
            # STRICT FILTERS - exclude non-card items
            exclude_keywords = [
                "proxy", "custom", "reprint", "fake", "replica",
                "sleeve", "case", "holder", "binder", "toploader",
                "lot of", "bundle", "collection", "mystery", "pack",
                "damaged", "poor", "creased", "bent", "torn",
                "digital", "online", "ptcgo", "code",
                "sticker", "decal", "poster", "art print",
            ]
            if any(kw in title_lower for kw in exclude_keywords):
                return None
            
            # Card name must be in title
            if card_name.lower() not in title_lower:
                return None
            
            # Set name should match if specified
            if set_name and set_name.lower() not in title_lower:
                # Allow partial matches for set names
                set_words = set_name.lower().split()
                if not any(w in title_lower for w in set_words if len(w) > 3):
                    return None
            
            # Filter by grade if specified
            if grade and grade != "Near Mint":
                grade_upper = grade.upper()
                title_upper = title.upper()
                # Must have exact grade match
                if grade_upper not in title_upper:
                    return None
                # For PSA grades, verify the number matches
                if "PSA" in grade_upper:
                    import re
                    grade_num = re.search(r'PSA\s*(\d+)', grade_upper)
                    title_grade = re.search(r'PSA\s*(\d+)', title_upper)
                    if grade_num and title_grade:
                        if grade_num.group(1) != title_grade.group(1):
                            return None
            
            # Price sanity check - filter obvious non-cards
            # A real vintage card is worth at least $10, PSA graded at least $50
            min_price = 10
            if grade and "PSA" in grade.upper():
                min_price = 50
            if price < min_price:
                return None
            
            # Detect edition (important for price variance)
            edition = "unlimited"
            if "1st edition" in title_lower or "1st ed" in title_lower or "first edition" in title_lower:
                edition = "1st_edition"
            elif "shadowless" in title_lower:
                edition = "shadowless"
            
            # Get date - prefer itemEndDate (sold date)
            date_str = item.get("itemEndDate") or item.get("itemCreationDate")
            
            # Parse date
            parsed_date = datetime.now()
            if date_str:
                try:
                    if "T" in date_str:
                        parsed_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        if parsed_date.tzinfo:
                            parsed_date = parsed_date.astimezone(timezone.utc).replace(tzinfo=None)
                except:
                    parsed_date = datetime.now()
            
            # Only include data from reasonable time range (last 2 years)
            two_years_ago = datetime.now() - timedelta(days=730)
            if parsed_date < two_years_ago:
                parsed_date = datetime.now()  # Treat old dates as current listings
            
            return {
                "price": price,
                "date": parsed_date,
                "title": title,
                "item_id": item.get("itemId"),
                "edition": edition,
            }
            
        except (ValueError, TypeError) as e:
            return None



    # ------------------------------------------------------------------ #
    # Card Search & Data Methods (replacing PriceCharting)
    # ------------------------------------------------------------------ #
    def search_cards(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search for Pokemon cards on eBay and return structured card data.
        This replaces the PriceCharting search functionality.
        """
        if not self.enabled:
            logger.warning("eBay service not enabled - missing credentials")
            return []

        # Check cache first
        cache_key = f"search_{query}_{limit}"
        if cache_key in self._price_cache:
            cached = self._price_cache[cache_key]
            if time.time() - cached["time"] < 600:  # 10 min cache for searches
                logger.info("eBay search cache hit for '%s'", query)
                return cached["data"]

        search_query = f"{query} pokemon card -lot -bundle -repack"
        logger.info("eBay searching for: %s", search_query)
        
        items = self._search_browse_api(search_query, limit=min(limit * 2, 60))  # Reduced
        
        logger.info("eBay returned %d items", len(items) if items else 0)
        
        if not items:
            return []

        # Group items by card identity (name + set) and extract unique cards
        seen_cards: Dict[str, Dict] = {}
        
        for item in items:
            card_data = self._extract_card_data_from_listing(item)
            if not card_data:
                continue
            
            # Create a unique key based on card name and set
            name = card_data.get('name') or card_data.get('product-name') or ''
            set_name = card_data.get('set_name') or card_data.get('console-name') or 'unknown'
            if not name:
                continue
            card_key = f"{name.lower()}_{set_name.lower()}"
            
            if card_key not in seen_cards:
                seen_cards[card_key] = card_data
            else:
                # Update with better data if available (e.g., image, price)
                existing = seen_cards[card_key]
                if not existing.get('image') and card_data.get('image'):
                    existing['image'] = card_data['image']
                # Collect prices to average later
                if 'prices' not in existing:
                    existing['prices'] = []
                existing['prices'].append(card_data.get('loose-price', 0))

        # Format results
        results = []
        for card_key, card_data in list(seen_cards.items())[:limit]:
            # Calculate average price if we collected multiple
            if 'prices' in card_data and card_data['prices']:
                prices = [p for p in card_data['prices'] if p > 0]
                if prices:
                    card_data['loose-price'] = round(sum(prices) / len(prices), 2)
                del card_data['prices']
            
            results.append(card_data)

        # Cache the results
        self._price_cache[cache_key] = {"data": results, "time": time.time()}
        
        return results

    def _extract_card_data_from_listing(self, item: Dict) -> Optional[Dict]:
        """Extract structured card data from an eBay listing."""
        title = item.get("title", "")
        if not title:
            return None

        # Extract card name and set from title
        card_name, set_name = self._parse_card_title(title)
        if not card_name:
            return None

        # Extract price
        price = 0.0
        price_info = item.get("price", {})
        if price_info.get("currency") == "USD":
            try:
                price = float(price_info.get("value", 0))
            except (ValueError, TypeError):
                pass

        # Extract rarity
        rarity = self._extract_rarity_from_title(title)

        # Extract grade if present
        grade = self._extract_grade_from_title(title)

        # Get image
        image_info = item.get("image", {})
        image_url = image_info.get("imageUrl", "") if isinstance(image_info, dict) else ""
        
        # Generate a unique ID based on card identity
        card_id = self._generate_card_id(card_name, set_name)

        return {
            "id": card_id,
            "product-name": card_name,
            "console-name": set_name or "Pokemon Cards",
            "loose-price": price if not grade else 0,  # Only set if ungraded
            "cib-price": price if grade else 0,  # Set if graded
            "new-price": 0,
            "image": image_url,
            "rarity": rarity,
            "grade": grade,
            "ebay_item_id": item.get("itemId"),
            "name": card_name,
            "set_name": set_name,
        }

    def _parse_card_title(self, title: str) -> Tuple[str, Optional[str]]:
        """Parse card name and set name from eBay listing title."""
        title_clean = title.strip()
        
        # Remove common suffixes and prefixes
        remove_patterns = [
            r'\s*-\s*pokemon\s*(tcg|card|trading card game)?\s*$',
            r'\s*pokemon\s*(tcg|card)?\s*-?\s*',
            r'\s*\(.*?\)\s*',  # Remove parenthetical info
            r'\s*\[.*?\]\s*',  # Remove bracketed info
            r'\bNM\b.*$',
            r'\bLP\b.*$',
            r'\bMP\b.*$',
            r'\bHP\b.*$',
            r'\bPSA\s*\d+\b',
            r'\bCGC\s*\d+\.?\d*\b',
            r'\bBGS\s*\d+\.?\d*\b',
            r'\b(Near Mint|Lightly Played|Moderately Played|Heavily Played)\b',
            r'\bFREE\s+SHIPPING\b',
            r'\b(HOT|SALE|NEW|RARE|VINTAGE)\b',
        ]
        
        processed = title_clean
        for pattern in remove_patterns:
            processed = re.sub(pattern, ' ', processed, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        processed = ' '.join(processed.split())
        
        # Try to extract set name from common patterns
        set_name = None
        set_patterns = [
            r'(\d+/\d+)\s*',  # Card number like "4/102"
            r'\b(Base Set|Jungle|Fossil|Team Rocket|Gym Heroes|Gym Challenge)\b',
            r'\b(Neo Genesis|Neo Discovery|Neo Revelation|Neo Destiny)\b',
            r'\b(Legendary Collection|Expedition|Aquapolis|Skyridge)\b',
            r'\b(Ruby & Sapphire|Sandstorm|Dragon|Team Magma vs Team Aqua)\b',
            r'\b(Hidden Legends|FireRed & LeafGreen|Team Rocket Returns)\b',
            r'\b(Deoxys|Emerald|Unseen Forces|Delta Species)\b',
            r'\b(Legend Maker|Holon Phantoms|Crystal Guardians|Dragon Frontiers)\b',
            r'\b(Power Keepers|Diamond & Pearl|Mysterious Treasures|Secret Wonders)\b',
            r'\b(Great Encounters|Majestic Dawn|Legends Awakened|Stormfront)\b',
            r'\b(Platinum|Rising Rivals|Supreme Victors|Arceus)\b',
            r'\b(HeartGold & SoulSilver|Unleashed|Undaunted|Triumphant)\b',
            r'\b(Call of Legends|Black & White|Emerging Powers|Noble Victories)\b',
            r'\b(Next Destinies|Dark Explorers|Dragons Exalted|Boundaries Crossed)\b',
            r'\b(Plasma Storm|Plasma Freeze|Plasma Blast|Legendary Treasures)\b',
            r'\b(XY|Flashfire|Furious Fists|Phantom Forces)\b',
            r'\b(Primal Clash|Roaring Skies|Ancient Origins|BREAKthrough)\b',
            r'\b(BREAKpoint|Fates Collide|Steam Siege|Evolutions)\b',
            r'\b(Sun & Moon|Guardians Rising|Burning Shadows|Crimson Invasion)\b',
            r'\b(Ultra Prism|Forbidden Light|Celestial Storm|Lost Thunder)\b',
            r'\b(Team Up|Unbroken Bonds|Unified Minds|Hidden Fates)\b',
            r'\b(Cosmic Eclipse|Sword & Shield|Rebel Clash|Darkness Ablaze)\b',
            r'\b(Champions Path|Vivid Voltage|Shining Fates|Battle Styles)\b',
            r'\b(Chilling Reign|Evolving Skies|Celebrations|Fusion Strike)\b',
            r'\b(Brilliant Stars|Astral Radiance|Pokemon GO|Lost Origin)\b',
            r'\b(Silver Tempest|Crown Zenith|Scarlet & Violet|Paldea Evolved)\b',
            r'\b(Obsidian Flames|151|Paradox Rift|Paldean Fates|Temporal Forces)\b',
            r'\b(Twilight Masquerade|Shrouded Fable|Stellar Crown|Surging Sparks)\b',
        ]
        
        for pattern in set_patterns:
            match = re.search(pattern, title_clean, re.IGNORECASE)
            if match:
                set_name = match.group(1) if match.lastindex else match.group(0)
                break
        
        # Extract Pokemon name (usually the first major word/phrase)
        # Remove numbers and special chars from the beginning
        card_name = re.sub(r'^[\d\s#]+', '', processed).strip()
        
        # Try to get just the Pokemon name (usually 1-2 words at the start)
        words = card_name.split()
        if len(words) > 3:
            # Try to identify the Pokemon name
            card_name = ' '.join(words[:2])  # Take first 2 words as likely Pokemon name
        
        return card_name.strip() if card_name else None, set_name

    def _extract_rarity_from_title(self, title: str) -> str:
        """Extract rarity from listing title."""
        title_lower = title.lower()
        
        # Check for specific rarity keywords (check more specific first)
        for keyword, rarity in sorted(RARITY_KEYWORDS.items(), key=lambda x: -len(x[0])):
            if keyword in title_lower:
                return rarity
        
        return "Unknown"

    def _extract_grade_from_title(self, title: str) -> Optional[str]:
        """Extract PSA/CGC/BGS grade from title."""
        title_upper = title.upper()
        
        # PSA grades
        psa_match = re.search(r'\bPSA\s*(\d+)\b', title_upper)
        if psa_match:
            return f"PSA {psa_match.group(1)}"
        
        # CGC grades
        cgc_match = re.search(r'\bCGC\s*(\d+\.?\d*)\b', title_upper)
        if cgc_match:
            return f"CGC {cgc_match.group(1)}"
        
        # BGS grades
        bgs_match = re.search(r'\bBGS\s*(\d+\.?\d*)\b', title_upper)
        if bgs_match:
            return f"BGS {bgs_match.group(1)}"
        
        return None

    def _generate_card_id(self, card_name: str, set_name: Optional[str]) -> str:
        """Generate a unique card ID."""
        import hashlib
        base = f"{card_name}_{set_name or 'unknown'}".lower()
        return hashlib.md5(base.encode()).hexdigest()[:12]

    def get_card_by_id(self, card_id: str, card_name: str = None, set_name: str = None) -> Optional[Dict]:
        """
        Get card details by searching eBay for a specific card.
        Since eBay doesn't have static IDs like PriceCharting, we search by name/set.
        """
        if not self.enabled:
            return None

        # If we have a card name, search for it
        if card_name:
            search_query = f"{card_name}"
            if set_name:
                search_query += f" {set_name}"
            search_query += " pokemon card -lot -bundle"
            
            items = self._search_browse_api(search_query, limit=20)
            
            if not items:
                return None

            # Get prices across different grades
            prices_by_grade = self._get_prices_by_grade(items, card_name, set_name)
            
            # Get the first valid item for base data
            for item in items:
                card_data = self._extract_card_data_from_listing(item)
                if card_data:
                    card_data['prices_by_grade'] = prices_by_grade
                    card_data['id'] = card_id
                    return card_data

        return None

    def _get_prices_by_grade(self, items: List[Dict], card_name: str, set_name: Optional[str]) -> Dict[str, Dict]:
        """Extract prices organized by grade from listing items."""
        grade_prices: Dict[str, List[float]] = {}
        
        for item in items:
            title = item.get("title", "")
            grade = self._extract_grade_from_title(title)
            
            price_info = item.get("price", {})
            if price_info.get("currency") != "USD":
                continue
            
            try:
                price = float(price_info.get("value", 0))
            except (ValueError, TypeError):
                continue
            
            if price <= 0:
                continue
            
            grade_key = grade or "Ungraded"
            if grade_key not in grade_prices:
                grade_prices[grade_key] = []
            grade_prices[grade_key].append(price)
        
        # Calculate averages
        result = {}
        for grade, prices in grade_prices.items():
            if prices:
                prices.sort()
                # Trimmed mean
                trimmed = prices[1:-1] if len(prices) > 2 else prices
                if trimmed:
                    avg = sum(trimmed) / len(trimmed)
                else:
                    avg = prices[0]
                result[grade] = {
                    "average_price": round(avg, 2),
                    "min_price": round(min(prices), 2),
                    "max_price": round(max(prices), 2),
                    "count": len(prices),
                }
        
        return result

    def get_card_prices(self, card_name: str, set_name: Optional[str] = None) -> Dict:
        """
        Get comprehensive price data for a card including prices by grade.
        """
        if not self.enabled:
            return {}

        # Check cache first
        cache_key = f"prices_{card_name}_{set_name}"
        if cache_key in self._price_cache:
            cached = self._price_cache[cache_key]
            if time.time() - cached["time"] < 900:  # 15 min cache
                return cached["data"]

        search_query = f"{card_name}"
        if set_name:
            search_query += f" {set_name}"
        search_query += " pokemon card"
        
        items = self._search_browse_api(search_query, limit=30)  # Reduced from 50
        
        if not items:
            return {}

        prices_by_grade = self._get_prices_by_grade(items, card_name, set_name)
        
        # Get overall loose (ungraded) price
        ungraded_data = prices_by_grade.get("Ungraded", {})
        loose_price = ungraded_data.get("average_price", 0)
        
        result = {
            "loose-price": loose_price * 100,  # Return in cents like PriceCharting
            "prices_by_grade": prices_by_grade,
            "rarity": self._extract_rarity_from_title(card_name),
        }
        
        # Cache the result
        self._price_cache[cache_key] = {"data": result, "time": time.time()}
        
        return result

    def search_cards_with_grades(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search for cards and include grade-specific pricing information.
        """
        if not self.enabled:
            return []

        # First get base card list
        cards = self.search_cards(query, limit)
        
        # For each card, try to get grade-specific pricing
        for card in cards:
            card_name = card.get("name") or card.get("product-name")
            set_name = card.get("set_name") or card.get("console-name")
            
            # Get prices by grade (limited search)
            search_query = f"{card_name} {set_name or ''} pokemon card PSA".strip()
            graded_items = self._search_browse_api(search_query, limit=30)
            
            if graded_items:
                prices_by_grade = self._get_prices_by_grade(graded_items, card_name, set_name)
                card['prices_by_grade'] = prices_by_grade

        return cards


ebay_price_service = EbayPriceService()


