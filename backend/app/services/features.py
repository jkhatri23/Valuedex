from typing import Dict
import random

from app.models.card import Card, CardFeature
from app.services.feature_migrations import ensure_card_features_sentiment_column
from app.services.sentiment import sentiment_service

# Ensure DB column exists at import time
ensure_card_features_sentiment_column()

class FeatureService:
    """Calculate features for ML model and investment ratings"""
    
    @staticmethod
    def _clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
        return max(min_value, min(max_value, value))
    
    @classmethod
    def _scale(cls, value: float, min_value: float, max_value: float) -> float:
        if max_value == min_value:
            return 0.5
        normalized = (value - min_value) / (max_value - min_value)
        return cls._clamp(normalized)
    
    @classmethod
    def _prefer_range(
        cls,
        value: float,
        ideal_min: float,
        ideal_max: float,
        absolute_min: float,
        absolute_max: float
    ) -> float:
        """
        Scores how well a value sits inside an ideal band while penalizing extremes.
        Returns 0-1 where 1 represents the sweet spot.
        """
        if value <= absolute_min or value >= absolute_max:
            return 0.0
        if ideal_min <= value <= ideal_max:
            return 1.0
        
        if value < ideal_min:
            gap = ideal_min - value
            span = ideal_min - absolute_min
        else:
            gap = value - ideal_max
            span = absolute_max - ideal_max
        
        if span <= 0:
            return 0.0
        
        return cls._clamp(1 - (gap / span))
    
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
        Calculate investment score (1-10) and rating.
        The score blends fundamentals, momentum, sentiment, stability, and valuation so
        it mirrors the same signals we use during price prediction.
        """
        rarity_score = rarity_score if rarity_score is not None else 0.0
        popularity_score = popularity_score if popularity_score is not None else 50.0
        artist_score = artist_score if artist_score is not None else 5.0
        trend_30d = trend_30d if trend_30d is not None else 0.0
        trend_90d = trend_90d if trend_90d is not None else 0.0
        trend_1y = trend_1y if trend_1y is not None else 0.0
        volatility = volatility if volatility is not None else 15.0
        market_sentiment = market_sentiment if market_sentiment is not None else 50.0
        current_price = current_price if current_price is not None else 50.0
        
        fundamentals = (
            (rarity_score / 10) * 0.4 +
            (popularity_score / 100) * 0.4 +
            (artist_score / 10) * 0.2
        ) * 10
        
        short_term = self._scale(trend_30d, -15, 20)
        mid_term = self._scale(trend_90d, -20, 25)
        long_term = self._scale(trend_1y, -30, 40)
        momentum = (
            short_term * 0.25 +
            mid_term * 0.30 +
            long_term * 0.45
        ) * 10
        
        sentiment_component = self._scale(market_sentiment, 35, 80)
        sentiment = (
            sentiment_component * 0.65 +
            (popularity_score / 100) * 0.35
        ) * 10
        
        volatility_quality = self._prefer_range(volatility, 12, 28, 5, 45)
        liquidity_quality = self._prefer_range(current_price, 25, 250, 5, 1000)
        stability = (volatility_quality * 0.7 + liquidity_quality * 0.3) * 10
        
        fundamentals_scale = fundamentals / 10
        price_scale = self._scale(current_price, 50, 600)
        value_alignment = self._clamp(0.5 + (fundamentals_scale - price_scale) * 0.6)
        valuation = value_alignment * 10
        
        composite_score = (
            fundamentals * 0.30 +
            momentum * 0.25 +
            sentiment * 0.15 +
            stability * 0.15 +
            valuation * 0.15
        )
        
        penalty = 0.0
        if trend_30d < -10:
            penalty += 0.3
        if trend_90d < -8:
            penalty += 0.4
        if trend_1y < -5:
            penalty += 0.5
        if volatility > 35:
            penalty += 0.4
        
        bonus = 0.0
        if fundamentals >= 7.5 and momentum >= 6.5 and sentiment >= 6.0:
            bonus += 0.3
        
        score = composite_score - penalty + bonus
        
        # Clamp to 1-10 so the rating scale remains familiar
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

