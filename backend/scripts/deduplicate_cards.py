#!/usr/bin/env python3
"""
Find and remove duplicate cards in the database.

Two cards are considered duplicates when they share the same name, a
similar set name (after stripping common prefixes like "Pokemon"), AND
the same card number.  Cards with different card numbers are treated as
distinct variants (e.g. holo vs reverse holo).  Cards where both entries
are missing a card number are still grouped together.

For each group of duplicates the script keeps the "best" entry -- the one
with a pokemontcg.io image, the most price-history rows, and the most
complete metadata -- then migrates child rows and deletes the rest.

Usage:
    python scripts/deduplicate_cards.py            # dry-run (no changes)
    python scripts/deduplicate_cards.py --apply     # actually delete dupes
"""

import sys
import os
import re
import argparse
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, engine, Base
from app.models.card import Card, PriceHistory, Prediction, CardFeature

SET_STRIP_RE = re.compile(
    r"^(pokemon\s+)?(tcg\s+)?",
    re.IGNORECASE,
)


def normalize_set(name: str) -> str:
    """'Pokemon Gym Challenge' and 'Gym Challenge' -> 'gym challenge'"""
    return SET_STRIP_RE.sub("", (name or "").strip()).strip().lower()


def score_card(card: Card, price_count: int) -> tuple:
    """Higher is better.  Returns a sortable tuple."""
    has_pokemontcg_image = 1 if card.image_url and "pokemontcg.io" in card.image_url else 0
    has_image = 1 if card.image_url else 0
    has_rarity = 1 if card.rarity else 0
    has_artist = 1 if card.artist else 0
    has_year = 1 if card.release_year else 0
    has_number = 1 if card.card_number else 0
    metadata_count = has_rarity + has_artist + has_year + has_number

    return (has_pokemontcg_image, has_image, price_count, metadata_count)


def normalize_card_number(num: str | None) -> str:
    """Normalize card number for comparison.

    Handles format differences between sources:
      '2' and '2/132' both become '2'
      'SV049/SV122' becomes 'sv049'
      None becomes '' so two cards that both lack a number still group.
    """
    raw = (num or "").strip().lower()
    if not raw:
        return ""
    return raw.split("/")[0].strip()


def find_duplicates(db):
    """Return a dict of {(norm_name, norm_set, norm_number): [Card, ...]}
    for groups with more than one entry."""
    all_cards = db.query(Card).all()
    groups = defaultdict(list)
    for card in all_cards:
        key = (
            (card.name or "").strip().lower(),
            normalize_set(card.set_name),
            normalize_card_number(card.card_number),
        )
        groups[key].append(card)

    return {k: v for k, v in groups.items() if len(v) > 1}


def merge_and_delete(db, keeper: Card, dupes: list[Card], dry_run: bool):
    """Migrate child rows from dupes to keeper, then delete dupes."""
    for dupe in dupes:
        if dupe.id == keeper.id:
            continue

        # Fill in any missing metadata on the keeper
        if not keeper.image_url and dupe.image_url:
            keeper.image_url = dupe.image_url
        if not keeper.rarity and dupe.rarity:
            keeper.rarity = dupe.rarity
        if not keeper.artist and dupe.artist:
            keeper.artist = dupe.artist
        if not keeper.release_year and dupe.release_year:
            keeper.release_year = dupe.release_year
        if not keeper.card_number and dupe.card_number:
            keeper.card_number = dupe.card_number
        if not keeper.tcgplayer_url and dupe.tcgplayer_url:
            keeper.tcgplayer_url = dupe.tcgplayer_url

        if dry_run:
            continue

        # Migrate price history
        db.query(PriceHistory).filter(PriceHistory.card_id == dupe.id).update(
            {"card_id": keeper.id}, synchronize_session=False
        )
        # Migrate predictions
        db.query(Prediction).filter(Prediction.card_id == dupe.id).update(
            {"card_id": keeper.id}, synchronize_session=False
        )
        # Delete dupe's features (keeper already has its own)
        db.query(CardFeature).filter(CardFeature.card_id == dupe.id).delete(
            synchronize_session=False
        )
        db.delete(dupe)


def main():
    parser = argparse.ArgumentParser(description="Deduplicate Pokemon cards")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually apply changes (default is dry-run)",
    )
    args = parser.parse_args()
    dry_run = not args.apply

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("Scanning for duplicates...")
    dup_groups = find_duplicates(db)

    if not dup_groups:
        print("No duplicates found.")
        db.close()
        return

    total_dupes = sum(len(v) - 1 for v in dup_groups.values())
    print(f"Found {len(dup_groups)} groups with {total_dupes} duplicate cards total.\n")

    for (name, norm_set, norm_num), cards in sorted(dup_groups.items()):
        price_counts = {
            c.id: db.query(PriceHistory).filter(PriceHistory.card_id == c.id).count()
            for c in cards
        }
        cards.sort(key=lambda c: score_card(c, price_counts[c.id]), reverse=True)
        keeper = cards[0]
        dupes = cards[1:]

        num_label = f" #{norm_num}" if norm_num else ""
        print(f"  {keeper.name} / {norm_set}{num_label}")
        print(f"    keep:   id={keeper.id}  ext={keeper.external_id}  "
              f"set=\"{keeper.set_name}\"  num={keeper.card_number}  "
              f"prices={price_counts[keeper.id]}  "
              f"img={'yes' if keeper.image_url else 'no'}")
        for d in dupes:
            print(f"    delete: id={d.id}  ext={d.external_id}  "
                  f"set=\"{d.set_name}\"  num={d.card_number}  "
                  f"prices={price_counts[d.id]}  "
                  f"img={'yes' if d.image_url else 'no'}")

        merge_and_delete(db, keeper, dupes, dry_run)

    if dry_run:
        print(f"\nDry run complete. {total_dupes} cards would be removed.")
        print("Run with --apply to actually delete them.")
        db.rollback()
    else:
        db.commit()
        remaining = db.query(Card).count()
        print(f"\nDone. Removed {total_dupes} duplicates. {remaining} cards remain.")

    db.close()


if __name__ == "__main__":
    main()
