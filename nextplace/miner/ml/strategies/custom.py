import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List
import bittensor as bt

class CustomStrategy:
    def __init__(self):
        """
        初始化策略
        
        過去的篩選標準（已停用）：
        1. 特定市場列表篩選
        2. 面積範圍篩選 (100-2000 平方呎)
        3. 建造年份篩選 (2010-2024)
        
        現行篩選標準：
        - 根據預定義的價格區間進行篩選
        """
        self.price_ranges = [
            (930000, 940000), (500000, 510000),
            (550000, 560000), (400000, 410000),
            (750000, 760000), (350000, 360000),
            (800000, 810000), (300000, 310000),
            (410000, 420000), (650000, 660000),
            (480000, 490000), (710000, 720000),
            (360000, 370000), (660000, 670000),
            (760000, 770000), (380000, 390000),
            (600000, 610000), (530000, 540000),
            (910000, 920000), (450000, 460000),
            (860000, 870000), (460000, 470000),
            (510000, 520000), (610000, 620000),
            (630000, 640000), (330000, 340000),
            (440000, 450000), (880000, 890000)
        ]
    
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
        
        目前僅檢查價格是否落在預定義的區間內
        """
        try:
            # 獲取並驗證價格
            try:
                price = float(data.get('price', 0))
                if price <= 0:
                    return False
            except (ValueError, TypeError):
                return False
            
            # 檢查價格是否在任一預定義區間內
            for min_price, max_price in self.price_ranges:
                if min_price < price <= max_price:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _make_prediction(self, data: Dict[str, Any]) -> Tuple[float, str]:
        """
        生成預測結果
        
        價格預測：直接使用輸入價格
        日期預測：當前日期 + 2天
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