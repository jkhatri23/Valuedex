"""
Price Collector Service - Builds historical price database over time.

This service periodically collects price data from eBay and stores it
in the database. Over time, this builds real historical data.

Run this as a scheduled job (cron) daily to collect price snapshots.
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.card import Card
from app.models.price_point import PricePoint
from app.price_database import PriceSessionLocal
from app.services.ebay import ebay_price_service

logger = logging.getLogger(__name__)


class PriceCollectorService:
    """Collects and stores price data to build historical records."""
    
    def __init__(self):
        self.ebay = ebay_price_service
    
    def collect_prices_for_card(
        self, 
        card_name: str, 
        set_name: Optional[str] = None,
        grades: List[str] = None
    ) -> Dict[str, float]:
        """
        Collect current prices for a card across all grades.
        Returns dict of grade -> price.
        """
        if grades is None:
            grades = ["Near Mint", "PSA 1", "PSA 2", "PSA 3", "PSA 4", 
                     "PSA 5", "PSA 6", "PSA 7", "PSA 8", "PSA 9", "PSA 10"]
        
        results = {}
        
        for grade in grades:
            try:
                grade_param = None if grade == "Near Mint" else grade
                price = self.ebay.get_average_price_for_grade(
                    card_name, set_name, grade_param or "pokemon"
                )
                if price and price > 0:
                    results[grade] = price
                    logger.info(f"Collected {card_name} {grade}: ${price:.2f}")
            except Exception as e:
                logger.warning(f"Failed to collect {card_name} {grade}: {e}")
        
        return results
    
    def save_price_snapshot(
        self,
        card_external_id: str,
        card_name: str,
        set_name: Optional[str],
        prices: Dict[str, float]
    ) -> int:
        """
        Save a price snapshot to the database.
        Returns number of price points saved.
        """
        saved = 0
        now = datetime.utcnow()
        
        try:
            db = PriceSessionLocal()
            
            for grade, price in prices.items():
                grade_db = None if grade == "Near Mint" else grade
                
                # Check if we already have a price for today
                existing = db.query(PricePoint).filter(
                    PricePoint.card_external_id == card_external_id,
                    PricePoint.grade == grade_db,
                    PricePoint.collected_at >= now.replace(hour=0, minute=0, second=0)
                ).first()
                
                if existing:
                    # Update existing
                    existing.price = price
                    existing.collected_at = now
                else:
                    # Create new
                    point = PricePoint(
                        card_external_id=card_external_id,
                        grade=grade_db,
                        price=price,
                        source="ebay_collected",
                        collected_at=now
                    )
                    db.add(point)
                    saved += 1
            
            db.commit()
            logger.info(f"Saved {saved} price points for {card_name}")
            
        except Exception as e:
            logger.error(f"Failed to save prices: {e}")
            db.rollback()
        finally:
            db.close()
        
        return saved
    
    def collect_and_save(
        self,
        card_external_id: str,
        card_name: str,
        set_name: Optional[str] = None
    ) -> int:
        """
        Collect prices from eBay and save to database.
        Call this daily to build history.
        """
        logger.info(f"Collecting prices for {card_name} ({set_name})")
        
        prices = self.collect_prices_for_card(card_name, set_name)
        
        if prices:
            return self.save_price_snapshot(
                card_external_id, card_name, set_name, prices
            )
        
        return 0
    
    def collect_all_tracked_cards(self) -> int:
        """
        Collect prices for all cards in the database.
        Run this as a daily scheduled job.
        """
        total_saved = 0
        
        try:
            db = SessionLocal()
            cards = db.query(Card).filter(Card.name.isnot(None)).all()
            
            logger.info(f"Collecting prices for {len(cards)} cards...")
            
            for card in cards:
                try:
                    saved = self.collect_and_save(
                        card.external_id,
                        card.name,
                        card.set_name
                    )
                    total_saved += saved
                except Exception as e:
                    logger.warning(f"Failed to collect {card.name}: {e}")
            
            logger.info(f"Total price points saved: {total_saved}")
            
        except Exception as e:
            logger.error(f"Collection failed: {e}")
        finally:
            db.close()
        
        return total_saved


# Singleton instance
price_collector = PriceCollectorService()


def run_daily_collection():
    """Entry point for scheduled collection job."""
    logger.info("Starting daily price collection...")
    total = price_collector.collect_all_tracked_cards()
    logger.info(f"Daily collection complete: {total} prices saved")
    return total

