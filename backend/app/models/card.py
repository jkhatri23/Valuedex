from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Card(Base):
    __tablename__ = "cards"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)  # PriceCharting ID
    name = Column(String, index=True)
    set_name = Column(String)
    rarity = Column(String)
    artist = Column(String)
    release_year = Column(Integer)
    card_number = Column(String)
    card_type = Column(String)  # e.g., "Holo", "Reverse Holo", "1st Edition"
    image_url = Column(String, nullable=True)
    tcgplayer_url = Column(String, nullable=True)
    ebay_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    prices = relationship("PriceHistory", back_populates="card", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="card", cascade="all, delete-orphan")
    features = relationship("CardFeature", back_populates="card", uselist=False, cascade="all, delete-orphan")

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("cards.id"))
    date = Column(DateTime, index=True)
    price_loose = Column(Float, nullable=True)
    price_complete = Column(Float, nullable=True)
    price_new = Column(Float, nullable=True)
    volume = Column(Integer, nullable=True)  # Sales volume
    source = Column(String)  # "pricecharting", "manual", etc.
    
    # Relationship
    card = relationship("Card", back_populates="prices")

class Prediction(Base):
    __tablename__ = "predictions"
    
    model_config = {"protected_namespaces": ()}
    
    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("cards.id"))
    prediction_date = Column(DateTime, default=datetime.utcnow)
    target_date = Column(DateTime)  # Future date
    years_ahead = Column(Integer)
    predicted_price = Column(Float)
    confidence_lower = Column(Float)
    confidence_upper = Column(Float)
    ml_model_version = Column(String)  # Renamed from model_version to avoid conflict
    features_used = Column(Text)  # JSON string of features
    
    # Relationship
    card = relationship("Card", back_populates="predictions")

class CardFeature(Base):
    __tablename__ = "card_features"
    
    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("cards.id"), unique=True)
    
    # Popularity metrics
    popularity_score = Column(Float, default=0.0)  # 0-100 scale
    search_volume = Column(Integer, default=0)
    
    # Rarity score (calculated)
    rarity_score = Column(Float, default=0.0)  # 0-10 scale
    
    # Artist popularity
    artist_score = Column(Float, default=0.0)  # 0-10 scale
    
    # Market metrics
    current_price = Column(Float)
    price_volatility = Column(Float)  # Standard deviation
    trend_30d = Column(Float)  # % change last 30 days
    trend_90d = Column(Float)
    trend_1y = Column(Float)
    
    # Investment score (calculated)
    investment_score = Column(Float)  # 1-10 rating
    investment_rating = Column(String)  # "Strong Buy", "Buy", "Hold", "Sell"
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    card = relationship("Card", back_populates="features")

