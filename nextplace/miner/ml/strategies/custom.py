import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
import bittensor as bt

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
    
    def predict(self, input_data: Dict[str, Any]) -> Tuple[float, str]:
        """
        主要預測函數
        """
        try:
            # 檢查是否符合預測條件
            if not self._should_predict(input_data):
                return None, None
            
            # 符合條件時進行預測
            return self._make_prediction(input_data)
            
        except Exception:
            return None, None
    
    def _should_predict(self, data: Dict[str, Any]) -> bool:
        """
        檢查是否符合預測條件
        """
        try:
            market = str(data.get('market', '')).strip()
            
            # 檢查數值型資料
            try:
                sqft = float(data.get('sqft', 0))
                year_built = int(data.get('year_built', 0))
            except (ValueError, TypeError):
                return False
            
            # 條件1：檢查市場是否在最佳市場列表中
            if market in self.nice_market_list:
                return True
            
            # 條件2：檢查面積範圍
            if 100 <= sqft <= 2000:
                return True
            
            # 條件3：檢查建造年份
            if 2010 <= year_built <= 2024:
                return True
            
            return False
            
        except Exception:
            return False
    
    def _make_prediction(self, data: Dict[str, Any]) -> Tuple[float, str]:
        """
        生成預測結果
        """
        try:
            # 使用 listing price 作為預測價格
            try:
                price = float(data.get('price', 0))
                if price <= 0:
                    return None, None
            except (ValueError, TypeError):
                return None, None
            
            # 設定預測日期（當前日期+2天）
            predicted_date = datetime.now() + timedelta(days=2)
            predicted_date_str = predicted_date.strftime("%Y-%m-%d")
            
            return price, predicted_date_str
            
        except Exception:
            return None, None