from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()

PRICE_DATABASE_URL = settings.price_database_url

if "postgresql" not in PRICE_DATABASE_URL:
    PRICE_DATABASE_URL = "sqlite:///./pricepoints.db"
    price_engine = create_engine(
        PRICE_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    price_engine = create_engine(PRICE_DATABASE_URL)

PriceSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=price_engine)

PriceBase = declarative_base()


def get_price_db():
    db = PriceSessionLocal()
    try:
        yield db
    finally:
        db.close()

