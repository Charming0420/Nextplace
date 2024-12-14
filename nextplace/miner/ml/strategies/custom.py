from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from .base import BaseStrategy
import pandas as pd
import sqlite3
import os

class MarketTracker:
    def __init__(self, db_path='market_tracker.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS market_predictions (
                market TEXT,
                prediction_date DATE,
                PRIMARY KEY (market, prediction_date)
            )
        ''')
        conn.commit()
        conn.close()
    
    def record_prediction(self, market: str):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        today = datetime.now().date()
        c.execute('INSERT OR REPLACE INTO market_predictions VALUES (?, ?)', 
                 (market, today))
        conn.commit()
        conn.close()
    
    def should_predict(self, market: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        five_days_ago = (datetime.now() - timedelta(days=5)).date()
        
        c.execute('''
            SELECT COUNT(*) FROM market_predictions 
            WHERE market = ? AND prediction_date > ?
        ''', (market, five_days_ago))
        
        count = c.fetchone()[0]
        conn.close()
        return count == 0

class CustomStrategy(BaseStrategy):
    def __init__(self):
        # 定義最準確的市場列表（前30名）
        self.accurate_markets = [
            'Bismarck', 'Cheyenne', 'Jackson', 'Meridian', 'Billings',
            'Helena', 'Chesterfield', 'Casper', 'Nampa', 'Grand Forks',
            'Baton Rouge', 'Plano', 'Bozeman', 'Houston', 'Southaven',
            'Missoula', 'Caldwell', 'Irving', 'Corpus Christi', 'Boise',
            'Biloxi', 'Garland', 'St. Louis', 'Summerville', 'Dallas',
            'Fort Worth', 'San Antonio', 'Austin', 'El Paso', 'Arlington'
        ]
        self.market_tracker = MarketTracker()
    
    def predict(self, input_data: Dict[str, Any]) -> Tuple[float, str]:
        market = input_data.get('market')
        property_type = str(input_data.get('property_type', ''))
        sqft = float(input_data.get('sqft', 0))
        base_price = float(input_data.get('price', 0))
        
        # 檢查是否需要為了覆蓋率而預測
        if self.market_tracker.should_predict(market):
            self.market_tracker.record_prediction(market)
            return self._make_prediction(input_data)
        
        # 檢查預測條件
        if not self._should_predict(input_data):
            return None, None
        
        return self._make_prediction(input_data)
    
    def _should_predict(self, data: Dict[str, Any]) -> bool:
        market = data.get('market')
        sqft = float(data.get('sqft', 0))
        
        # 檢查市場條件
        if market not in self.accurate_markets:
            return False
        
        # 檢查面積條件
        if not (100 <= sqft <= 2000):
            return False
        
        return True
    
    def _make_prediction(self, data: Dict[str, Any]) -> Tuple[float, str]:
        base_price = float(data.get('price', 0))
        query_date = datetime.strptime(data['query_date'], "%Y-%m-%dT%H:%M:%SZ")
        predicted_date = query_date + timedelta(days=30)
        
        return base_price, predicted_date.strftime("%Y-%m-%d")