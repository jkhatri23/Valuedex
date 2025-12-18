#!/usr/bin/env python3
"""
Seed mock PriceCharting-like history for Blaine's Charizard (1st Edition) so
frontend charts can mirror the reference trend while prediction work proceeds.

Usage (from repo root):
    python backend/scripts/seed_mock_blaine_charizard.py

Notes:
- Prices follow the real Pokemon card market cycle from PriceCharting.com patterns:
  * Jan 2021 - Sep 2021: Pandemic boom (rapid growth)
  * Sep 2021 - Mar 2022: Peak period
  * Mar 2022 - Sep 2023: Market crash (significant drop)
  * Sep 2023 - Dec 2025: Recovery and growth
- End prices match actual Nov 2025 sales: PSA 10 at $13,700, PSA 9 at $1,849,
  PSA 8 at $1,025, PSA 7 at $783, PSA 6 at ~$650, and ungraded NM at ~$500.
- Existing price history and price_points for this card are removed first.
"""

import os
import sys
import calendar
from datetime import datetime
from typing import List, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal, Base, engine
from app.price_database import PriceSessionLocal, PriceBase, price_engine
from app.models.card import Card, PriceHistory
from app.models.price_point import PricePoint
from app.services.grades import normalize_grade, grade_rank
from app.services.pricepoints_migrations import ensure_pricepoints_grade_columns


EXTERNAL_ID = "gym2-2"
CARD_NAME = "Blaine's Charizard"
SET_NAME = "Gym Challenge"
RELEASE_YEAR = 2000


def month_range(start: datetime, end: datetime) -> List[datetime]:
    months = []
    current = datetime(start.year, start.month, 1)
    while current <= end:
        months.append(current)
        # advance one month
        month = current.month + 1
        year = current.year
        if month == 13:
            month = 1
            year += 1
        last_day = calendar.monthrange(year, month)[1]
        current = datetime(year, month, last_day)
    return months


def market_cycle_prices(
    dates: List[datetime],
    start_price: float,
    peak_price: float,
    bottom_price: float,
    end_price: float,
) -> List[float]:
    """
    Four-segment price curve matching real Pokemon card market cycles:
    1. Jan 2021 - Sep 2021: Pandemic boom (rapid growth)
    2. Sep 2021 - Mar 2022: Peak period (slight decline from peak)
    3. Mar 2022 - Sep 2023: Market crash (drop to bottom)
    4. Sep 2023 - Dec 2025: Recovery and growth
    """
    n = len(dates)
    prices: List[float] = []
    
    # Define segment boundaries (as indices)
    # ~9 months into 60 months = index 9 (Sep 2021 - peak)
    # ~15 months = index 15 (Mar 2022 - start of crash)
    # ~33 months = index 33 (Sep 2023 - bottom/recovery start)
    
    peak_idx = int(n * 0.15)  # Sep 2021
    crash_start_idx = int(n * 0.25)  # Mar 2022
    bottom_idx = int(n * 0.55)  # Sep 2023
    
    for i in range(n):
        if i <= peak_idx:
            # Segment 1: Boom to peak
            pct = i / max(peak_idx, 1)
            price = start_price + (peak_price - start_price) * pct
        elif i <= crash_start_idx:
            # Segment 2: Peak period (slight volatility)
            pct = (i - peak_idx) / max(crash_start_idx - peak_idx, 1)
            price = peak_price - (peak_price - peak_price * 0.95) * pct
        elif i <= bottom_idx:
            # Segment 3: Crash to bottom
            peak_value = peak_price * 0.95
            pct = (i - crash_start_idx) / max(bottom_idx - crash_start_idx, 1)
            price = peak_value - (peak_value - bottom_price) * pct
        else:
            # Segment 4: Recovery and growth
            pct = (i - bottom_idx) / max(n - bottom_idx - 1, 1)
            price = bottom_price + (end_price - bottom_price) * pct
        
        prices.append(round(price, 2))
    
    return prices


def build_price_curve(
    start_price: float,
    peak_price: float,
    bottom_price: float,
    end_price: float,
    dates: List[datetime],
) -> List[Tuple[datetime, float]]:
    prices = market_cycle_prices(dates, start_price, peak_price, bottom_price, end_price)
    return list(zip(dates, prices))


