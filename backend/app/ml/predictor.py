import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
import joblib

class PricePredictor:
    """
    Hybrid prediction model combining:
    1. Time-series forecasting (trend-based)
    2. Feature-based regression (rarity, popularity, etc.)
    """
    
    def __init__(self):
        self.time_model = LinearRegression()
        self.feature_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.is_trained = False
    
    def prepare_time_series_data(self, price_history: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare time series data for training"""
        if not price_history:
            return np.array([]), np.array([])
        
        dates = []
        prices = []
        
        for record in price_history:
            if isinstance(record.get('date'), str):
                date = datetime.fromisoformat(record['date'].replace('Z', '+00:00'))
            else:
                date = record['date']
            
            dates.append(date.timestamp())
            prices.append(record.get('price', record.get('price_loose', 0)))
        
        X = np.array(dates).reshape(-1, 1)
        y = np.array(prices)
        
        return X, y
    
    def predict_with_time_series(
        self,
        price_history: List[Dict],
        years_ahead: int
    ) -> Tuple[float, float, float]:
        """
        Predict price using time series analysis
        Returns: (predicted_price, lower_bound, upper_bound)
        """
        
        X, y = self.prepare_time_series_data(price_history)
        
        if len(X) < 2:
            # Not enough data, return current price with wider confidence
            current_price = price_history[-1].get('price', 0) if price_history else 100.0
            return current_price, current_price * 0.7, current_price * 1.5
        
        # Train simple linear model
        self.time_model.fit(X, y)
        
        # Predict future date
        future_date = datetime.now() + timedelta(days=years_ahead * 365)
        future_timestamp = np.array([[future_date.timestamp()]])
        
        predicted_price = self.time_model.predict(future_timestamp)[0]
        
        # Calculate confidence interval based on historical variance
        residuals = y - self.time_model.predict(X)
        std_error = np.std(residuals)
        
        # Confidence widens with time
        confidence_multiplier = 1 + (years_ahead * 0.1)
        lower_bound = predicted_price - (std_error * confidence_multiplier * 1.96)
        upper_bound = predicted_price + (std_error * confidence_multiplier * 1.96)
        
        # Ensure non-negative prices
        predicted_price = max(0, predicted_price)
        lower_bound = max(0, lower_bound)
        upper_bound = max(lower_bound, upper_bound)
        
        return predicted_price, lower_bound, upper_bound
    
    def predict_with_features(
        self,
        features: Dict,
        years_ahead: int
    ) -> float:
        """
        Predict price multiplier based on card features
        Returns a growth rate to apply to current price
        """
        
        # Feature-based growth rate calculation
        current_price = features.get('current_price', 100)
        rarity_score = features.get('rarity_score', 5)
        popularity_score = features.get('popularity_score', 50)
        artist_score = features.get('artist_score', 5)
        trend_1y = features.get('trend_1y', 5)
        
        # Base annual growth rate (%)
        base_growth = 5.0
        
        # Adjust based on features
        rarity_boost = (rarity_score / 10) * 3  # Up to 3% boost
        popularity_boost = (popularity_score / 100) * 4  # Up to 4% boost
        artist_boost = (artist_score / 10) * 2  # Up to 2% boost
        trend_boost = min(trend_1y / 10, 5)  # Up to 5% boost
        
        annual_growth_rate = base_growth + rarity_boost + popularity_boost + artist_boost + trend_boost
        
        # Apply compound growth
        growth_multiplier = (1 + annual_growth_rate / 100) ** years_ahead
        predicted_price = current_price * growth_multiplier
        
        return predicted_price
    
    def predict_hybrid(
        self,
        price_history: List[Dict],
        features: Dict,
        years_ahead: int
    ) -> Dict:
        """
        Hybrid prediction combining time series and features
        """
        
        # Time series prediction
        ts_price, ts_lower, ts_upper = self.predict_with_time_series(price_history, years_ahead)
        
        # Feature-based prediction
        feature_price = self.predict_with_features(features, years_ahead)
        
        # Weighted combination (60% time series, 40% features)
        if len(price_history) >= 3:
            final_price = (ts_price * 0.6) + (feature_price * 0.4)
        else:
            # If limited history, rely more on features
            final_price = (ts_price * 0.3) + (feature_price * 0.7)
        
        # Adjust confidence bounds
        lower_bound = min(ts_lower, final_price * 0.75)
        upper_bound = max(ts_upper, final_price * 1.4)
        
        target_date = datetime.now() + timedelta(days=years_ahead * 365)
        
        return {
            "predicted_price": round(final_price, 2),
            "confidence_lower": round(lower_bound, 2),
            "confidence_upper": round(upper_bound, 2),
            "target_date": target_date.isoformat(),
            "years_ahead": years_ahead,
            "model_version": "hybrid_v1",
            "time_series_prediction": round(ts_price, 2),
            "feature_prediction": round(feature_price, 2)
        }
    
    def generate_prediction_timeline(
        self,
        price_history: List[Dict],
        features: Dict,
        max_years: int = 5
    ) -> List[Dict]:
        """Generate predictions for multiple years"""
        
        timeline = []
        
        for year in range(1, max_years + 1):
            prediction = self.predict_hybrid(price_history, features, year)
            timeline.append(prediction)
        
        return timeline

# Create singleton
predictor = PricePredictor()

