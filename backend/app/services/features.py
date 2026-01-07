"""Feature calculation for cards."""

from typing import Dict
import random
from app.models.card import Card


class FeatureService:
    """Calculate features for ML model and investment ratings."""
    
    RARITY_SCORES = {
        "common": 1.0, "uncommon": 2.5, "rare": 4.0,
        "holo rare": 6.0, "ultra rare": 8.0, "secret rare": 9.5,
    }
    
    POKEMON_POPULARITY = {
        "charizard": 100, "pikachu": 95, "mewtwo": 90,
        "lugia": 85, "rayquaza": 85, "gengar": 80,
        "mew": 90, "blastoise": 82, "venusaur": 80,
        "umbreon": 88, "espeon": 85,
    }
    
    ARTIST_SCORES = {
        "ken sugimori": 9.0, "mitsuhiro arita": 8.5,
        "atsuko nishida": 8.0, "kouki saitou": 7.5,
    }
    
    def calculate_rarity_score(self, rarity: str) -> float:
        if not rarity:
            return 3.0
        rarity_lower = rarity.lower()
        for key, score in self.RARITY_SCORES.items():
            if key in rarity_lower:
                return score
        return 3.0
    
    def calculate_popularity_score(self, name: str) -> float:
        if not name:
            return 50.0
        name_lower = name.lower()
        for pokemon, score in self.POKEMON_POPULARITY.items():
            if pokemon in name_lower:
                return float(score)
        return random.uniform(40, 60)
    
    def calculate_artist_score(self, artist: str) -> float:
        if not artist:
            return 5.0
        artist_lower = artist.lower()
        for known, score in self.ARTIST_SCORES.items():
            if known in artist_lower:
                return score
        return 5.0
    
    def calculate_investment_score(
        self, price: float, rarity: float, popularity: float,
        artist: float, trend_30d: float, trend_1y: float, volatility: float
    ) -> tuple[float, str]:
        """Calculate investment score (1-10) and rating."""
        fundamentals = (rarity / 10) * 0.4 + (popularity / 100) * 0.4 + (artist / 10) * 0.2
        momentum = max(0, min(1, (trend_1y + 30) / 70))
        stability = max(0, min(1, 1 - (volatility / 50)))
        
        score = (fundamentals * 5 + momentum * 3 + stability * 2)
        score = max(1.0, min(10.0, score))
        
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
    
    def create_card_features(self, card: Card, current_price: float, price_history: list) -> Dict:
        """Create features for a card."""
        rarity = self.calculate_rarity_score(card.rarity)
        popularity = self.calculate_popularity_score(card.name)
        artist = self.calculate_artist_score(card.artist)
        
        trend_30d = random.uniform(-5, 15)
        trend_90d = random.uniform(-3, 20)
        trend_1y = random.uniform(0, 30)
        volatility = random.uniform(5, 25)
        sentiment = random.uniform(40, 70)
        
        score, rating = self.calculate_investment_score(
            current_price, rarity, popularity, artist, trend_30d, trend_1y, volatility
        )
        
        return {
            "popularity_score": popularity,
            "rarity_score": rarity,
            "artist_score": artist,
            "current_price": current_price,
            "price_volatility": volatility,
            "trend_30d": trend_30d,
            "trend_90d": trend_90d,
            "trend_1y": trend_1y,
            "market_sentiment": sentiment,
            "investment_score": score,
            "investment_rating": rating,
        }


feature_service = FeatureService()