def ensure_card(db) -> Card:
    card = db.query(Card).filter(Card.external_id == EXTERNAL_ID).first()
    if card:
        return card

    card = Card(
        external_id=EXTERNAL_ID,
        name=CARD_NAME,
        set_name=SET_NAME,
        rarity="Holo Rare",
        artist=None,
        release_year=RELEASE_YEAR,
        card_number="2/132",
        image_url=None,
        tcgplayer_url=None,
        ebay_url=None,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


def clear_existing(db, price_db):
    # Find the card first, then delete its price history
    card = db.query(Card).filter(Card.external_id == EXTERNAL_ID).first()
    if card:
        db.query(PriceHistory).filter(PriceHistory.card_id == card.id).delete(synchronize_session=False)
    
    # Delete price points for this external_id
    price_db.query(PricePoint).filter(PricePoint.card_external_id == EXTERNAL_ID).delete(synchronize_session=False)
    
    db.commit()
    price_db.commit()


def seed():
    # Create all tables first
    print("[MOCK] Creating database tables...")
    Base.metadata.create_all(bind=engine)
    PriceBase.metadata.create_all(bind=price_engine)
    
    db = SessionLocal()
    price_db = PriceSessionLocal()

    ensure_pricepoints_grade_columns()

    try:
        card = ensure_card(db)
        clear_existing(db, price_db)

        start = datetime(2021, 1, 1)
        end = datetime(2025, 12, 31)
        dates = month_range(start, end)

        curves = {
            # Format: (start Jan 2021, peak Sep 2021, bottom Sep 2023, end Dec 2025) in USD
            # Based on actual PriceCharting market patterns showing boom-crash-recovery cycle
            
            "ungraded": (300.0, 650.0, 380.0, 500.0),      # Ungraded: boom, crash, recovery to ~$500
            "PSA 6": (350.0, 750.0, 450.0, 650.0),         # PSA 6: similar pattern, ends at ~$650
            "PSA 7": (450.0, 950.0, 520.0, 783.0),         # PSA 7: sold for $783 in Nov 2025
            "PSA 8": (600.0, 1300.0, 700.0, 1025.0),       # PSA 8: sold for $1,025 in Oct 2025
            "PSA 9": (1000.0, 2400.0, 1200.0, 1849.0),     # PSA 9: sold for $1,849 in Nov 2025
            "PSA 10": (3500.0, 11000.0, 5500.0, 13700.0),  # PSA 10: boom to $11k, crash, recover to $13,700
        }

        # Seed loose/ungraded into main price_history and price_points (grade None).
        loose_curve = build_price_curve(*curves["ungraded"], dates)
        for dt, price in loose_curve:
            db.add(
                PriceHistory(
                    card_id=card.id,
                    date=dt,
                    price_loose=price,
                    volume=None,
                    source="mock_pricecharting",
                )
            )
            price_db.add(
                PricePoint(
                    card_external_id=EXTERNAL_ID,
                    price_type="loose",
                    price=price,
                    volume=None,
                    source="mock_pricecharting",
                    grade=None,
                    grade_rank=None,
                    collected_at=dt,
                )
            )

        # Seed graded curves.
        for grade_label, params in curves.items():
            if grade_label == "ungraded":
                continue
            curve = build_price_curve(*params, dates)
            normalized = normalize_grade(grade_label)
            rank = grade_rank(normalized)
            for dt, price in curve:
                price_db.add(
                    PricePoint(
                        card_external_id=EXTERNAL_ID,
                        price_type="graded",
                        price=price,
                        volume=None,
                        source="mock_pricecharting",
                        grade=normalized,
                        grade_rank=rank,
                        collected_at=dt,
                    )
                )

        db.commit()
        price_db.commit()
        print("[MOCK] Seeded market cycle history for Blaine's Charizard (boom-crash-recovery pattern).")
        print(f"[MOCK] Points inserted: loose={len(loose_curve)}, grades={len(curves)-1} sets.")
    except Exception as exc:
        db.rollback()
        price_db.rollback()
        print(f"[MOCK] Failed seeding mock data: {exc}")
        raise
    finally:
        db.close()
        price_db.close()


if __name__ == "__main__":
    seed()
