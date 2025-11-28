#!/usr/bin/env python3
"""
Script to populate/refresh graded price points for all cards using eBay sold data.

For each card in the main database and for each canonical grade (Near Mint, PSA 6–10),
this script will:
  - Query eBay's FindingService for recent sold listings filtered by that grade
  - Compute an average sold price
  - Record a PricePoint row in pricepoints.db with grade + grade_rank

Usage:
    python scripts/update_ebay_grade_prices.py

Notes:
  - Make sure your .env has a valid EBAY_APP_ID (ebay_app_id) configured.
  - This can make a *lot* of API calls (cards × grades). Consider running it
    during off-hours or limiting the number of cards via the MAX_CARDS constant
    below if you're experimenting.
"""

import sys
import os
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.price_database import PriceSessionLocal
from app.models.card import Card
from app.services.ebay import ebay_price_service
from app.services.grades import GRADE_ORDER
from app.services.pokemon_tcg_sync import pokemon_tcg_sync


# Optional safety limit while testing. Set to None to process all cards.
MAX_CARDS: Optional[int] = None


def update_graded_prices() -> dict:
    db = SessionLocal()
    price_db = PriceSessionLocal()

    try:
        cards_query = db.query(Card).order_by(Card.id.asc())
        if MAX_CARDS is not None:
            cards = cards_query.limit(MAX_CARDS).all()
        else:
            cards = cards_query.all()

        total_cards = len(cards)
        print(f"[EBAY] Updating graded prices for {total_cards} cards...")

        updated_points = 0

        for i, card in enumerate(cards, 1):
            card_name = card.name or ""
            set_name = card.set_name

            if not card.external_id or not card_name:
                continue

            print(f"[EBAY] ({i}/{total_cards}) {card_name} [{set_name}]")

            for grade in GRADE_ORDER:
                price = ebay_price_service.get_average_price_for_grade(
                    card_name, set_name, grade
                )
                if price is None:
                    continue

                # Record as a graded price point sourced from eBay.
                pokemon_tcg_sync._record_price_point(  # type: ignore[attr-defined]
                    price_db,
                    card.external_id,
                    price,
                    price_type="graded",
                    volume=None,
                    source="ebay",
                    grade=grade,
                )
                updated_points += 1

            # Commit periodically to avoid huge transactions
            if i % 50 == 0:
                price_db.commit()
                print(f"[EBAY] Committed up to card {i}, total points: {updated_points}")

        price_db.commit()
        print(f"[EBAY] ✅ Finished. Total graded price points recorded: {updated_points}")

        return {
            "success": True,
            "cards_processed": total_cards,
            "price_points_created": updated_points,
        }
    except Exception as exc:
        price_db.rollback()
        print(f"[EBAY] ❌ Error while updating graded prices: {exc}")
        return {"success": False, "message": str(exc)}
    finally:
        db.close()
        price_db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("eBay Graded Price Update Script")
    print("=" * 60)
    print()
    print(
        "This will query eBay for each card and grade (Near Mint, PSA 6–10)\n"
        "and store graded price points in pricepoints.db.\n"
    )

    result = update_graded_prices()

    if result.get("success"):
        print()
        print("=" * 60)
        print("✅ eBay graded price update complete!")
        print("=" * 60)
        print(f"Cards processed: {result.get('cards_processed', 0)}")
        print(f"Graded price points created: {result.get('price_points_created', 0)}")
    else:
        print()
        print("=" * 60)
        print("❌ eBay graded price update failed!")
        print("=" * 60)
        print(f"Error: {result.get('message', 'Unknown error')}")
        sys.exit(1)


