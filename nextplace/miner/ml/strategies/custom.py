import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple

# class MarketTracker:
#     def __init__(self, file_path='market_tracker.json'):
#         self.file_path = os.path.join('/home/ubuntu/Nextplace', file_path)
#         self.init_file()
    
#     def init_file(self):
#         if not os.path.exists(self.file_path):
#             self._save_data({'predictions': {}})
    
#     def _load_data(self) -> Dict:
#         try:
#             with open(self.file_path, 'r') as f:
#                 return json.load(f)
#         except (FileNotFoundError, json.JSONDecodeError):
#             return {'predictions': {}}
    
#     def _save_data(self, data: Dict):
#         with open(self.file_path, 'w') as f:
#             json.dump(data, f, indent=2)
    
#     def record_prediction(self, market: str):ㄋ
#         data = self._load_data()
#         today = datetime.now().strftime('%Y-%m-%d')
        
#         if market not in data['predictions']:
#             data['predictions'][market] = []
        
#         data['predictions'][market].append(today)
#         self._save_data(data)
    
#     def should_predict(self, market: str) -> bool:
#         data = self._load_data()
#         if market not in data['predictions']:
#             return True
        
#         five_days_ago = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d')
#         recent_predictions = [
#             date for date in data['predictions'][market]
#             if date >= five_days_ago
#         ]
        
#         return len(recent_predictions) == 0

class CustomStrategy:
    def __init__(self):
        # 根據樣本數、變異率和標準差選出的前20個最佳市場
        self.nice_market_list = {
            'Bismarck': {'count': 112, 'abs_mean': 0.68, 'std': 1.79},
            'Cheyenne': {'count': 159, 'abs_mean': 0.81, 'std': 2.07},
            'Meridian': {'count': 274, 'abs_mean': 0.95, 'std': 1.94},
            'Billings': {'count': 146, 'abs_mean': 1.19, 'std': 3.27},
            'Nampa': {'count': 247, 'abs_mean': 1.32, 'std': 3.24},
            'Baton Rouge': {'count': 320, 'abs_mean': 1.22, 'std': 3.54},
            'Plano': {'count': 214, 'abs_mean': 1.51, 'std': 2.91},
            'Houston': {'count': 2546, 'abs_mean': 1.47, 'std': 3.51},
            'Caldwell': {'count': 146, 'abs_mean': 1.51, 'std': 3.48},
            'Fort Worth': {'count': 892, 'abs_mean': 1.62, 'std': 3.12},
            'Dallas': {'count': 1245, 'abs_mean': 1.58, 'std': 3.24},
            'Austin': {'count': 1102, 'abs_mean': 1.64, 'std': 3.18},
            'San Antonio': {'count': 986, 'abs_mean': 1.71, 'std': 3.32},
            'Oklahoma City': {'count': 742, 'abs_mean': 1.68, 'std': 3.28},
            'Tulsa': {'count': 584, 'abs_mean': 1.72, 'std': 3.35},
            'Little Rock': {'count': 428, 'abs_mean': 1.75, 'std': 3.42},
            'Memphis': {'count': 652, 'abs_mean': 1.78, 'std': 3.45},
            'Nashville': {'count': 884, 'abs_mean': 1.82, 'std': 3.48},
            'Birmingham': {'count': 524, 'abs_mean': 1.85, 'std': 3.52},
            'Jackson': {'count': 386, 'abs_mean': 1.88, 'std': 3.56}
        }
        # self.market_tracker = MarketTracker()
    
    def predict(self, input_data: Dict[str, Any]) -> Tuple[float, str]:
        # # 檢查是否需要為了覆蓋率而預測
        # market = input_data.get('market')
        # if self.market_tracker.should_predict(market):
        #     self.market_tracker.record_prediction(market)
        #     prediction = self._make_prediction(input_data)
        #     if prediction[0] is not None:
        #         input_data['force_update_past_predictions'] = True
        #     return prediction
        
        # 檢查是否符合預測條件
        if self._should_predict(input_data):
            input_data['force_update_past_predictions'] = True
            return self._make_prediction(input_data)
        
        return None, None
    
    def _should_predict(self, data: Dict[str, Any]) -> bool:
        """
        檢查是否符合預測條件
        """
        market = data.get('market')
        property_type = str(data.get('property_type', ''))
        sqft = float(data.get('sqft', 0))
        year_built = int(data.get('year_built', 0))
        
        # 條件1：檢查市場是否在最佳市場列表中
        if market in self.nice_market_list:
            return True
        
        # 條件2：檢查房產類型
        if property_type in ['1', '6']:
            return True
        
        # 條件3：檢查面積範圍
        if 100 <= sqft <= 2000:
            return True
        
        # 條件4：檢查建造年份
        if 2010 <= year_built <= 2024:
            return True
        
        return False
    
    def _make_prediction(self, data: Dict[str, Any]) -> Tuple[float, str]:
        """
        生成預測結果
        """
        try:
            base_price = float(data.get('price', 0))
            predicted_date = datetime.now() + timedelta(days=2)
            
            return base_price, predicted_date.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            return None, None