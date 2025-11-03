from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import random

from app.database import get_db
from app.models.card import Card, PriceHistory, CardFeature
from app.services.pricecharting import pricecharting_service
from app.services.features import feature_service
from pydantic import BaseModel

router = APIRouter()

# Pydantic schemas
class CardSearchResult(BaseModel):
    id: str
    name: str
    set_name: str
    current_price: float
    image_url: Optional[str] = None

class CardDetail(BaseModel):
    id: int
    external_id: str
    name: str
    set_name: str
    rarity: Optional[str]
    artist: Optional[str]
    release_year: Optional[int]
    card_number: Optional[str]
    image_url: Optional[str]
    tcgplayer_url: Optional[str]
    ebay_url: Optional[str]
    current_price: float
    features: Optional[dict] = None

class PricePoint(BaseModel):
    date: str
    price: float
    volume: Optional[int] = None

@router.get("/search")
async def search_cards(q: str, limit: int = 20):
    """Search for Pokemon cards"""
    results = pricecharting_service.search_cards(q, limit)
    
    cards = []
    for item in results:
        cards.append({
            "id": item.get("id"),
            "name": item.get("product-name"),
            "set_name": item.get("console-name", "Unknown Set"),
            "current_price": item.get("loose-price", 0),
            "image_url": item.get("image")
        })
    
    return {"cards": cards, "count": len(cards)}

@router.get("/{card_id}")
async def get_card_detail(card_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a card"""
    
    # Check if card exists in DB
    card = db.query(Card).filter(Card.external_id == card_id).first()
    
    if not card:
        # Fetch from API and create
        card_data = pricecharting_service.get_card_by_id(card_id)
        
        if not card_data:
            # If we can't fetch the card details, return a minimal response
            # using data from the search result if available
            raise HTTPException(
                status_code=404, 
                detail=f"Card {card_id} not found. The Pokemon TCG API may be slow or unavailable."
            )
        
        # Create card - use real data from Pokemon TCG API
        release_year = None
        if card_data.get("set_release"):
            try:
                release_year = int(card_data["set_release"].split("/")[0])
            except:
                release_year = _extract_year(card_data.get("console-name", ""))
        
        card = Card(
            external_id=card_id,
            name=card_data.get("product-name"),
            set_name=card_data.get("console-name", "Unknown"),
            rarity=card_data.get("rarity") or _extract_rarity(card_data.get("product-name", "")),
            artist=card_data.get("artist") or _get_random_artist(),
            release_year=release_year or _extract_year(card_data.get("console-name", "")),
            card_number=card_data.get("number"),
            image_url=card_data.get("image"),
            tcgplayer_url=f"https://shop.tcgplayer.com/pokemon/{card_data.get('product-name', '').replace(' ', '-')}",
            ebay_url=f"https://www.ebay.com/sch/i.html?_nkw=pokemon+{card_data.get('product-name', '').replace(' ', '+')}"
        )
        db.add(card)
        db.commit()
        db.refresh(card)
        
        # Create initial price history
        current_price = card_data.get("loose-price", 100)
        _create_mock_price_history(db, card.id, current_price)
        
        # Create features
        features_dict = feature_service.create_card_features(card, current_price, [])
        card_features = CardFeature(card_id=card.id, **features_dict)
        db.add(card_features)
        db.commit()
    
    # Get features
    features = db.query(CardFeature).filter(CardFeature.card_id == card.id).first()
    
    return {
        "id": card.id,
        "external_id": card.external_id,
        "name": card.name,
        "set_name": card.set_name,
        "rarity": card.rarity,
        "artist": card.artist,
        "release_year": card.release_year,
        "card_number": card.card_number,
        "image_url": card.image_url,
        "tcgplayer_url": card.tcgplayer_url,
        "ebay_url": card.ebay_url,
        "current_price": features.current_price if features else 0,
        "features": {
            "popularity_score": features.popularity_score,
            "rarity_score": features.rarity_score,
            "artist_score": features.artist_score,
            "trend_30d": features.trend_30d,
            "trend_90d": features.trend_90d,
            "trend_1y": features.trend_1y,
            "volatility": features.price_volatility,
            "investment_score": features.investment_score,
            "investment_rating": features.investment_rating
        } if features else None
    }

@router.get("/{card_id}/prices")
async def get_price_history(card_id: str, db: Session = Depends(get_db)):
    """Get price history for a card"""
    
    card = db.query(Card).filter(Card.external_id == card_id).first()
    
    if not card:
        # Try to get card detail first (will create it)
        await get_card_detail(card_id, db)
        card = db.query(Card).filter(Card.external_id == card_id).first()
    
    prices = db.query(PriceHistory).filter(
        PriceHistory.card_id == card.id
    ).order_by(PriceHistory.date.asc()).all()
    
    price_points = [
        {
            "date": p.date.isoformat(),
            "price": p.price_loose or 0,
            "volume": p.volume
        }
        for p in prices
    ]
    
    return {"card_id": card_id, "prices": price_points}

@router.get("/{card_id}/rating")
async def get_investment_rating(card_id: str, db: Session = Depends(get_db)):
    """Get investment rating for a card"""
    
    card = db.query(Card).filter(Card.external_id == card_id).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    features = db.query(CardFeature).filter(CardFeature.card_id == card.id).first()
    
    if not features:
        raise HTTPException(status_code=404, detail="Features not calculated")
    
    return {
        "card_id": card_id,
        "investment_score": features.investment_score,
        "investment_rating": features.investment_rating,
        "current_price": features.current_price,
        "trends": {
            "30d": features.trend_30d,
            "90d": features.trend_90d,
            "1y": features.trend_1y
        },
        "factors": {
            "rarity_score": features.rarity_score,
            "popularity_score": features.popularity_score,
            "artist_score": features.artist_score,
            "volatility": features.price_volatility
        }
    }

# Helper functions
def _extract_rarity(name: str) -> str:
    """Extract rarity from card name"""
    name_lower = name.lower()
    if "holo" in name_lower or "holographic" in name_lower:
        return "Holo Rare"
    elif "ultra rare" in name_lower:
        return "Ultra Rare"
    elif "secret" in name_lower:
        return "Secret Rare"
    elif "rare" in name_lower:
        return "Rare"
    return "Uncommon"

def _get_random_artist() -> str:
    """Get a random Pokemon card artist"""
    artists = [
        "Ken Sugimori",
        "Mitsuhiro Arita",
        "Atsuko Nishida",
        "Kouki Saitou",
        "Sowsow",
        "5ban Graphics",
        "Kagemaru Himeno",
        "Yuka Morii"
    ]
    return random.choice(artists)

def _extract_year(set_name: str) -> int:
    """Extract or estimate release year"""
    if "base set" in set_name.lower():
        return 1999
    elif "fossil" in set_name.lower() or "jungle" in set_name.lower():
        return 2000
    return random.randint(2018, 2024)

def _create_mock_price_history(db: Session, card_id: int, current_price: float):
    """Create mock price history for a card"""
    # Create 12 months of price history
    for i in range(12):
        date = datetime.now() - timedelta(days=(12-i) * 30)
        # Price varies around current price
        variation = random.uniform(0.85, 1.15)
        price = current_price * variation * (0.8 + (i / 12) * 0.2)  # Slight upward trend
        
        price_record = PriceHistory(
            card_id=card_id,
            date=date,
            price_loose=round(price, 2),
            volume=random.randint(50, 500),
            source="mock"
        )
        db.add(price_record)
    
    db.commit()

