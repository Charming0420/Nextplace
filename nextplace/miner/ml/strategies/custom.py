import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from .base import BaseStrategy

class MarketTracker:
    def __init__(self, file_path='market_tracker.json'):
        self.file_path = os.path.join('/home/ubuntu/Nextplace', file_path)
        self.init_file()
    
    def init_file(self):
        if not os.path.exists(self.file_path):
            self._save_data({'predictions': {}})
    
    def _load_data(self) -> Dict:
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {'predictions': {}}
    
    def _save_data(self, data: Dict):
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def record_prediction(self, market: str):
        data = self._load_data()
        today = datetime.now().strftime('%Y-%m-%d')
        
        if market not in data['predictions']:
            data['predictions'][market] = []
        
        data['predictions'][market].append(today)
        self._save_data(data)
    
    def should_predict(self, market: str) -> bool:
        data = self._load_data()
        if market not in data['predictions']:
            return True
        
        five_days_ago = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
        recent_predictions = [
            date for date in data['predictions'][market]
            if date >= five_days_ago
        ]
        
        return len(recent_predictions) == 0

class CustomStrategy(BaseStrategy):
    def __init__(self):
        # 定義最準確的市場列表（根據樣本數、變異率和標準差綜合評分）
        self.accurate_markets = [
            # 樣本數>100，變異率<2%，標準差<4%的市場
            'Bismarck',   # 樣本:112, 變異:-0.68%, 標準差:1.79%
            'Cheyenne',   # 樣本:159, 變異:-0.81%, 標準差:2.07%
            'Meridian',   # 樣本:274, 變異:-0.95%, 標準差:1.94%
            'Billings',   # 樣本:146, 變異:-1.19%, 標準差:3.27%
            'Nampa',      # 樣本:247, 變異:-1.32%, 標準差:3.24%
            'Baton Rouge',# 樣本:320, 變異:-1.22%, 標準差:3.54%
            'Plano',      # 樣本:214, 變異:-1.51%, 標準差:2.91%
            'Houston',    # 樣本:2546, 變異:-1.47%, 標準差:3.51%
            'Caldwell',   # 樣本:146, 變異:-1.51%, 標準差:3.48%
            'Corpus Christi', # 樣本:314, 變異:-1.64%, 標準差:3.98%
            'Boise',      # 樣本:370, 變異:-1.47%, 標準差:4.07%
            'St. Louis',  # 樣本:723, 變異:-1.88%, 標準差:4.56%
            'Summerville',# 樣本:332, 變異:-1.54%, 標準差:4.20%
            'Dallas',     # 樣本:1111, 變異:-1.97%, 標準差:3.96%
            'Fort Worth', # 樣本:1114, 變異:-1.95%, 標準差:3.66%
        ]
        self.market_tracker = MarketTracker()
    
    def predict(self, input_data: Dict[str, Any]) -> Tuple[float, str]:
        market = input_data.get('market')
        property_type = str(input_data.get('property_type', ''))
        sqft = float(input_data.get('sqft', 0))
        year_built = int(input_data.get('year_built', 0))
        base_price = float(input_data.get('price', 0))
        
        # 檢查是否需要為了覆蓋率而預測
        if self.market_tracker.should_predict(market):
            self.market_tracker.record_prediction(market)
            return self._make_prediction(input_data)
        
        # 檢查是否符合任一預測條件
        if self._should_predict(input_data):
            return self._make_prediction(input_data)
        
        return None, None
    
    def _should_predict(self, data: Dict[str, Any]) -> bool:
        market = data.get('market')
        property_type = str(data.get('property_type', ''))
        sqft = float(data.get('sqft', 0))
        year_built = int(data.get('year_built', 0))
        
        # 條件1：市場條件
        if market in self.accurate_markets:
            return True
        
        # 條件2：物業類型條件
        if property_type in ['1', '6']:  # Single Family Residential 或 House
            return True
        
        # 條件3：面積條件
        if 100 <= sqft <= 2000:
            return True
        
        # 條件4：建造年份條件
        if 2010 <= year_built <= 2024:
            return True
        
        return False
    
    def _make_prediction(self, data: Dict[str, Any]) -> Tuple[float, str]:
        base_price = float(data.get('price', 0))
        query_date = datetime.strptime(data['query_date'], "%Y-%m-%dT%H:%M:%SZ")
        predicted_date = query_date + timedelta(days=30)
        
        return base_price, predicted_date.strftime("%Y-%m-%d")