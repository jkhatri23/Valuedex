"""Prediction API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime
import asyncio
import logging

from app.database import get_db
from app.models.card import Card, PriceHistory, CardFeature, Prediction
from app.ml.predictor import predictor
from app.services.features import feature_service
from app.services.pricecharting_scraper import pricecharting_scraper

router = APIRouter()
logger = logging.getLogger(__name__)


async def _fetch_and_store_pricecharting_history(db, card) -> List[PriceHistory]:
    """Fetch real sales data from PriceCharting and store it in the PriceHistory table."""
    try:
        search_results = await asyncio.to_thread(
            pricecharting_scraper.search_card, card.name, card.set_name, card.card_number
        )
        if not search_results:
            logger.warning(f"No PriceCharting results for {card.name} / {card.set_name}")
            return []

        best_match = None
        for r in search_results:
            if not r.get("is_first_edition"):
                best_match = r
                break
        if not best_match:
            best_match = search_results[0]

        sales_by_grade = await asyncio.to_thread(
            pricecharting_scraper.get_sales_history, best_match["url"]
        )

        sales = sales_by_grade.get("Ungraded", [])
        if not sales:
            for grade_sales in sales_by_grade.values():
                if grade_sales:
                    sales = grade_sales
                    break

        if not sales:
            logger.warning(f"No sales history from PriceCharting for {card.name}")
            return []

        logger.info(f"Storing {len(sales)} PriceCharting data points for card {card.id} ({card.name})")
        for sale in sales:
            try:
                sale_date = datetime.strptime(sale["date"], "%Y-%m-%d")
            except (ValueError, KeyError):
                continue
            db.add(PriceHistory(
                card_id=card.id,
                date=sale_date,
                price_loose=round(sale["price"], 2),
                volume=1,
                source="pricecharting_ebay"
            ))
        db.commit()

        return db.query(PriceHistory).filter(
            PriceHistory.card_id == card.id
        ).order_by(PriceHistory.date.asc()).all()

    except Exception as e:
        logger.error(f"Failed to fetch PriceCharting history for {card.name}: {e}")
        return []

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
    
    # If insufficient price history, fetch real data from PriceCharting
    if len(price_history) < 2:
        logger.info(f"Insufficient price history for card {card.id} ({card.name}), fetching from PriceCharting...")
        price_history = await _fetch_and_store_pricecharting_history(db, card)
    
    if not price_history:
        raise HTTPException(status_code=400, detail="No price history available. PriceCharting has no sales data for this card.")
    
    features = db.query(CardFeature).filter(CardFeature.card_id == card.id).first()
    
    # Generate features if missing, using the most recent real price
    if not features:
        current_price = price_history[-1].price_loose or 0
        if current_price > 0:
            logger.info(f"Generating features for card {card.id} from PriceCharting price ${current_price}")
            features_dict = feature_service.create_card_features(card, current_price, [])
            features = CardFeature(card_id=card.id, **features_dict)
            db.add(features)
            db.commit()
        else:
            raise HTTPException(status_code=400, detail="No valid price data to generate features")
    
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
