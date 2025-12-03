from sqlalchemy import inspect, text

from app.database import engine


def ensure_card_features_sentiment_column() -> None:
    """
    Make sure the card_features table has a market_sentiment column.
    Safe to call multiple times; only alters when column is missing.
    """
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "card_features" not in tables:
        return

    columns = {col["name"] for col in inspector.get_columns("card_features")}
    if "market_sentiment" in columns:
        return

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE card_features ADD COLUMN market_sentiment FLOAT"))


