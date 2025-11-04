#!/usr/bin/env python3
"""
Script to update PostgreSQL database with latest Pokemon card information.
This is designed to be run daily (via cron or scheduler).

Usage:
    python scripts/update_database.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.pokemon_tcg_sync import pokemon_tcg_sync

if __name__ == "__main__":
    print("=" * 60)
    print("Pokemon TCG Database Update Script")
    print("=" * 60)
    print()
    
    result = pokemon_tcg_sync.update_database()
    
    if result.get("success"):
        print()
        print("=" * 60)
        print("✅ Database update successful!")
        print("=" * 60)
        print(f"Total cards: {result.get('total_cards', 0)}")
        print(f"New cards saved: {result.get('saved', 0)}")
        print(f"Cards updated: {result.get('updated', 0)}")
        print(f"Errors: {result.get('errors', 0)}")
        print(f"Time: {result.get('time_elapsed', 0):.2f} seconds")
    else:
        print()
        print("=" * 60)
        print("❌ Database update failed!")
        print("=" * 60)
        print(f"Error: {result.get('message', 'Unknown error')}")
        sys.exit(1)

