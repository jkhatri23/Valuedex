"""
Pokemon TCG API Database Sync Service
Populates and updates PostgreSQL database with cards from pokemontcg.io
"""
import requests
import time
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models.card import Card, PriceHistory
from app.config import get_settings

settings = get_settings()


class PokemonTCGSync:
    """Service to sync Pokemon TCG cards from pokemontcg.io API to PostgreSQL"""
    
    BASE_URL = "https://api.pokemontcg.io/v2"
    
    def __init__(self):
        self.api_key = settings.pricecharting_api_key or settings.pokemon_tcg_api_key or ""
        self.headers = {}
        if self.api_key:
            self.headers["X-Api-Key"] = self.api_key
    
    def fetch_all_cards(self, page_size: int = 250) -> List[Dict]:
        """
        Fetch all cards from Pokemon TCG API using pagination.
        Returns a list of all cards.
        """
        all_cards = []
        page = 1
        
        print(f"[SYNC] Starting to fetch all cards from Pokemon TCG API...")
        
        while True:
            try:
                url = f"{self.BASE_URL}/cards"
                params = {
                    "page": page,
                    "pageSize": page_size
                }
                
                print(f"[SYNC] Fetching page {page}...")
                response = requests.get(url, params=params, headers=self.headers, timeout=60)
                response.raise_for_status()
                
                data = response.json()
                cards = data.get("data", [])
                
                if not cards:
                    break
                
                all_cards.extend(cards)
                print(f"[SYNC] Fetched {len(cards)} cards from page {page}. Total: {len(all_cards)}")
                
                # Check if there are more pages
                total_count = data.get("totalCount", 0)
                if len(all_cards) >= total_count:
                    break
                
                page += 1
                
                # Rate limiting - be nice to the API
                time.sleep(0.5)  # 500ms delay between requests
                
            except requests.exceptions.RequestException as e:
                print(f"[SYNC] Error fetching page {page}: {e}")
                break
        
        print(f"[SYNC] ✅ Finished fetching. Total cards: {len(all_cards)}")
        return all_cards
    
    def extract_price(self, card: Dict) -> float:
        """Extract market price from card data"""
        try:
            # Try TCGPlayer prices first (US market)
            if "tcgplayer" in card and "prices" in card["tcgplayer"]:
                prices = card["tcgplayer"]["prices"]
                
                # Try different price types in order of preference
                for price_type in ["holofoil", "normal", "reverseHolofoil", "1stEditionHolofoil", "unlimitedHolofoil"]:
                    if price_type in prices:
                        price_data = prices[price_type]
                        if "market" in price_data and price_data["market"]:
                            return round(float(price_data["market"]), 2)
                        elif "mid" in price_data and price_data["mid"]:
                            return round(float(price_data["mid"]), 2)
            
            # Try Cardmarket prices (European market)
            if "cardmarket" in card and "prices" in card["cardmarket"]:
                prices = card["cardmarket"]["prices"]
                if "averageSellPrice" in prices and prices["averageSellPrice"]:
                    return round(float(prices["averageSellPrice"]), 2)
                elif "trendPrice" in prices and prices["trendPrice"]:
                    return round(float(prices["trendPrice"]), 2)
            
            return 0.0
        except Exception as e:
            print(f"[SYNC] Error extracting price: {e}")
            return 0.0
    
    def save_card_to_db(self, card_data: Dict, db: Session) -> Optional[Card]:
        """Save or update a single card in the database"""
        try:
            external_id = card_data.get("id")
            if not external_id:
                return None
            
            # Check if card exists
            existing_card = db.query(Card).filter(Card.external_id == external_id).first()
            
            # Extract card information
            name = card_data.get("name", "")
            set_info = card_data.get("set", {})
            set_name = set_info.get("name", "Unknown")
            
            # Extract release year
            release_year = None
            release_date = set_info.get("releaseDate", "")
            if release_date:
                try:
                    release_year = int(release_date.split("/")[0])
                except:
                    pass
            
            # Extract price
            current_price = self.extract_price(card_data)
            
            # Get image URL
            images = card_data.get("images", {})
            image_url = images.get("small") or images.get("large")
            
            if existing_card:
                # Update existing card
                existing_card.name = name
                existing_card.set_name = set_name
                existing_card.rarity = card_data.get("rarity", existing_card.rarity)
                existing_card.artist = card_data.get("artist", existing_card.artist)
                existing_card.release_year = release_year or existing_card.release_year
                existing_card.card_number = card_data.get("number", existing_card.card_number)
                if image_url:
                    existing_card.image_url = image_url
                
                # Update price if changed
                if current_price > 0:
                    # Check if price history exists for today
                    today = datetime.now().date()
                    existing_price = db.query(PriceHistory).filter(
                        PriceHistory.card_id == existing_card.id,
                        PriceHistory.date >= datetime.combine(today, datetime.min.time())
                    ).first()
                    
                    if not existing_price:
                        # Add new price history entry
                        price_record = PriceHistory(
                            card_id=existing_card.id,
                            date=datetime.now(),
                            price_loose=current_price,
                            volume=0,
                            source="pokemontcg_api"
                        )
                        db.add(price_record)
                    elif existing_price.price_loose != current_price:
                        # Update today's price if different
                        existing_price.price_loose = current_price
                        existing_price.date = datetime.now()
                
                return existing_card
            else:
                # Create new card
                new_card = Card(
                    external_id=external_id,
                    name=name,
                    set_name=set_name,
                    rarity=card_data.get("rarity"),
                    artist=card_data.get("artist"),
                    release_year=release_year,
                    card_number=card_data.get("number"),
                    image_url=image_url,
                    tcgplayer_url=card_data.get("tcgplayer", {}).get("url"),
                    ebay_url=f"https://www.ebay.com/sch/i.html?_nkw=pokemon+{name.replace(' ', '+')}"
                )
                db.add(new_card)
                db.flush()  # Get the card ID
                
                # Add current price (real price from API, no simulation)
                # Historical data will be built over time by daily updates
                if current_price > 0:
                    price_record = PriceHistory(
                        card_id=new_card.id,
                        date=datetime.now(),
                        price_loose=current_price,
                        volume=0,
                        source="pokemontcg_api"
                    )
                    db.add(price_record)
                
                return new_card
                
        except IntegrityError:
            db.rollback()
            return None
        except Exception as e:
            print(f"[SYNC] Error saving card {card_data.get('id')}: {e}")
            db.rollback()
            return None
    
    def populate_database(self, batch_size: int = 100) -> Dict:
        """
        Populate the database with all cards from Pokemon TCG API.
        This is the initial population - can take a while!
        """
        print(f"[SYNC] Starting database population...")
        start_time = time.time()
        
        # Fetch all cards
        all_cards = self.fetch_all_cards()
        
        if not all_cards:
            print("[SYNC] No cards fetched. Aborting.")
            return {"success": False, "message": "No cards fetched"}
        
        db = SessionLocal()
        saved_count = 0
        updated_count = 0
        error_count = 0
        
        try:
            for i, card_data in enumerate(all_cards, 1):
                existing_card = db.query(Card).filter(
                    Card.external_id == card_data.get("id")
                ).first()
                
                result = self.save_card_to_db(card_data, db)
                
                if result:
                    if existing_card:
                        updated_count += 1
                    else:
                        saved_count += 1
                else:
                    error_count += 1
                
                # Commit in batches for better performance
                if i % batch_size == 0:
                    db.commit()
                    print(f"[SYNC] Processed {i}/{len(all_cards)} cards... "
                          f"(Saved: {saved_count}, Updated: {updated_count}, Errors: {error_count})")
            
            # Final commit
            db.commit()
            
            elapsed = time.time() - start_time
            print(f"[SYNC] ✅ Database population complete!")
            print(f"[SYNC] Total cards processed: {len(all_cards)}")
            print(f"[SYNC] New cards saved: {saved_count}")
            print(f"[SYNC] Existing cards updated: {updated_count}")
            print(f"[SYNC] Errors: {error_count}")
            print(f"[SYNC] Time elapsed: {elapsed:.2f} seconds")
            
            return {
                "success": True,
                "total_cards": len(all_cards),
                "saved": saved_count,
                "updated": updated_count,
                "errors": error_count,
                "time_elapsed": elapsed
            }
            
        except Exception as e:
            db.rollback()
            print(f"[SYNC] ❌ Error during population: {e}")
            return {"success": False, "message": str(e)}
        finally:
            db.close()
    
    def update_database(self, batch_size: int = 100) -> Dict:
        """
        Update the database with latest card information and prices.
        This is the daily update job - faster than full population.
        """
        print(f"[SYNC] Starting daily database update...")
        start_time = time.time()
        
        # Fetch all cards (API will return latest data)
        all_cards = self.fetch_all_cards()
        
        if not all_cards:
            print("[SYNC] No cards fetched. Aborting.")
            return {"success": False, "message": "No cards fetched"}
        
        db = SessionLocal()
        saved_count = 0
        updated_count = 0
        error_count = 0
        
        try:
            for i, card_data in enumerate(all_cards, 1):
                existing_card = db.query(Card).filter(
                    Card.external_id == card_data.get("id")
                ).first()
                
                result = self.save_card_to_db(card_data, db)
                
                if result:
                    if existing_card:
                        updated_count += 1
                    else:
                        saved_count += 1
                else:
                    error_count += 1
                
                # Commit in batches
                if i % batch_size == 0:
                    db.commit()
                    print(f"[SYNC] Processed {i}/{len(all_cards)} cards... "
                          f"(Saved: {saved_count}, Updated: {updated_count}, Errors: {error_count})")
            
            # Final commit
            db.commit()
            
            elapsed = time.time() - start_time
            print(f"[SYNC] ✅ Daily update complete!")
            print(f"[SYNC] Total cards processed: {len(all_cards)}")
            print(f"[SYNC] New cards saved: {saved_count}")
            print(f"[SYNC] Cards updated: {updated_count}")
            print(f"[SYNC] Errors: {error_count}")
            print(f"[SYNC] Time elapsed: {elapsed:.2f} seconds")
            
            return {
                "success": True,
                "total_cards": len(all_cards),
                "saved": saved_count,
                "updated": updated_count,
                "errors": error_count,
                "time_elapsed": elapsed
            }
            
        except Exception as e:
            db.rollback()
            print(f"[SYNC] ❌ Error during update: {e}")
            return {"success": False, "message": str(e)}
        finally:
            db.close()


# Global instance
pokemon_tcg_sync = PokemonTCGSync()

