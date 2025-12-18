from sqlalchemy import inspect, text

from app.price_database import price_engine, PriceSessionLocal
from app.models.price_point import PricePoint
from app.services.grades import normalize_grade, grade_rank


def ensure_pricepoints_grade_columns() -> None:
    """
    Lightweight migration helper to make sure the price_points table
    has grade / grade_rank columns.

    Safe to call multiple times; it will only ALTER TABLE when needed.
    """
    inspector = inspect(price_engine)
    tables = inspector.get_table_names()

    if "price_points" not in tables:
        # Table doesn't exist yet – it will be created from models later.
        return

    existing_columns = {col["name"] for col in inspector.get_columns("price_points")}

    statements = []
    if "grade" not in existing_columns:
        statements.append("ALTER TABLE price_points ADD COLUMN grade VARCHAR")
    if "grade_rank" not in existing_columns:
        statements.append("ALTER TABLE price_points ADD COLUMN grade_rank INTEGER")
    if "shipping_cost" not in existing_columns:
        statements.append("ALTER TABLE price_points ADD COLUMN shipping_cost FLOAT")

    if not statements:
        return

    with price_engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))


def normalize_existing_pricepoints() -> int:
    """
    Normalize and rank existing price_points rows so they can be ordered
    by grade quality.

    Uses either the explicit grade column (if present) or falls back to
    interpreting price_type as a grade label.

    Returns the number of rows updated.
    """
    ensure_pricepoints_grade_columns()

    db = PriceSessionLocal()
    updated = 0
    try:
        for pp in db.query(PricePoint).all():
            # If we already have both grade and rank, skip
            if pp.grade and pp.grade_rank is not None:
                continue

            # Prefer an explicit grade, otherwise fall back to price_type
            raw = pp.grade or pp.price_type
            if not raw:
                continue

            normalized = normalize_grade(raw)
            rank = grade_rank(normalized) if normalized else None

            # If nothing changed, skip unnecessary write
            if pp.grade == normalized and pp.grade_rank == rank:
                continue

            pp.grade = normalized
            pp.grade_rank = rank
            updated += 1

        if updated:
            db.commit()
        return updated
    except Exception as exc:
        db.rollback()
        print(f"[MIGRATION] Error normalizing price point grades: {exc}")
        return updated
    finally:
        db.close()


