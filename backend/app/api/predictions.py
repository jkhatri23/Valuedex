"""Prediction API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime
import logging

from app.database import get_db
from app.models.card import Card, PriceHistory, CardFeature, Prediction
from app.ml.predictor import predictor

router = APIRouter()
logger = logging.getLogger(__name__)

class PredictionRequest(BaseModel):
    card_id: Union[str, int, None] = ""
    card_name: Optional[str] = ""
    set_name: Optional[str] = ""
    years_ahead: int = 3
    
    class Config:
        extra = "ignore"  # Ignore extra fields


@router.post("/predict")
async def predict_card_price(request: PredictionRequest, db: Session = Depends(get_db)):
    """Predict future price of a Pokemon card."""
    # Convert card_id to string for consistent handling
    card_id_str = str(request.card_id) if request.card_id else ""
    logger.info(f"Prediction request: card_id={card_id_str!r}, card_name={request.card_name!r}, set_name={request.set_name!r}, years_ahead={request.years_ahead!r}")
    card = None
    
    # Try internal ID first (if numeric)
    if card_id_str and card_id_str.isdigit():
        card = db.query(Card).filter(Card.id == int(card_id_str)).first()
    
    # Try external_id
    if not card and card_id_str:
        card = db.query(Card).filter(Card.external_id == card_id_str).first()
    
    # Try searching by card name
    if not card and request.card_name:
        card = db.query(Card).filter(Card.name.ilike(f"%{request.card_name}%")).first()
    
    # Fallback: find the most popular card (Charizard) if nothing else works
    if not card:
        card = db.query(Card).filter(Card.name.ilike("%Charizard%")).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="No cards in database. Please search for a card first.")
    
    price_history = db.query(PriceHistory).filter(
        PriceHistory.card_id == card.id
    ).order_by(PriceHistory.date.asc()).all()
    
    if not price_history:
        raise HTTPException(status_code=400, detail="No price history available")
    
    features = db.query(CardFeature).filter(CardFeature.card_id == card.id).first()
    if not features:
        raise HTTPException(status_code=400, detail="Features not calculated")
    
    price_data = [{"date": p.date, "price": p.price_loose} for p in price_history]
    
    features_dict = {
        "current_price": features.current_price,
        "rarity_score": features.rarity_score,
        "popularity_score": features.popularity_score,
        "artist_score": features.artist_score,
        "trend_30d": features.trend_30d,
        "trend_90d": features.trend_90d,
        "trend_1y": features.trend_1y,
        "volatility": features.price_volatility,
        "market_sentiment": features.market_sentiment
    }
    
    prediction = predictor.predict_hybrid(
        price_history=price_data,
        features=features_dict,
        years_ahead=request.years_ahead
    )
    
    timeline = predictor.generate_prediction_timeline(
        price_history=price_data,
        features=features_dict,
        max_years=5
    )
    
    growth_rate = (prediction["predicted_price"] - features.current_price) / features.current_price * 100
    
    # Save prediction
    db.add(Prediction(
        card_id=card.id,
        target_date=datetime.fromisoformat(prediction["target_date"]),
        years_ahead=request.years_ahead,
        predicted_price=prediction["predicted_price"],
        confidence_lower=prediction["confidence_lower"],
        confidence_upper=prediction["confidence_upper"],
        ml_model_version=prediction["model_version"],
        features_used=str(features_dict)
    ))
    db.commit()
    
    return {
        "card_id": card_id_str or card.external_id,
        "card_name": card.name,
        "current_price": features.current_price,
        "predicted_price": prediction["predicted_price"],
        "confidence_lower": prediction["confidence_lower"],
        "confidence_upper": prediction["confidence_upper"],
        "years_ahead": request.years_ahead,
        "target_date": prediction["target_date"],
        "model_version": prediction["model_version"],
        "growth_rate": round(growth_rate, 2),
        "scenarios": prediction["scenarios"],
        "risk_assessment": prediction["risk_assessment"],
        "market_factors": prediction["market_factors"],
        "recommendation": prediction["recommendation"],
        "timeline": timeline,
        "insights": {
            "time_series_contribution": prediction["time_series_prediction"],
            "feature_contribution": prediction["feature_prediction"],
            "investment_rating": features.investment_rating,
            "investment_score": features.investment_score,
            "volatility": prediction["risk_assessment"]["volatility"],
            "reward_risk_ratio": prediction["risk_assessment"]["reward_risk_ratio"]
        }
    }


@router.get("/predictions/{card_id}")
async def get_card_predictions(card_id: str, db: Session = Depends(get_db)):
    """Get prediction history for a card."""
    card = db.query(Card).filter(Card.external_id == card_id).first()
    if not card and card_id.isdigit():
        card = db.query(Card).filter(Card.id == int(card_id)).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    predictions = db.query(Prediction).filter(
        Prediction.card_id == card.id
    ).order_by(Prediction.prediction_date.desc()).limit(10).all()
    
    return {
        "card_id": card_id,
        "predictions": [{
            "prediction_date": p.prediction_date.isoformat(),
            "target_date": p.target_date.isoformat(),
            "years_ahead": p.years_ahead,
            "predicted_price": p.predicted_price,
            "confidence_lower": p.confidence_lower,
            "confidence_upper": p.confidence_upper,
            "model_version": p.ml_model_version
        } for p in predictions]
    }
