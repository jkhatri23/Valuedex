#!/usr/bin/env python3
"""
Clean the price_points table by removing graded eBay entries that deviate
more than ±60% from the rolling median of the last N accepted data points.

We preserve the earliest baseline year (2021) so the UI retains historical
context, but still keep coverage through 2025.
"""

import os
import sys
from datetime import datetime
from statistics import median
from typing import List

# Add backend root to the import path when the script is run directly.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.price_database import PriceSessionLocal
from app.models.price_point import PricePoint

ROLLING_MEDIAN_WINDOW = 5
OUTLIER_TOLERANCE = 0.60
BASELINE_YEAR = 2021
START_YEAR = 2021
END_YEAR = 2025


def _within_year_range(collected_at: datetime) -> bool:
    return START_YEAR <= collected_at.year <= END_YEAR


def clean_price_points() -> None:
    session = PriceSessionLocal()
    removed = 0
    try:
        card_ids = [row[0] for row in session.query(PricePoint.card_external_id).distinct().all()]

        for card_id in card_ids:
            grades = (
                session.query(PricePoint.grade)
                .filter(PricePoint.card_external_id == card_id)
                .distinct()
                .all()
            )
            for (grade,) in grades:
                if not grade:
                    continue

                points: List[PricePoint] = (
                    session.query(PricePoint)
                    .filter(
                        PricePoint.card_external_id == card_id,
                        PricePoint.grade == grade,
                        PricePoint.source == "ebay",
                        PricePoint.collected_at >= datetime(START_YEAR, 1, 1),
                        PricePoint.collected_at <= datetime(END_YEAR, 12, 31, 23, 59, 59),
                    )
                    .order_by(PricePoint.collected_at.asc())
                    .all()
                )

                accepted_window: List[float] = []
                for point in points:
                    if not _within_year_range(point.collected_at):
                        continue

                    if point.collected_at.year == BASELINE_YEAR:
                        accepted_window.append(point.price or 0)
                        continue

                    if len(accepted_window) >= ROLLING_MEDIAN_WINDOW:
                        window_prices = [p for p in accepted_window[-ROLLING_MEDIAN_WINDOW:] if p > 0]
                        if len(window_prices) == ROLLING_MEDIAN_WINDOW:
                            baseline = median(window_prices)
                            lower = baseline * (1 - OUTLIER_TOLERANCE)
                            upper = baseline * (1 + OUTLIER_TOLERANCE)
                            if point.price is None or point.price < lower or point.price > upper:
                                session.delete(point)
                                removed += 1
                                continue

                    accepted_window.append(point.price or 0)

        session.commit()
        print(f"[CLEANUP] Removed {removed} outlier price point(s).")
    except Exception as exc:
        session.rollback()
        print(f"[CLEANUP] Failed while cleaning price points: {exc}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    clean_price_points()

