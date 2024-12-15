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
        # 根據樣本數、變異率和標準差的綜合評分選擇市場
        # 條件：樣本數 >= 100，abs_mean < 2%，std < 4%
        self.accurate_markets = {
            'Bismarck': {'count': 112, 'variance': -0.68, 'std': 1.79},
            'Cheyenne': {'count': 159, 'variance': -0.81, 'std': 2.07},
            'Meridian': {'count': 274, 'variance': -0.95, 'std': 1.94},
            'Billings': {'count': 146, 'variance': -1.19, 'std': 3.27},
            'Nampa': {'count': 247, 'variance': -1.32, 'std': 3.24},
            'Baton Rouge': {'count': 320, 'variance': -1.22, 'std': 3.54},
            'Plano': {'count': 214, 'variance': -1.51, 'std': 2.91},
            'Houston': {'count': 2546, 'variance': -1.47, 'std': 3.51},
            'Caldwell': {'count': 146, 'variance': -1.51, 'std': 3.48}
        }
        self.market_tracker = MarketTracker()
    
    def predict(self, input_data: Dict[str, Any]) -> Tuple[float, str]:
        market = input_data.get('market')
        
        # 檢查是否需要為了覆蓋率而預測
        if self.market_tracker.should_predict(market):
            self.market_tracker.record_prediction(market)
            prediction = self._make_prediction(input_data)
            if prediction[0] is not None:
                input_data['force_update_past_predictions'] = True
            return prediction
        
        # 檢查是否符合預測條件
        if self._should_predict(input_data):
            input_data['force_update_past_predictions'] = True
            return self._make_prediction(input_data)
        
        return None, None
    
    def _should_predict(self, data: Dict[str, Any]) -> bool:
        market = data.get('market')
        property_type = str(data.get('property_type', ''))
        sqft = float(data.get('sqft', 0))
        year_built = int(data.get('year_built', 0))
        
        # 市場評分系統
        if market in self.accurate_markets:
            market_data = self.accurate_markets[market]
            # 根據樣本數、變異率和標準差計算綜合分數
            sample_score = min(1.0, market_data['count'] / 1000)  # 樣本數評分
            variance_score = 1.0 - abs(market_data['variance']) / 2.0  # 變異率評分
            std_score = 1.0 - market_data['std'] / 4.0  # 標準差評分
            
            # 綜合評分 (加權平均)
            total_score = (sample_score * 0.3 + variance_score * 0.4 + std_score * 0.3)
            
            # 只有當綜合評分超過閾值時才預測
            if total_score >= 0.7:
                return True
        
        # 其他條件保持不變
        if property_type in ['1', '6']:
            return True
        
        if 100 <= sqft <= 2000:
            return True
        
        if 2010 <= year_built <= 2024:
            return True
        
        return False
    
    def _make_prediction(self, data: Dict[str, Any]) -> Tuple[float, str]:
        base_price = float(data.get('price', 0))
        query_date = datetime.now()  # 使用當前時間
        predicted_date = query_date + timedelta(days=2)  # 預測兩天後
        
        return base_price, predicted_date.strftime("%Y-%m-%d")