#!/usr/bin/env python3
"""
Clear all price history and price points from the database.
Run this before seeding mock data for a clean slate.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, Base, engine
from app.price_database import PriceSessionLocal, PriceBase, price_engine
from app.models.card import PriceHistory
from app.models.price_point import PricePoint

def clear_all():
    db = SessionLocal()
    price_db = PriceSessionLocal()
    
    try:
        # Clear all price history
        count_history = db.query(PriceHistory).count()
        db.query(PriceHistory).delete()
        
        # Clear all price points
        count_points = price_db.query(PricePoint).count()
        price_db.query(PricePoint).delete()
        
        db.commit()
        price_db.commit()
        
        print(f"[CLEAR] Deleted {count_history} price history records")
        print(f"[CLEAR] Deleted {count_points} price points")
        print("[CLEAR] ✅ All price data cleared successfully")
    except Exception as e:
        db.rollback()
        price_db.rollback()
        print(f"[CLEAR] ❌ Error: {e}")
        raise
    finally:
        db.close()
        price_db.close()

if __name__ == "__main__":
    print("This will delete ALL price history and price points.")
    response = input("Continue? (yes/no): ")
    if response.lower() == "yes":
        clear_all()
    else:
        print("Aborted.")
