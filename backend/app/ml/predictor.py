"""Price prediction using time series analysis and Monte Carlo simulation."""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class PricePredictor:
    """Hybrid prediction model combining time series and feature-based analysis."""
    
    def exponential_smoothing(self, data: np.ndarray, alpha: float = 0.3, beta: float = 0.1) -> Tuple[np.ndarray, float, float]:
        """Double exponential smoothing (Holt's method)."""
        if len(data) < 2:
            return data, data[-1] if len(data) > 0 else 0, 0
        
        level = data[0]
        trend = data[1] - data[0]
        smoothed = [level]
        
        for i in range(1, len(data)):
            last_level = level
            level = alpha * data[i] + (1 - alpha) * (level + trend)
            trend = beta * (level - last_level) + (1 - beta) * trend
            smoothed.append(level)
        
        return np.array(smoothed), level, trend
    
    def calculate_volatility(self, prices: np.ndarray) -> float:
        """Calculate annualized volatility from price returns."""
        if len(prices) < 2:
            return 0.0
        returns = np.diff(prices) / prices[:-1]
        return float(np.std(returns) * np.sqrt(252))
    
    def monte_carlo_simulation(
        self,
        current_price: float,
        trend: float,
        volatility: float,
        years_ahead: int,
        n_simulations: int = 1000
    ) -> Tuple[float, float, float, np.ndarray]:
        """Monte Carlo simulation for price prediction."""
        days = int(years_ahead * 365)
        dt = 1/365
        
        annual_trend = np.clip(trend / current_price * 365, -0.5, 0.3)
        drift = annual_trend * dt
        diffusion = volatility * np.sqrt(dt)
        
        simulations = np.zeros((n_simulations, days))
        simulations[:, 0] = current_price
        
        for i in range(n_simulations):
            for t in range(1, days):
                shock = np.random.normal(0, 1)
                simulations[i, t] = simulations[i, t-1] * np.exp(drift + diffusion * shock)
                max_price = current_price * (1.5 ** years_ahead)
                simulations[i, t] = min(simulations[i, t], max_price)
        
        final_prices = simulations[:, -1]
        return (
            float(np.mean(final_prices)),
            float(np.percentile(final_prices, 10)),
            float(np.percentile(final_prices, 90)),
            final_prices
        )
    
    def prepare_time_series_data(self, price_history: List[Dict]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Extract timestamps, prices, and volumes from history."""
        if not price_history:
            return np.array([]), np.array([]), np.array([])
        
        dates, prices, volumes = [], [], []
        for record in price_history:
            date = record.get('date')
            if isinstance(date, str):
                date = datetime.fromisoformat(date.replace('Z', '+00:00'))
            dates.append(date.timestamp())
            prices.append(record.get('price', record.get('price_loose', 0)))
            volumes.append(record.get('volume', 1) or 1)
        
        return np.array(dates), np.array(prices), np.array(volumes)
    
    def calculate_sentiment_multiplier(self, popularity: float, sentiment: float, trend_1y: float) -> float:
        """Calculate growth multiplier based on market sentiment."""
        popularity = popularity if popularity is not None else 50
        sentiment = sentiment if sentiment is not None else 50
        trend_1y = trend_1y if trend_1y is not None else 0
        
        popularity_factor = (popularity / 100) * 0.15
        sentiment_factor = ((sentiment - 50) / 50) * 0.10
        
        if trend_1y > 20:
            momentum = 0.10
        elif trend_1y > 5:
            momentum = 0.05
        elif trend_1y < -10:
            momentum = -0.10
        else:
            momentum = 0.0
        
        return float(np.clip(1.0 + popularity_factor + sentiment_factor + momentum, 0.85, 1.25))
    
    def predict_with_time_series(self, price_history: List[Dict], years_ahead: int, features: Optional[Dict] = None) -> Dict:
        """Time series prediction with Monte Carlo simulation."""
        _, y, volumes = self.prepare_time_series_data(price_history)
        
        if len(y) < 2:
            price = price_history[-1].get('price', 100.0) if price_history else 100.0
            return {
                "base_prediction": price,
                "conservative": price * 0.8,
                "moderate": price,
                "aggressive": price * 1.3,
                "confidence_lower": price * 0.6,
                "confidence_upper": price * 1.5,
                "risk_level": "high",
                "volatility": 0.0,
                "downside_risk_pct": 20.0,
                "upside_potential_pct": 50.0,
                "sentiment_multiplier": 1.0,
                "current_trend": 0.0
            }
        
        _, level, trend = self.exponential_smoothing(y, alpha=0.2, beta=0.05)
        volatility = self.calculate_volatility(y)
        
        recent = y[-min(30, len(y)):]
        recent_vol = volumes[-min(30, len(volumes)):] if len(volumes) > 0 else None
        if recent_vol is not None and np.sum(recent_vol) > 0:
            current_price = float(np.sum(recent * recent_vol) / np.sum(recent_vol))
        else:
            current_price = float(y[-1])
        
        sentiment_mult = 1.0
        if features:
            sentiment_mult = self.calculate_sentiment_multiplier(
                features.get('popularity_score', 50),
                features.get('market_sentiment', 50),
                features.get('trend_1y', 0)
            )
        
        max_daily = current_price * 0.001
        adjusted_trend = float(np.clip(trend * sentiment_mult, -max_daily, max_daily))
        
        mean_price, mc_lower, mc_upper, sims = self.monte_carlo_simulation(
            current_price, adjusted_trend, volatility, years_ahead
        )
        
        downside = (current_price - mc_lower) / current_price
        upside = (mc_upper - current_price) / current_price
        
        if downside > 0.30:
            risk = "high"
        elif downside > 0.15:
            risk = "moderate"
        else:
            risk = "low"
        
        return {
            "base_prediction": mean_price,
            "conservative": float(np.percentile(sims, 25)),
            "moderate": float(np.percentile(sims, 50)),
            "aggressive": float(np.percentile(sims, 75)),
            "confidence_lower": mc_lower,
            "confidence_upper": mc_upper,
            "risk_level": risk,
            "volatility": volatility,
            "downside_risk_pct": float(downside * 100),
            "upside_potential_pct": float(upside * 100),
            "sentiment_multiplier": sentiment_mult,
            "current_trend": float(trend)
        }
    
    def predict_with_features(self, features: Dict, years_ahead: int) -> float:
        """Feature-based price prediction."""
        current = features.get('current_price') or 100
        rarity = features.get('rarity_score') or 5
        popularity = features.get('popularity_score') or 50
        artist = features.get('artist_score') or 5
        trend_1y = features.get('trend_1y') or 0
        sentiment = features.get('market_sentiment') or 50
        vol = features.get('volatility') or 0.2
        
        growth = 6.0  # Base annual growth
        growth += (rarity / 10) * 3.5
        growth += (popularity / 100) * 5
        growth += (artist / 10) * 2
        
        if trend_1y > 20:
            growth += 6
        elif trend_1y > 10:
            growth += 4
        elif trend_1y > 0:
            growth += 2
        elif trend_1y < -10:
            growth -= 3
        
        growth += ((sentiment - 50) / 50) * 4
        growth += min(vol * 2, 2)
        
        decay = 0.95 ** (years_ahead - 1)
        multiplier = (1 + growth * decay / 100) ** years_ahead
        
        return float(current * multiplier)
    
    def predict_hybrid(self, price_history: List[Dict], features: Dict, years_ahead: int) -> Dict:
        """Hybrid prediction combining time series and feature analysis."""
        ts = self.predict_with_time_series(price_history, years_ahead, features)
        feat_price = self.predict_with_features(features, years_ahead)
        
        if len(price_history) >= 12:
            final = ts["moderate"] * 0.75 + feat_price * 0.25
            conservative = ts["conservative"] * 0.75 + feat_price * 0.8 * 0.25
            aggressive = ts["aggressive"] * 0.75 + feat_price * 1.2 * 0.25
        else:
            final = ts["moderate"] * 0.5 + feat_price * 0.5
            conservative = ts["conservative"] * 0.5 + feat_price * 0.85 * 0.5
            aggressive = ts["aggressive"] * 0.5 + feat_price * 1.15 * 0.5
        
        target_date = datetime.now() + timedelta(days=years_ahead * 365)
        
        upside = ts["upside_potential_pct"]
        downside = ts["downside_risk_pct"]
        reward_risk = upside / max(downside, 1)
        
        if reward_risk > 2.5 and ts["risk_level"] == "low":
            rec = "strong_buy"
        elif reward_risk > 1.5 and ts["risk_level"] != "high":
            rec = "buy"
        elif reward_risk > 1.0:
            rec = "hold"
        elif reward_risk > 0.5:
            rec = "consider_selling"
        else:
            rec = "sell"
        
        return {
            "predicted_price": round(final, 2),
            "confidence_lower": round(ts["confidence_lower"], 2),
            "confidence_upper": round(ts["confidence_upper"], 2),
            "scenarios": {
                "conservative": round(conservative, 2),
                "moderate": round(final, 2),
                "aggressive": round(aggressive, 2)
            },
            "risk_assessment": {
                "risk_level": ts["risk_level"],
                "volatility": round(ts["volatility"], 3),
                "downside_risk_pct": round(downside, 2),
                "upside_potential_pct": round(upside, 2),
                "reward_risk_ratio": round(reward_risk, 2)
            },
            "market_factors": {
                "sentiment_multiplier": round(ts["sentiment_multiplier"], 3),
                "popularity_score": features.get("popularity_score", 50),
                "market_sentiment": features.get("market_sentiment", 50),
                "current_trend": round(ts["current_trend"], 2)
            },
            "target_date": target_date.isoformat(),
            "years_ahead": years_ahead,
            "model_version": "v2",
            "recommendation": rec,
            "time_series_prediction": round(ts["moderate"], 2),
            "feature_prediction": round(feat_price, 2)
        }
    
    def generate_prediction_timeline(self, price_history: List[Dict], features: Dict, max_years: int = 5) -> List[Dict]:
        """Generate predictions for multiple years."""
        timeline = []
        for year in range(1, max_years + 1):
            p = self.predict_hybrid(price_history, features, year)
            timeline.append({
                "years_ahead": year,
                "target_date": p["target_date"],
                "predicted_price": p["predicted_price"],
                "conservative": p["scenarios"]["conservative"],
                "moderate": p["scenarios"]["moderate"],
                "aggressive": p["scenarios"]["aggressive"],
                "confidence_lower": p["confidence_lower"],
                "confidence_upper": p["confidence_upper"],
                "risk_level": p["risk_assessment"]["risk_level"],
                "recommendation": p["recommendation"]
            })
        return timeline


predictor = PricePredictor()
