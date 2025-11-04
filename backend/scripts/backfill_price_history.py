#!/usr/bin/env python3
"""
Script to backfill price history for cards that only have one price entry.
This generates 12 months of historical price data for existing cards.

Usage:
    python scripts/backfill_price_history.py
"""

import sys
import os
import random
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models.card import Card, PriceHistory
from sqlalchemy import func

def backfill_price_history():
    """Backfill price history for cards with only one entry"""
    db = SessionLocal()
    
    try:
        # Find cards with only one price history entry
        cards_with_one_price = db.query(Card).join(PriceHistory).group_by(Card.id).having(
            func.count(PriceHistory.id) == 1
        ).all()
        
        print(f"[BACKFILL] Found {len(cards_with_one_price)} cards with only one price entry")
        
        updated_count = 0
        
        for card in cards_with_one_price:
            # Get the existing price entry
            existing_price = db.query(PriceHistory).filter(
                PriceHistory.card_id == card.id
            ).order_by(PriceHistory.date.desc()).first()
            
            if not existing_price or not existing_price.price_loose:
                continue
            
            current_price = existing_price.price_loose
            current_date = existing_price.date or datetime.now()
            
            # Generate 12 months of historical data with realistic market fluctuations
            base_price = current_price * random.uniform(0.7, 0.9)  # Start 10-30% lower
            
            # Generate prices with realistic market behavior (volatility, trends, corrections)
            prices = []
            price = base_price
            
            for i in range(12):
                months_ago = 12 - i
                hist_date = current_date - timedelta(days=months_ago * 30)
                
                # Check if price history already exists for this date
                existing = db.query(PriceHistory).filter(
                    PriceHistory.card_id == card.id,
                    PriceHistory.date >= hist_date - timedelta(days=1),
                    PriceHistory.date <= hist_date + timedelta(days=1)
                ).first()
                
                if existing:
                    # Use existing price as starting point for next iteration
                    price = existing.price_loose or price
                    continue
                
                # Calculate overall trend (should end near current_price)
                trend_factor = i / 12.0
                target_price = base_price + (current_price - base_price) * trend_factor
                
                # Add realistic volatility:
                # - Random fluctuations (±8%)
                # - Occasional larger moves (±15% for market events)
                # - Natural price corrections
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
                    source="backfill_estimated"
                )
                db.add(historical_price)
            
            updated_count += 1
            
            # Commit every 100 cards
            if updated_count % 100 == 0:
                db.commit()
                print(f"[BACKFILL] Processed {updated_count}/{len(cards_with_one_price)} cards...")
        
        # Final commit
        db.commit()
        
        print(f"[BACKFILL] ✅ Backfill complete!")
        print(f"[BACKFILL] Updated {updated_count} cards with historical price data")
        
        return {"success": True, "updated": updated_count}
        
    except Exception as e:
        db.rollback()
        print(f"[BACKFILL] ❌ Error: {e}")
        return {"success": False, "message": str(e)}
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Price History Backfill Script")
    print("=" * 60)
    print()
    print("This will generate 12 months of historical price data")
    print("for cards that currently only have one price entry.")
    print()
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Aborted.")
        sys.exit(0)
    
    print()
    result = backfill_price_history()
    
    if result.get("success"):
        print()
        print("=" * 60)
        print("✅ Backfill successful!")
        print("=" * 60)
        print(f"Cards updated: {result.get('updated', 0)}")
    else:
        print()
        print("=" * 60)
        print("❌ Backfill failed!")
        print("=" * 60)
        print(f"Error: {result.get('message', 'Unknown error')}")
        sys.exit(1)

