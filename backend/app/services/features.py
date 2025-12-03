from typing import Dict
import random

from app.models.card import Card, CardFeature
from app.services.feature_migrations import ensure_card_features_sentiment_column
from app.services.sentiment import sentiment_service

# Ensure DB column exists at import time
ensure_card_features_sentiment_column()

class FeatureService:
    """Calculate features for ML model and investment ratings"""
    
    # Rarity tiers (higher = more rare)
    RARITY_SCORES = {
        "common": 1.0,
        "uncommon": 2.5,
        "rare": 4.0,
        "holo rare": 6.0,
        "ultra rare": 8.0,
        "secret rare": 9.5,
        "promotional": 5.0,
    }
    
    # Popular Pokemon (based on general popularity)
    POKEMON_POPULARITY = {
        "charizard": 100,
        "pikachu": 95,
        "mewtwo": 90,
        "lugia": 85,
        "rayquaza": 85,
        "gengar": 80,
        "gyarados": 80,
        "dragonite": 78,
        "eevee": 85,
        "mew": 90,
        "blastoise": 82,
        "venusaur": 80,
        "umbreon": 88,
        "espeon": 85,
        "lucario": 75,
    }
    
    # Notable artists
    ARTIST_SCORES = {
        "ken sugimori": 9.0,
        "mitsuhiro arita": 8.5,
        "atsuko nishida": 8.0,
        "kouki saitou": 7.5,
        "sowsow": 7.0,
        "5ban graphics": 6.0,
    }
    
    def calculate_rarity_score(self, rarity: str) -> float:
        """Calculate rarity score (0-10)"""
        if not rarity:
            return 3.0
        
        rarity_lower = rarity.lower()
        for key, score in self.RARITY_SCORES.items():
            if key in rarity_lower:
                return score
        
        return 3.0
    
    def calculate_popularity_score(self, card_name: str) -> float:
        """Calculate Pokemon popularity (0-100)"""
        if not card_name:
            return 50.0
        
        name_lower = card_name.lower()
        
        # Check for known Pokemon
        for pokemon, score in self.POKEMON_POPULARITY.items():
            if pokemon in name_lower:
                return score
        
        # Default medium popularity
        return random.uniform(40, 60)
    
    def calculate_artist_score(self, artist: str) -> float:
        """Calculate artist popularity (0-10)"""
        if not artist:
            return 5.0
        
        artist_lower = artist.lower()
        for known_artist, score in self.ARTIST_SCORES.items():
            if known_artist in artist_lower:
                return score
        
        return 5.0
    
    def calculate_investment_score(
        self,
        current_price: float,
        rarity_score: float,
        popularity_score: float,
        artist_score: float,
        trend_30d: float,
        trend_90d: float,
        trend_1y: float,
        volatility: float,
        market_sentiment: float,
    ) -> tuple[float, str]:
        """
        Calculate investment score (1-10) and rating
        Similar to stock ratings: Strong Buy, Buy, Hold, Sell
        """
        score = 5.0  # Base score
        
        # Rarity factor (higher rarity = better investment)
        score += (rarity_score / 10) * 1.5
        
        # Popularity factor
        score += (popularity_score / 100) * 2.0
        
        # Artist factor
        score += (artist_score / 10) * 0.8
        
        # Trend factors (positive trends increase score)
        if trend_1y > 10:
            score += 1.5
        elif trend_1y > 5:
            score += 0.8
        elif trend_1y < -10:
            score -= 1.0
        
        if trend_90d > 5:
            score += 0.5
        elif trend_90d < -5:
            score -= 0.5
        
        # Sentiment factor (market buzz can drive demand)
        sentiment_normalized = (market_sentiment - 50) / 50  # -1 to 1 range
        score += sentiment_normalized * 1.2
        
        # Volatility (moderate volatility is good for growth)
        if 10 < volatility < 25:
            score += 0.5
        elif volatility > 40:
            score -= 0.3
        
        # Price tier (very expensive cards are less liquid)
        if current_price > 500:
            score -= 0.3
        elif 50 < current_price < 200:
            score += 0.2
        
        # Clamp to 1-10
        score = max(1.0, min(10.0, score))
        
        # Determine rating
        if score >= 8.5:
            rating = "Strong Buy"
        elif score >= 7.0:
            rating = "Buy"
        elif score >= 5.5:
            rating = "Hold"
        elif score >= 4.0:
            rating = "Underperform"
        else:
            rating = "Sell"
        
        return round(score, 2), rating
    
    def create_card_features(
        self,
        card: Card,
        current_price: float,
        price_history: list
    ) -> Dict:
        """Create all features for a card"""
        
        # Calculate basic features
        rarity_score = self.calculate_rarity_score(card.rarity)
        popularity_score = self.calculate_popularity_score(card.name)
        artist_score = self.calculate_artist_score(card.artist)
        
        # Calculate trends (mock for now - would use real price history)
        trend_30d = random.uniform(-5, 15)
        trend_90d = random.uniform(-3, 20)
        trend_1y = random.uniform(0, 30)
        volatility = random.uniform(5, 25)
        
        # Market sentiment via Google Trends
        market_sentiment = sentiment_service.get_sentiment_score(card.name or card.set_name)
        
        # Calculate investment score
        investment_score, investment_rating = self.calculate_investment_score(
            current_price=current_price,
            rarity_score=rarity_score,
            popularity_score=popularity_score,
            artist_score=artist_score,
            trend_30d=trend_30d,
            trend_90d=trend_90d,
            trend_1y=trend_1y,
            volatility=volatility,
            market_sentiment=market_sentiment,
        )
        
        return {
            "popularity_score": popularity_score,
            "rarity_score": rarity_score,
            "artist_score": artist_score,
            "current_price": current_price,
            "price_volatility": volatility,
            "trend_30d": trend_30d,
            "trend_90d": trend_90d,
            "trend_1y": trend_1y,
            "market_sentiment": market_sentiment,
            "investment_score": investment_score,
            "investment_rating": investment_rating,
        }

feature_service = FeatureService()

