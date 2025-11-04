#!/usr/bin/env python3
"""
Script to remove all simulated/estimated price history from the database.
This will keep only real prices from the API, and historical data will be
built over time by the daily update job.

Usage:
    python scripts/remove_simulated_price_history.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models.card import Card, PriceHistory

def remove_simulated_history():
    """Remove all simulated/estimated price history"""
    db = SessionLocal()
    
    try:
        # Find all estimated price history entries
        simulated_sources = [
            "pokemontcg_api_estimated",
            "external_api_estimated", 
            "backfill_estimated",
            "regenerated_estimated",
            "mock"
        ]
        
        # Count before deletion
        total_count = db.query(PriceHistory).filter(
            PriceHistory.source.in_(simulated_sources)
        ).count()
        
        print(f"[CLEANUP] Found {total_count} simulated price history entries")
        
        if total_count == 0:
            print("[CLEANUP] No simulated price history found. Nothing to remove.")
            return {"success": True, "deleted": 0}
        
        # Delete simulated entries
        deleted = db.query(PriceHistory).filter(
            PriceHistory.source.in_(simulated_sources)
        ).delete(synchronize_session=False)
        
        db.commit()
        
        print(f"[CLEANUP] ✅ Removed {deleted} simulated price history entries")
        print("[CLEANUP] Only real prices from the API remain.")
        print("[CLEANUP] Historical data will be built over time by daily updates.")
        
        # Count remaining real prices
        real_count = db.query(PriceHistory).filter(
            ~PriceHistory.source.in_(simulated_sources)
        ).count()
        
        print(f"[CLEANUP] Real price entries remaining: {real_count}")
        
        return {"success": True, "deleted": deleted, "remaining": real_count}
        
    except Exception as e:
        db.rollback()
        print(f"[CLEANUP] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": str(e)}
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Remove Simulated Price History Script")
    print("=" * 60)
    print()
    print("This will remove ALL simulated/estimated price history entries.")
    print("Only real prices from the Pokemon TCG API will remain.")
    print()
    print("⚠️  Historical data will be built over time by daily updates.")
    print()
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Aborted.")
        sys.exit(0)
    
    print()
    result = remove_simulated_history()
    
    if result.get("success"):
        print()
        print("=" * 60)
        print("✅ Cleanup successful!")
        print("=" * 60)
        print(f"Deleted: {result.get('deleted', 0)} simulated entries")
        print(f"Remaining: {result.get('remaining', 0)} real price entries")
        print()
        print("From now on, only real prices will be saved.")
        print("Historical data will accumulate over time as the daily update runs.")
    else:
        print()
        print("=" * 60)
        print("❌ Cleanup failed!")
        print("=" * 60)
        print(f"Error: {result.get('message', 'Unknown error')}")
        sys.exit(1)

