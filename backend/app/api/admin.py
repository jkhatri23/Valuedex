"""
Admin API endpoints for database management
"""
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Optional

from app.services.pokemon_tcg_sync import pokemon_tcg_sync
from app.services.card_index import card_index

router = APIRouter()


class UpdateResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict] = None


@router.post("/admin/populate-database", response_model=UpdateResponse)
async def populate_database(background_tasks: BackgroundTasks):
    """
    Trigger initial database population with all Pokemon cards.
    This is a long-running task and will run in the background.
    
    WARNING: This will fetch ALL cards from pokemontcg.io and may take a while!
    """
    def run_population():
        result = pokemon_tcg_sync.populate_database()
        return result
    
    # Run in background
    background_tasks.add_task(run_population)
    
    return UpdateResponse(
        success=True,
        message="Database population started in background. Check logs for progress.",
        data={"status": "started"}
    )


@router.post("/admin/update-database", response_model=UpdateResponse)
async def update_database(background_tasks: BackgroundTasks):
    """
    Trigger manual database update with latest card information and prices.
    This is the daily update job - runs in background.
    """
    def run_update():
        result = pokemon_tcg_sync.update_database()
        return result
    
    # Run in background
    background_tasks.add_task(run_update)
    
    return UpdateResponse(
        success=True,
        message="Database update started in background. Check logs for progress.",
        data={"status": "started"}
    )


@router.post("/admin/rebuild-index", response_model=UpdateResponse)
async def rebuild_index():
    """Rebuild the in-memory card search index from the database."""
    card_index.build()
    return UpdateResponse(
        success=True,
        message=f"Index rebuilt with {card_index.size} cards.",
        data={"indexed_cards": card_index.size}
    )


@router.post("/admin/refresh-prices", response_model=UpdateResponse)
async def refresh_prices(card_ids: list[str] = None):
    """Refresh prices from PriceCharting for specific cards (or featured cards if none specified)."""
    from app.database import SessionLocal
    from app.models.card import Card, PriceHistory, CardFeature
    from app.services.pricecharting_scraper import pricecharting_scraper
    from datetime import datetime

    featured = ["gym2-2", "base1-4", "base1-15", "neo1-4", "base1-2"]
    ids_to_update = card_ids or featured

    db = SessionLocal()
    updated = {}
    try:
        for ext_id in ids_to_update:
            card = db.query(Card).filter(Card.external_id == ext_id).first()
            if not card:
                updated[ext_id] = "not found"
                continue
            try:
                results = pricecharting_scraper.search_card(card.name, card.set_name, card.card_number)
                if not results:
                    updated[ext_id] = "no pricecharting results"
                    continue
                best = next((r for r in results if not r.get("is_first_edition")), results[0])
                prices = pricecharting_scraper.get_card_prices(best["url"])
                new_price = prices.get("ungraded", 0)
                if new_price <= 0:
                    updated[ext_id] = "no ungraded price"
                    continue
                features = db.query(CardFeature).filter(CardFeature.card_id == card.id).first()
                old_price = features.current_price if features else 0
                if features:
                    features.current_price = new_price
                db.add(PriceHistory(
                    card_id=card.id, date=datetime.now(),
                    price_loose=new_price, volume=1, source="pricecharting"
                ))
                updated[ext_id] = f"${old_price:.2f} -> ${new_price:.2f}"
            except Exception as e:
                updated[ext_id] = f"error: {e}"
        db.commit()
    finally:
        db.close()

    return UpdateResponse(
        success=True,
        message=f"Refreshed {len(updated)} cards",
        data=updated
    )


@router.get("/admin/sync-status")
async def get_sync_status():
    """
    Get information about the database sync status.
    Returns card count and last update info.
    """
    from app.database import SessionLocal
    from app.models.card import Card, PriceHistory
    from sqlalchemy import func
    
    db = SessionLocal()
    try:
        total_cards = db.query(func.count(Card.id)).scalar() or 0
        
        # Get latest price history date
        latest_price = db.query(PriceHistory).order_by(
            PriceHistory.date.desc()
        ).first()
        
        last_update = latest_price.date.isoformat() if latest_price else None
        
        return {
            "success": True,
            "total_cards": total_cards,
            "indexed_cards": card_index.size,
            "last_update": last_update,
            "scheduler_running": True
        }
    finally:
        db.close()

