#!/usr/bin/env python3
"""
Bulk populate database with Pokemon cards from the Pokemon TCG GitHub dataset.
Uses the offline JSON data (no API rate limits) and fills in prices where available.

Usage:
    python scripts/bulk_populate.py [--max-cards 5000]
"""

import sys
import os
import json
import time
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal, Base, engine
from app.price_database import PriceSessionLocal, price_engine
from app.models.card import Card, PriceHistory, CardFeature
from app.models.price_point import PricePoint
from app.services.features import feature_service
from app.services.grades import normalize_grade, grade_rank
from app.services.pricepoints_migrations import ensure_pricepoints_grade_columns

DATA_DIR = "/tmp/pokemon-tcg-data"
CARDS_DIR = os.path.join(DATA_DIR, "cards", "en")
SETS_FILE = os.path.join(DATA_DIR, "sets", "en.json")

PRIORITY_SETS = [
    "base1", "base2", "base3", "base4", "base5", "base6",
    "neo1", "neo2", "neo3", "neo4",
    "ecard1", "ecard2", "ecard3",
    "ex1", "ex2", "ex3", "ex4", "ex5", "ex6", "ex7", "ex8",
    "ex9", "ex10", "ex11", "ex12", "ex13", "ex14", "ex15", "ex16",
    "dp1", "dp2", "dp3", "dp4", "dp5", "dp6", "dp7",
    "pl1", "pl2", "pl3", "pl4",
    "hgss1", "hgss2", "hgss3", "hgss4",
    "bw1", "bw2", "bw3", "bw4", "bw5", "bw6", "bw7", "bw8", "bw9", "bw10", "bw11",
    "xy0", "xy1", "xy2", "xy3", "xy4", "xy5", "xy6", "xy7", "xy8", "xy9", "xy10", "xy11", "xy12",
    "sm1", "sm2", "sm3", "sm35", "sm4", "sm5", "sm6", "sm7", "sm75", "sm8", "sm9", "sm10", "sm11", "sm115", "sm12",
    "swsh1", "swsh2", "swsh3", "swsh35", "swsh4", "swsh45", "swsh5", "swsh6", "swsh7", "swsh8", "swsh9", "swsh10", "swsh11", "swsh12", "swsh12pt5",
    "sv1", "sv2", "sv3", "sv3pt5", "sv4", "sv4pt5", "sv5", "sv6", "sv7", "sv8",
]


def load_sets() -> dict:
    with open(SETS_FILE) as f:
        sets_list = json.load(f)
    return {s["id"]: s for s in sets_list}


def load_all_cards(sets_info: dict, max_cards: int) -> list:
    """Load cards from JSON files, prioritizing popular sets."""
    all_cards = []
    loaded_set_ids = set()

    for set_id in PRIORITY_SETS:
        if len(all_cards) >= max_cards:
            break
        filepath = os.path.join(CARDS_DIR, f"{set_id}.json")
        if not os.path.exists(filepath):
            continue
        with open(filepath) as f:
            cards = json.load(f)
        set_meta = sets_info.get(set_id, {})
        for card in cards:
            card["_set_meta"] = set_meta
        all_cards.extend(cards)
        loaded_set_ids.add(set_id)
        print(f"  Loaded {set_id} ({set_meta.get('name', '?')}): {len(cards)} cards")

    if len(all_cards) < max_cards:
        for filename in sorted(os.listdir(CARDS_DIR)):
            if len(all_cards) >= max_cards:
                break
            if not filename.endswith(".json"):
                continue
            set_id = filename.replace(".json", "")
            if set_id in loaded_set_ids:
                continue
            filepath = os.path.join(CARDS_DIR, filename)
            with open(filepath) as f:
                cards = json.load(f)
            set_meta = sets_info.get(set_id, {})
            for card in cards:
                card["_set_meta"] = set_meta
            all_cards.extend(cards)
            loaded_set_ids.add(set_id)
            print(f"  Loaded {set_id} ({set_meta.get('name', '?')}): {len(cards)} cards")

    if len(all_cards) > max_cards:
        all_cards = all_cards[:max_cards]

    return all_cards


def extract_release_year(set_meta: dict) -> int | None:
    release_date = set_meta.get("releaseDate", "")
    if release_date:
        try:
            return int(release_date.split("/")[0])
        except (ValueError, IndexError):
            pass
    return None


