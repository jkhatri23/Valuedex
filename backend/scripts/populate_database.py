#!/usr/bin/env python3
"""
Script to populate PostgreSQL database with Pokemon cards from pokemontcg.io
Run this once to initially populate the database.

Usage:
    python scripts/populate_database.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.pokemon_tcg_sync import pokemon_tcg_sync

if __name__ == "__main__":
    print("=" * 60)
    print("Pokemon TCG Database Population Script")
    print("=" * 60)
    print()
    print("This will fetch ALL cards from pokemontcg.io and save them to your database.")
    print("This may take a while depending on your internet connection...")
    print()
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Aborted.")
        sys.exit(0)
    
    print()
    result = pokemon_tcg_sync.populate_database()
    
    if result.get("success"):
        print()
        print("=" * 60)
        print("✅ Database population successful!")
        print("=" * 60)
        print(f"Total cards: {result.get('total_cards', 0)}")
        print(f"New cards saved: {result.get('saved', 0)}")
        print(f"Existing cards updated: {result.get('updated', 0)}")
        print(f"Errors: {result.get('errors', 0)}")
        print(f"Time: {result.get('time_elapsed', 0):.2f} seconds")
    else:
        print()
        print("=" * 60)
        print("❌ Database population failed!")
        print("=" * 60)
        print(f"Error: {result.get('message', 'Unknown error')}")
        sys.exit(1)

