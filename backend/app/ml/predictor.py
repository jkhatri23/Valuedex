import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class PricePredictor:
    """
    Advanced prediction model using cryptocurrency/financial forecasting techniques:
    1. Exponential Smoothing (Holt-Winters) - captures trends and seasonality
    2. Volume-Weighted Price Analysis - accounts for market activity
    3. Sentiment & Popularity Scoring - market psychology
    4. Monte Carlo Simulation - risk assessment & confidence intervals
    5. Multi-Scenario Analysis - conservative, moderate, aggressive predictions
    """
    
    def __init__(self):
        self.time_model = LinearRegression()
        self.feature_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.is_trained = False
        
    def exponential_smoothing(
        self, 
        data: np.ndarray, 
        alpha: float = 0.3, 
        beta: float = 0.1
    ) -> Tuple[np.ndarray, float, float]:
        """
        Double Exponential Smoothing (Holt's method) for trend forecasting.
        Similar to what's used in crypto price predictions.
        
        Args:
            data: Price history array
            alpha: Level smoothing parameter (0-1)
            beta: Trend smoothing parameter (0-1)
            
        Returns:
            smoothed values, final level, final trend
        """
        if len(data) < 2:
            return data, data[-1] if len(data) > 0 else 0, 0
            
        level = data[0]
        trend = data[1] - data[0] if len(data) > 1 else 0
        smoothed = [level]
        
        for i in range(1, len(data)):
            last_level = level
            level = alpha * data[i] + (1 - alpha) * (level + trend)
            trend = beta * (level - last_level) + (1 - beta) * trend
            smoothed.append(level)
            
        return np.array(smoothed), level, trend
    
    def calculate_volatility(self, prices: np.ndarray, window: int = 30) -> float:
        """
        Calculate price volatility (similar to crypto volatility metrics).
        Uses standard deviation of returns.
        """
        if len(prices) < 2:
            return 0.0
            
        returns = np.diff(prices) / prices[:-1]
        volatility = np.std(returns) * np.sqrt(252)  # Annualized volatility
        return volatility
    
    def monte_carlo_simulation(
        self,
        current_price: float,
        trend: float,
        volatility: float,
        years_ahead: int,
        n_simulations: int = 1000
    ) -> Tuple[float, float, float, np.ndarray]:
        """
        Monte Carlo simulation for price prediction with risk assessment.
        Standard in crypto and financial forecasting.
        
        Returns: (mean_price, lower_percentile, upper_percentile, all_simulations)
        """
        days = int(years_ahead * 365)
        dt = 1/365  # Daily time step
        
        # Normalize trend to annual percentage (convert from absolute daily trend)
        # Cap at realistic collectibles growth rate (max 30% annually = 0.3)
        annual_trend = np.clip(trend / current_price * 365, -0.5, 0.3)
        
        # Convert to daily drift rate
        drift = annual_trend * dt
        diffusion = volatility * np.sqrt(dt)
        
        simulations = np.zeros((n_simulations, days))
        simulations[:, 0] = current_price
        
        for i in range(n_simulations):
            for t in range(1, days):
                # Geometric Brownian Motion (GBM) with realistic constraints
                shock = np.random.normal(0, 1)
                simulations[i, t] = simulations[i, t-1] * np.exp(drift + diffusion * shock)
                
                # Safety cap: prevent runaway exponential growth
                max_reasonable = current_price * (1.5 ** years_ahead)  # Max 50% annual growth
                simulations[i, t] = min(simulations[i, t], max_reasonable)
        
        final_prices = simulations[:, -1]
        mean_price = np.mean(final_prices)
        lower_bound = np.percentile(final_prices, 10)  # 10th percentile (conservative)
        upper_bound = np.percentile(final_prices, 90)  # 90th percentile (optimistic)
        
        return mean_price, lower_bound, upper_bound, final_prices
    
    def prepare_time_series_data(
        self, 
        price_history: List[Dict],
        include_volume: bool = False
    ) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """Prepare time series data with optional volume weighting"""
        if not price_history:
            return np.array([]), np.array([]), None
        
        dates = []
        prices = []
        volumes = []
        
        for record in price_history:
            if isinstance(record.get('date'), str):
                date = datetime.fromisoformat(record['date'].replace('Z', '+00:00'))
            else:
                date = record['date']
            
            dates.append(date.timestamp())
            prices.append(record.get('price', record.get('price_loose', 0)))
            volumes.append(record.get('volume', 1) or 1)  # Default to 1 if no volume
        
        X = np.array(dates).reshape(-1, 1)
        y = np.array(prices)
        v = np.array(volumes) if include_volume else None
        
        return X, y, v
    
    def calculate_volume_weighted_price(
        self, 
        prices: np.ndarray, 
        volumes: np.ndarray
    ) -> float:
        """
        Volume-Weighted Average Price (VWAP) - standard in crypto/stock analysis.
        Gives more weight to prices with higher trading volume.
        """
        if volumes is None or len(volumes) == 0 or np.sum(volumes) == 0:
            return np.mean(prices)
        
        return np.sum(prices * volumes) / np.sum(volumes)
    
    def calculate_sentiment_multiplier(
        self,
        popularity_score: float,
        market_sentiment: float,
        trend_1y: float
    ) -> float:
        """
        Calculate sentiment-based growth multiplier.
        Combines popularity, market sentiment, and recent trends.
        
        Args:
            popularity_score: 0-100, card popularity
            market_sentiment: 0-100, overall market sentiment
            trend_1y: Annual price change percentage
            
        Returns:
            Growth multiplier (typically 0.85 - 1.25)
        """
        # Handle None values with defaults
        popularity_score = popularity_score if popularity_score is not None else 50
        market_sentiment = market_sentiment if market_sentiment is not None else 50
        trend_1y = trend_1y if trend_1y is not None else 0
        
        # Normalize inputs
        popularity_factor = (popularity_score / 100) * 0.15  # Max 15% boost
        sentiment_factor = ((market_sentiment - 50) / 50) * 0.10  # +/- 10%
        
        # Momentum factor based on 1-year trend
        if trend_1y > 20:
            momentum_factor = 0.10  # Strong momentum
        elif trend_1y > 5:
            momentum_factor = 0.05  # Moderate momentum
        elif trend_1y < -10:
            momentum_factor = -0.10  # Negative momentum
        else:
            momentum_factor = 0.0
        
        # Combined multiplier (typically 0.85 to 1.25)
        multiplier = 1.0 + popularity_factor + sentiment_factor + momentum_factor
        return np.clip(multiplier, 0.85, 1.25)
    
    def predict_with_advanced_time_series(
        self,
        price_history: List[Dict],
        years_ahead: int,
        features: Optional[Dict] = None
    ) -> Dict:
        """
        Advanced time series prediction using:
        1. Exponential Smoothing for trend
        2. Monte Carlo simulation for risk assessment
        3. Volume-weighted adjustments
        4. Sentiment-based multipliers
        
        Returns: Comprehensive prediction with multiple scenarios
        """
        X, y, volumes = self.prepare_time_series_data(price_history, include_volume=True)
        
        if len(y) < 2:
            # Not enough data
            current_price = price_history[-1].get('price', 0) if price_history else 100.0
            return {
                "base_prediction": current_price,
                "conservative": current_price * 0.8,
                "moderate": current_price,
                "aggressive": current_price * 1.3,
                "confidence_lower": current_price * 0.6,
                "confidence_upper": current_price * 1.5,
                "risk_level": "high",
                "volatility": 0.0
            }
        
        # 1. Apply exponential smoothing to capture trend
        # Use conservative smoothing parameters to avoid overreacting to recent noise
        smoothed_prices, level, trend = self.exponential_smoothing(y, alpha=0.2, beta=0.05)
        
        # 2. Calculate historical volatility
        volatility = self.calculate_volatility(y)
        
        # 3. Get current/recent price (prefer volume-weighted)
        if volumes is not None and len(volumes) > 0:
            recent_prices = y[-min(30, len(y)):]
            recent_volumes = volumes[-min(30, len(volumes)):]
            current_price = self.calculate_volume_weighted_price(recent_prices, recent_volumes)
        else:
            current_price = y[-1]
        
        # 4. Apply sentiment multiplier if features provided
        sentiment_multiplier = 1.0
        if features:
            popularity = features.get('popularity_score', 50)
            sentiment = features.get('market_sentiment', 50)
            trend_1y = features.get('trend_1y', 0)
            sentiment_multiplier = self.calculate_sentiment_multiplier(
                popularity, sentiment, trend_1y
            )
        
        # Adjust trend with sentiment - cap to prevent unrealistic growth
        # Trend should represent reasonable daily price change
        max_daily_trend = current_price * 0.001  # Max 0.1% daily = ~36% annually
        adjusted_trend = np.clip(trend * sentiment_multiplier, -max_daily_trend, max_daily_trend)
        
        # 5. Monte Carlo simulation for robust predictions
        mean_price, mc_lower, mc_upper, simulations = self.monte_carlo_simulation(
            current_price=current_price,
            trend=adjusted_trend,
            volatility=volatility,
            years_ahead=years_ahead,
            n_simulations=1000
        )
        
        # 6. Generate multiple scenarios
        # Conservative: 25th percentile with reduced trend
        conservative_price = np.percentile(simulations, 25)
        
        # Moderate: 50th percentile (median)
        moderate_price = np.percentile(simulations, 50)
        
        # Aggressive: 75th percentile with enhanced trend
        aggressive_price = np.percentile(simulations, 75)
        
        # 7. Risk assessment
        downside_risk = (current_price - mc_lower) / current_price
        upside_potential = (mc_upper - current_price) / current_price
        
        if downside_risk > 0.30:
            risk_level = "high"
        elif downside_risk > 0.15:
            risk_level = "moderate"
        else:
            risk_level = "low"
        
        return {
            "base_prediction": float(mean_price),
            "conservative": float(conservative_price),
            "moderate": float(moderate_price),
            "aggressive": float(aggressive_price),
            "confidence_lower": float(mc_lower),
            "confidence_upper": float(mc_upper),
            "risk_level": risk_level,
            "volatility": float(volatility),
            "downside_risk_pct": float(downside_risk * 100),
            "upside_potential_pct": float(upside_potential * 100),
            "sentiment_multiplier": float(sentiment_multiplier),
            "current_trend": float(trend)
        }
    
    def predict_with_features(
        self,
        features: Dict,
        years_ahead: int
    ) -> float:
        """
        Feature-based prediction with enhanced market factors.
        Incorporates card attributes, market sentiment, and momentum.
        """
        
        # Feature-based growth rate calculation with None handling
        current_price = features.get('current_price') or 100
        rarity_score = features.get('rarity_score') or 5
        popularity_score = features.get('popularity_score') or 50
        artist_score = features.get('artist_score') or 5
        trend_1y = features.get('trend_1y') or 0
        market_sentiment = features.get('market_sentiment') or 50
        volatility = features.get('volatility') or 0.2
        
        # Base annual growth rate (%) - collectibles historically grow 5-8%
        base_growth = 6.0
        
        # Adjust based on features (weighted by importance)
        rarity_boost = (rarity_score / 10) * 3.5  # Up to 3.5% boost
        popularity_boost = (popularity_score / 100) * 5  # Up to 5% boost
        artist_boost = (artist_score / 10) * 2  # Up to 2% boost
        
        # Momentum factor (recent trends are important)
        if trend_1y > 20:
            trend_boost = 6  # Strong positive momentum
        elif trend_1y > 10:
            trend_boost = 4
        elif trend_1y > 0:
            trend_boost = 2
        elif trend_1y > -10:
            trend_boost = 0
        else:
            trend_boost = -3  # Negative momentum
        
        # Sentiment boost (market psychology matters)
        sentiment_boost = ((market_sentiment - 50) / 50) * 4  # +/-4% based on sentiment
        
        # Volatility adjustment (high volatility = higher potential)
        volatility_factor = min(volatility * 2, 2)  # Cap at 2%
        
        annual_growth_rate = (
            base_growth
            + rarity_boost
            + popularity_boost
            + artist_boost
            + trend_boost
            + sentiment_boost
            + volatility_factor
        )
        
        # Apply compound growth with decay for long-term predictions
        # Growth rates tend to moderate over time
        decay_factor = 0.95 ** (years_ahead - 1)  # Slight decay each year
        adjusted_growth = annual_growth_rate * decay_factor
        
        growth_multiplier = (1 + adjusted_growth / 100) ** years_ahead
        predicted_price = current_price * growth_multiplier
        
        return predicted_price
    
    def predict_hybrid(
        self,
        price_history: List[Dict],
        features: Dict,
        years_ahead: int
    ) -> Dict:
        """
        Advanced hybrid prediction using:
        - Exponential smoothing + Monte Carlo simulation
        - Volume-weighted price analysis
        - Sentiment & popularity scoring
        - Multiple scenario generation (conservative, moderate, aggressive)
        
        This approach mirrors cryptocurrency prediction models for
        optimal risk-reward balance.
        """
        
        # Get advanced time series prediction with all features
        ts_result = self.predict_with_advanced_time_series(
            price_history=price_history,
            years_ahead=years_ahead,
            features=features
        )
        
        # Feature-based adjustment for long-term factors
        feature_price = self.predict_with_features(features, years_ahead)
        
        # Weight based on data availability and quality
        if len(price_history) >= 12:  # At least 1 year of data
            # Trust time series more with good history
            final_price = (ts_result["moderate"] * 0.75) + (feature_price * 0.25)
            conservative = (ts_result["conservative"] * 0.75) + (feature_price * 0.8 * 0.25)
            aggressive = (ts_result["aggressive"] * 0.75) + (feature_price * 1.2 * 0.25)
        else:
            # Balance both methods with limited history
            final_price = (ts_result["moderate"] * 0.5) + (feature_price * 0.5)
            conservative = (ts_result["conservative"] * 0.5) + (feature_price * 0.85 * 0.5)
            aggressive = (ts_result["aggressive"] * 0.5) + (feature_price * 1.15 * 0.5)
        
        target_date = datetime.now() + timedelta(days=years_ahead * 365)
        
        # Calculate reward-risk ratio
        upside = ts_result["upside_potential_pct"]
        downside = ts_result["downside_risk_pct"]
        reward_risk_ratio = upside / max(downside, 1)  # Higher is better
        
        # Investment recommendation based on risk-reward
        if reward_risk_ratio > 2.5 and ts_result["risk_level"] == "low":
            recommendation = "strong_buy"
        elif reward_risk_ratio > 1.5 and ts_result["risk_level"] != "high":
            recommendation = "buy"
        elif reward_risk_ratio > 1.0:
            recommendation = "hold"
        elif reward_risk_ratio > 0.5:
            recommendation = "consider_selling"
        else:
            recommendation = "sell"
        
        return {
            # Primary prediction
            "predicted_price": round(final_price, 2),
            "confidence_lower": round(ts_result["confidence_lower"], 2),
            "confidence_upper": round(ts_result["confidence_upper"], 2),
            
            # Multiple scenarios
            "scenarios": {
                "conservative": round(conservative, 2),
                "moderate": round(final_price, 2),
                "aggressive": round(aggressive, 2)
            },
            
            # Risk metrics
            "risk_assessment": {
                "risk_level": ts_result["risk_level"],
                "volatility": round(ts_result["volatility"], 3),
                "downside_risk_pct": round(downside, 2),
                "upside_potential_pct": round(upside, 2),
                "reward_risk_ratio": round(reward_risk_ratio, 2)
            },
            
            # Market factors
            "market_factors": {
                "sentiment_multiplier": round(ts_result["sentiment_multiplier"], 3),
                "popularity_score": features.get("popularity_score", 50),
                "market_sentiment": features.get("market_sentiment", 50),
                "current_trend": round(ts_result["current_trend"], 2)
            },
            
            # Metadata
            "target_date": target_date.isoformat(),
            "years_ahead": years_ahead,
            "model_version": "advanced_v2_crypto",
            "recommendation": recommendation,
            
            # Model contributions (for transparency)
            "time_series_prediction": round(ts_result["moderate"], 2),
            "feature_prediction": round(feature_price, 2)
        }
    
    def generate_prediction_timeline(
        self,
        price_history: List[Dict],
        features: Dict,
        max_years: int = 5
    ) -> List[Dict]:
        """
        Generate predictions for multiple years with full risk analysis.
        Provides conservative, moderate, and aggressive scenarios for each timeframe.
        """
        
        timeline = []
        
        for year in range(1, max_years + 1):
            prediction = self.predict_hybrid(price_history, features, year)
            
            # Simplify for timeline (keep essential info)
            timeline.append({
                "years_ahead": year,
                "target_date": prediction["target_date"],
                "predicted_price": prediction["predicted_price"],
                "conservative": prediction["scenarios"]["conservative"],
                "moderate": prediction["scenarios"]["moderate"],
                "aggressive": prediction["scenarios"]["aggressive"],
                "confidence_lower": prediction["confidence_lower"],
                "confidence_upper": prediction["confidence_upper"],
                "risk_level": prediction["risk_assessment"]["risk_level"],
                "recommendation": prediction["recommendation"]
            })
        
        return timeline

# Create singleton
predictor = PricePredictor()