def save_card(card_data: dict, db, price_db) -> str:
    """Save a single card. Returns 'new', 'updated', or 'error'."""
    external_id = card_data.get("id")
    if not external_id:
        return "error"

    try:
        existing = db.query(Card).filter(Card.external_id == external_id).first()
        set_meta = card_data.get("_set_meta", {})
        name = card_data.get("name", "")
        set_name = set_meta.get("name", "Unknown")
        release_year = extract_release_year(set_meta)
        images = card_data.get("images", {})
        image_url = images.get("small") or images.get("large")
        rarity = card_data.get("rarity")
        artist = card_data.get("artist")
        card_number = card_data.get("number")

        tcgplayer = card_data.get("tcgplayer", {})
        tcgplayer_url = tcgplayer.get("url") if tcgplayer else None
        current_price = 0.0
        if tcgplayer and "prices" in tcgplayer:
            prices = tcgplayer["prices"]
            for pt in ["holofoil", "normal", "reverseHolofoil", "1stEditionHolofoil", "unlimitedHolofoil"]:
                if pt in prices:
                    pd = prices[pt]
                    current_price = pd.get("market") or pd.get("mid") or 0
                    if current_price:
                        current_price = round(float(current_price), 2)
                        break

        if existing:
            existing.name = name
            existing.set_name = set_name
            existing.rarity = rarity or existing.rarity
            existing.artist = artist or existing.artist
            existing.release_year = release_year or existing.release_year
            existing.card_number = card_number or existing.card_number
            if image_url:
                existing.image_url = image_url
            if tcgplayer_url:
                existing.tcgplayer_url = tcgplayer_url
            return "updated"
        else:
            ebay_search = f"https://www.ebay.com/sch/i.html?_nkw=pokemon+{name.replace(' ', '+')}"
            new_card = Card(
                external_id=external_id,
                name=name,
                set_name=set_name,
                rarity=rarity,
                artist=artist,
                release_year=release_year,
                card_number=card_number,
                image_url=image_url,
                tcgplayer_url=tcgplayer_url,
                ebay_url=ebay_search,
            )
            db.add(new_card)
            db.flush()

            if current_price > 0:
                price_record = PriceHistory(
                    card_id=new_card.id,
                    date=datetime.now(),
                    price_loose=current_price,
                    volume=0,
                    source="pokemontcg_github",
                )
                db.add(price_record)

            features_dict = feature_service.create_card_features(new_card, current_price, [])
            card_feature = CardFeature(card_id=new_card.id, **features_dict)
            db.add(card_feature)

            return "new"

    except IntegrityError:
        db.rollback()
        return "error"
    except Exception as e:
        print(f"  Error saving {external_id}: {e}")
        db.rollback()
        return "error"


def main():
    parser = argparse.ArgumentParser(description="Bulk populate Pokemon card database")
    parser.add_argument("--max-cards", type=int, default=5000)
    args = parser.parse_args()

    if not os.path.exists(CARDS_DIR):
        print(f"Data not found at {DATA_DIR}. Clone it first:")
        print(f"  git clone --depth 1 https://github.com/PokemonTCG/pokemon-tcg-data.git {DATA_DIR}")
        sys.exit(1)

    print("=" * 60)
    print(f"Bulk Populate: Loading up to {args.max_cards} cards")
    print("=" * 60)

    Base.metadata.create_all(bind=engine)

    ensure_pricepoints_grade_columns()

    print("\nLoading set metadata...")
    sets_info = load_sets()
    print(f"Found {len(sets_info)} sets\n")

    print("Loading card data from JSON files...")
    all_cards = load_all_cards(sets_info, args.max_cards)
    print(f"\nTotal cards to process: {len(all_cards)}\n")

    db = SessionLocal()
    price_db = PriceSessionLocal()
    new_count = 0
    updated_count = 0
    error_count = 0
    start_time = time.time()
    batch_size = 200

    try:
        for i, card_data in enumerate(all_cards, 1):
            result = save_card(card_data, db, price_db)
            if result == "new":
                new_count += 1
            elif result == "updated":
                updated_count += 1
            else:
                error_count += 1

            if i % batch_size == 0:
                db.commit()
                price_db.commit()
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                print(f"  [{i}/{len(all_cards)}] New: {new_count}, Updated: {updated_count}, "
                      f"Errors: {error_count} ({rate:.0f} cards/sec)")

        db.commit()
        price_db.commit()

    except Exception as e:
        db.rollback()
        price_db.rollback()
        print(f"\nFatal error: {e}")
        sys.exit(1)
    finally:
        db.close()
        price_db.close()

    elapsed = time.time() - start_time
    total_in_db = SessionLocal().query(Card).count()

    print()
    print("=" * 60)
    print("Done!")
    print("=" * 60)
    print(f"  New cards:     {new_count}")
    print(f"  Updated:       {updated_count}")
    print(f"  Errors:        {error_count}")
    print(f"  Time:          {elapsed:.1f}s")
    print(f"  Total in DB:   {total_in_db}")


if __name__ == "__main__":
    main()
