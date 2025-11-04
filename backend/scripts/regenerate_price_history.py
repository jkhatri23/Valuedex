#!/usr/bin/env python3
"""
Script to regenerate price history for all cards with realistic fluctuations.
This will delete existing estimated price history and regenerate it with the new algorithm.

Usage:
    python scripts/regenerate_price_history.py
"""

import sys
import os
import random
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models.card import Card, PriceHistory

def regenerate_price_history():
    """Regenerate price history for all cards with realistic fluctuations"""
    db = SessionLocal()
    
    try:
        # Get all cards
        all_cards = db.query(Card).all()
        print(f"[REGEN] Found {len(all_cards)} cards to process")
        
        updated_count = 0
        
        for card in all_cards:
            # Get current price (most recent price history entry)
            latest_price = db.query(PriceHistory).filter(
                PriceHistory.card_id == card.id
            ).order_by(PriceHistory.date.desc()).first()
            
            if not latest_price or not latest_price.price_loose:
                continue
            
            current_price = latest_price.price_loose
            current_date = latest_price.date or datetime.now()
            
            # Delete existing estimated price history
            deleted = db.query(PriceHistory).filter(
                PriceHistory.card_id == card.id,
                PriceHistory.source.in_(["pokemontcg_api_estimated", "external_api_estimated", "backfill_estimated"])
            ).delete()
            
            # Generate new 12 months of historical data with realistic fluctuations
            base_price = current_price * random.uniform(0.7, 0.9)  # Start 10-30% lower
            
            # Generate prices with realistic market behavior
            prices = []
            price = base_price
            
            for i in range(12):
                months_ago = 12 - i
                hist_date = current_date - timedelta(days=months_ago * 30)
                
                # Calculate overall trend (should end near current_price)
                trend_factor = i / 12.0
                target_price = base_price + (current_price - base_price) * trend_factor
                
                # Add realistic volatility:
                # - Random fluctuations (±8%)
                # - Occasional larger moves (±15% for market events)
                volatility = random.uniform(-0.08, 0.08)
                
                # Occasionally add larger market movements (10% chance)
                if random.random() < 0.1:
                    volatility += random.uniform(-0.15, 0.15)
                
                # Apply mean reversion - prices tend to move toward target
                mean_reversion = (target_price - price) * 0.2
                
                # Calculate new price
                price = price * (1 + volatility) + mean_reversion
                
                # Ensure price stays reasonable (not too far from target)
                price = price * 0.7 + target_price * 0.3
                
                # Final price
                price = max(0.01, round(price, 2))
                prices.append((hist_date, price))
            
            # Normalize last price to match current_price exactly
            if prices:
                last_date, _ = prices[-1]
                prices[-1] = (last_date, current_price)
            
            # Save all price points
            for hist_date, hist_price in prices:
                historical_price = PriceHistory(
                    card_id=card.id,
                    date=hist_date,
                    price_loose=hist_price,
                    volume=random.randint(10, 200),
                    source="regenerated_estimated"
                )
                db.add(historical_price)
            
            updated_count += 1
            
            # Commit every 100 cards
            if updated_count % 100 == 0:
                db.commit()
                print(f"[REGEN] Processed {updated_count}/{len(all_cards)} cards...")
        
        # Final commit
        db.commit()
        
        print(f"[REGEN] ✅ Regeneration complete!")
        print(f"[REGEN] Updated {updated_count} cards with realistic price fluctuations")
        
        return {"success": True, "updated": updated_count}
        
    except Exception as e:
        db.rollback()
        print(f"[REGEN] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": str(e)}
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Price History Regeneration Script")
    print("=" * 60)
    print()
    print("This will regenerate price history for ALL cards with realistic")
    print("market fluctuations instead of linear progressions.")
    print()
    print("⚠️  This will delete existing estimated price history and create new data.")
    print()
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Aborted.")
        sys.exit(0)
    
    print()
    result = regenerate_price_history()
    
    if result.get("success"):
        print()
        print("=" * 60)
        print("✅ Regeneration successful!")
        print("=" * 60)
        print(f"Cards updated: {result.get('updated', 0)}")
        print()
        print("Price charts should now show realistic fluctuations instead of linear lines!")
    else:
        print()
        print("=" * 60)
        print("❌ Regeneration failed!")
        print("=" * 60)
        print(f"Error: {result.get('message', 'Unknown error')}")
        sys.exit(1)

