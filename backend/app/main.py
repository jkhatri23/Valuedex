from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import cards, predictions
from app.database import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Pokedictor API",
    description="Pokemon Card Value Prediction API",
    version="1.0.0"
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

