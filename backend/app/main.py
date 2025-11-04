from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.api import cards, predictions, admin
from app.database import engine, Base
from app.services.pokemon_tcg_sync import pokemon_tcg_sync
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables
Base.metadata.create_all(bind=engine)

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
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
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
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

