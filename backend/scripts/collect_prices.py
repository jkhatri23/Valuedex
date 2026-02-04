#!/usr/bin/env python3
"""
Daily Price Collection Script

Run this daily via cron to build historical price data:

    # Add to crontab (runs at 2 AM daily):
    0 2 * * * cd /path/to/pokedict/backend && ./venv/bin/python scripts/collect_prices.py

Or run manually:
    python scripts/collect_prices.py
    python scripts/collect_prices.py --card "Charizard" --set "Base Set"
"""

import sys
import os
import argparse
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.price_collector import price_collector, run_daily_collection
from app.services.ebay import ebay_price_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def collect_single_card(card_name: str, set_name: str = None):
    """Collect prices for a single card."""
    logger.info(f"Collecting prices for: {card_name} ({set_name or 'any set'})")
    
    # Generate a simple ID
    card_id = f"{card_name.lower().replace(' ', '_')}_{(set_name or 'unknown').lower().replace(' ', '_')}"
    
    saved = price_collector.collect_and_save(card_id, card_name, set_name)
    
    if saved > 0:
        logger.info(f"✓ Saved {saved} price points")
    else:
        logger.warning("No prices collected")
    
    return saved


def main():
    parser = argparse.ArgumentParser(description='Collect card prices from eBay')
    parser.add_argument('--card', '-c', help='Card name to collect')
    parser.add_argument('--set', '-s', help='Set name (optional)')
    parser.add_argument('--all', '-a', action='store_true', help='Collect all tracked cards')
    
    args = parser.parse_args()
    
    if not ebay_price_service.enabled:
        logger.error("eBay API not configured! Set EBAY_APP_ID and EBAY_CERT_ID in .env")
        sys.exit(1)
    
    if args.card:
        # Collect single card
        collect_single_card(args.card, args.set)
    elif args.all:
        # Collect all tracked cards
        run_daily_collection()
    else:
        # Default: show usage and collect a sample card
        print("Price Collector - Build historical price data")
        print("=" * 50)
        print()
        print("Usage:")
        print("  python collect_prices.py --card 'Charizard' --set 'Base Set'")
        print("  python collect_prices.py --all  # Collect all tracked cards")
        print()
        print("To build history, run this script DAILY via cron:")
        print("  0 2 * * * cd /path/to/backend && ./venv/bin/python scripts/collect_prices.py --all")
        print()
        
        # Demo: collect Charizard prices
        print("Demo: Collecting Charizard Base Set prices...")
        collect_single_card("Charizard", "Base Set")


if __name__ == "__main__":
    main()

