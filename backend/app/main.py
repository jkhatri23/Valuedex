from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.api import cards, predictions, admin
from app.database import engine, Base, SessionLocal
from app.price_database import price_engine, PriceBase
from app.models.card import Card, CardFeature, PriceHistory
from app.services.pokemon_tcg_sync import pokemon_tcg_sync
from app.services.features import feature_service
from app.services.card_index import card_index
import logging
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)
PriceBase.metadata.create_all(bind=price_engine)

# Setup scheduler
scheduler = BackgroundScheduler()

def daily_update_job():
    """Daily job to update card prices and add new cards"""
    logger.info("Starting scheduled daily database update...")
    result = pokemon_tcg_sync.update_database()
    if result.get("success"):
        logger.info(f"Daily update successful: {result.get('updated', 0)} cards updated")
    else:
        logger.error(f"Daily update failed: {result.get('message', 'Unknown error')}")

def fix_missing_features():
    """Add CardFeature records to cards that don't have them"""
    db = SessionLocal()
    try:
        # Find cards without features
        cards_without_features = db.query(Card).outerjoin(CardFeature).filter(
            CardFeature.id == None
        ).all()
        
        if not cards_without_features:
            logger.info("All cards have features. No fix needed.")
            return
        
        logger.info(f"Found {len(cards_without_features)} cards without features. Creating...")
        
        created = 0
        for card in cards_without_features:
            # Get the most recent price for this card
            latest_price = db.query(PriceHistory).filter(
                PriceHistory.card_id == card.id
            ).order_by(PriceHistory.date.desc()).first()
            
            current_price = latest_price.price_loose if latest_price else 0
            
            # Create features
            features_dict = feature_service.create_card_features(card, current_price, [])
            card_feature = CardFeature(card_id=card.id, **features_dict)
            db.add(card_feature)
            created += 1
            
            # Commit in batches
            if created % 100 == 0:
                db.commit()
                logger.info(f"Created features for {created}/{len(cards_without_features)} cards...")
        
        db.commit()
        logger.info(f"Created features for {created} cards")
        
    except Exception as e:
        logger.error(f"Error fixing missing features: {e}")
        db.rollback()
    finally:
        db.close()

def initial_populate_job():
    """Populate database with cards from Pokemon TCG API on first startup"""
    db = SessionLocal()
    try:
        # Check if database needs population (fewer than 100 cards means it's likely empty or minimal)
        card_count = db.query(Card).count()
        logger.info(f"Database has {card_count} cards")
        
        if card_count < 100:
            logger.info("Database needs population. Fetching cards from Pokemon TCG API...")
            result = pokemon_tcg_sync.populate_database(max_cards=1000)
            if result.get("success"):
                logger.info(f"Initial population successful: {result.get('saved', 0)} cards saved, {result.get('updated', 0)} updated")
            else:
                logger.error(f"Initial population failed: {result.get('message', 'Unknown error')}")
        else:
            logger.info("Database already populated. Skipping initial population.")
        
        # Fix any cards missing features
        fix_missing_features()

        # Build in-memory search index
        logger.info("Building card search index...")
        card_index.build()
        logger.info(f"Card search index ready: {card_index.size} cards indexed")

    except Exception as e:
        logger.error(f"Error during initial population check: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup - Run initial population in background thread so server starts quickly
    populate_thread = threading.Thread(target=initial_populate_job, daemon=True)
    populate_thread.start()
    logger.info("Started background database population check...")
    
    # Schedule daily updates
    scheduler.add_job(
        daily_update_job,
        trigger=CronTrigger(hour=2, minute=0),  # Run at 2 AM daily
        id='daily_card_update',
        name='Daily Pokemon Card Database Update',
        replace_existing=True
    )
    scheduler.start()
    logger.info("Scheduler started - Daily updates scheduled at 2 AM UTC")
    yield
    # Shutdown
    scheduler.shutdown()
    logger.info("Scheduler stopped")

app = FastAPI(
    title="Pokedictor API",
    description="Pokemon Card Value Prediction API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app", "https://valuedex.ca", "https://www.valuedex.ca"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(cards.router, prefix="/api/cards", tags=["cards"])
app.include_router(predictions.router, prefix="/api", tags=["predictions"])
app.include_router(admin.router, prefix="/api", tags=["admin"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to Pokedictor API",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
