from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.price_database import PriceBase


class PricePoint(PriceBase):
    __tablename__ = "price_points"

    id = Column(Integer, primary_key=True, index=True)
    card_external_id = Column(String, index=True)

    # e.g. 'loose', 'complete', 'new'
    price_type = Column(String, default="loose")

    # Condition / grade label, e.g. 'Near Mint', 'PSA 6', 'PSA 7', ...
    # Optional so existing rows remain valid.
    grade = Column(String, nullable=True)

    # Numeric rank for sorting by grade quality (lower is better condition).
    # Based on canonical order: Near Mint, PSA 6, PSA 7, PSA 8, PSA 9, PSA 10
    grade_rank = Column(Integer, nullable=True)

    price = Column(Float)
    volume = Column(Integer, nullable=True)
    source = Column(String, default="pokemontcg_api")
    collected_at = Column(DateTime, default=datetime.utcnow, index=True)

