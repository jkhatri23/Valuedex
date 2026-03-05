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

