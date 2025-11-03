from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.card import Card, PriceHistory, CardFeature, Prediction
from app.ml.predictor import predictor

router = APIRouter()

class PredictionRequest(BaseModel):
    card_id: str
    years_ahead: int = 3

class PredictionResponse(BaseModel):
    card_id: str
    card_name: str
    current_price: float
    predicted_price: float
    confidence_lower: float
    confidence_upper: float
    years_ahead: int
    target_date: str
    model_version: str
    growth_rate: float
    timeline: List[dict]

@router.post("/predict")
async def predict_card_price(
    request: PredictionRequest,
    db: Session = Depends(get_db)
):
    """Predict future price of a Pokemon card"""
    
    # Get card from database
    card = db.query(Card).filter(Card.external_id == request.card_id).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found. Please fetch card details first.")
    
    # Get price history
    price_history = db.query(PriceHistory).filter(
        PriceHistory.card_id == card.id
    ).order_by(PriceHistory.date.asc()).all()
    
    if not price_history:
        raise HTTPException(status_code=400, detail="No price history available for this card")
    
    # Get features
    features = db.query(CardFeature).filter(CardFeature.card_id == card.id).first()
    
    if not features:
        raise HTTPException(status_code=400, detail="Card features not calculated")
    
    # Prepare data for prediction
    price_data = [
        {
            "date": p.date,
            "price": p.price_loose
        }
        for p in price_history
    ]
    
    features_dict = {
        "current_price": features.current_price,
        "rarity_score": features.rarity_score,
        "popularity_score": features.popularity_score,
        "artist_score": features.artist_score,
        "trend_30d": features.trend_30d,
        "trend_90d": features.trend_90d,
        "trend_1y": features.trend_1y,
        "volatility": features.price_volatility
    }
    
    # Generate predictions
    prediction = predictor.predict_hybrid(
        price_history=price_data,
        features=features_dict,
        years_ahead=request.years_ahead
    )
    
    # Generate full timeline
    timeline = predictor.generate_prediction_timeline(
        price_history=price_data,
        features=features_dict,
        max_years=5
    )
    
    # Calculate growth rate
    growth_rate = ((prediction["predicted_price"] - features.current_price) / 
                   features.current_price * 100)
    
    # Save prediction to database
    db_prediction = Prediction(
        card_id=card.id,
        target_date=datetime.fromisoformat(prediction["target_date"]),
        years_ahead=request.years_ahead,
        predicted_price=prediction["predicted_price"],
        confidence_lower=prediction["confidence_lower"],
        confidence_upper=prediction["confidence_upper"],
        ml_model_version=prediction["model_version"],
        features_used=str(features_dict)
    )
    db.add(db_prediction)
    db.commit()
    
    return {
        "card_id": request.card_id,
        "card_name": card.name,
        "current_price": features.current_price,
        "predicted_price": prediction["predicted_price"],
        "confidence_lower": prediction["confidence_lower"],
        "confidence_upper": prediction["confidence_upper"],
        "years_ahead": request.years_ahead,
        "target_date": prediction["target_date"],
        "model_version": prediction["model_version"],
        "growth_rate": round(growth_rate, 2),
        "timeline": timeline,
        "insights": {
            "time_series_contribution": prediction["time_series_prediction"],
            "feature_contribution": prediction["feature_prediction"],
            "investment_rating": features.investment_rating,
            "investment_score": features.investment_score
        }
    }

@router.get("/predictions/{card_id}")
async def get_card_predictions(
    card_id: str,
    db: Session = Depends(get_db)
):
    """Get all predictions for a card"""
    
    card = db.query(Card).filter(Card.external_id == card_id).first()
    
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    predictions = db.query(Prediction).filter(
        Prediction.card_id == card.id
    ).order_by(Prediction.prediction_date.desc()).limit(10).all()
    
    return {
        "card_id": card_id,
        "predictions": [
            {
                "prediction_date": p.prediction_date.isoformat(),
                "target_date": p.target_date.isoformat(),
                "years_ahead": p.years_ahead,
                "predicted_price": p.predicted_price,
                "confidence_lower": p.confidence_lower,
                "confidence_upper": p.confidence_upper,
                "model_version": p.ml_model_version
            }
            for p in predictions
        ]
    }

