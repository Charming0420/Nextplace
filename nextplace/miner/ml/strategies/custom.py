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
            nextplace_id = input_data.get('nextplace_id', 'unknown')
            bt.logging.debug(f"開始處理房產 {nextplace_id} 的預測請求")
            
            # 檢查是否符合預測條件
            should_predict = self._should_predict(input_data)
            if not should_predict:
                bt.logging.info(f"房產 {nextplace_id} 不符合任何預測條件，跳過預測")
                return None, None
            
            # 符合條件時進行預測
            return self._make_prediction(input_data)
            
        except Exception as e:
            bt.logging.error(f"預測過程發生錯誤: {str(e)}")
            return None, None
    
    def _should_predict(self, data: Dict[str, Any]) -> bool:
        """
        檢查是否符合預測條件
        """
        try:
            nextplace_id = data.get('nextplace_id', 'unknown')
            market = str(data.get('market', '')).strip()
            
            # 檢查數值型資料
            try:
                sqft = float(data.get('sqft', 0))
                year_built = int(data.get('year_built', 0))
            except (ValueError, TypeError) as e:
                bt.logging.error(f"房產 {nextplace_id} 的數值轉換錯誤: {str(e)}")
                return False
            
            bt.logging.debug(f"檢查房產 {nextplace_id} 的條件:")
            bt.logging.debug(f"市場: {market}")
            bt.logging.debug(f"面積: {sqft}")
            bt.logging.debug(f"建造年份: {year_built}")
            
            # 條件1：檢查市場是否在最佳市場列表中
            in_nice_market = market in self.nice_market_list
            if in_nice_market:
                bt.logging.info(f"房產 {nextplace_id} 符合條件1: 市場 {market} 在最佳市場列表中")
                return True
            else:
                bt.logging.debug(f"房產 {nextplace_id} 不符合條件1: 市場 {market} 不在最佳市場列表中")
            
            # 條件2：檢查面積範圍
            valid_sqft = 100 <= sqft <= 2000
            if valid_sqft:
                bt.logging.info(f"房產 {nextplace_id} 符合條件2: 面積 {sqft} 在範圍內")
                return True
            else:
                bt.logging.debug(f"房產 {nextplace_id} 不符合條件2: 面積 {sqft} 不在範圍內")
            
            # 條件3：檢查建造年份
            valid_year = 2010 <= year_built <= 2024
            if valid_year:
                bt.logging.info(f"房產 {nextplace_id} 符合條件3: 建造年份 {year_built} 在範圍內")
                return True
            else:
                bt.logging.debug(f"房產 {nextplace_id} 不符合條件3: 建造年份 {year_built} 不在範圍內")
            
            bt.logging.info(f"房產 {nextplace_id} 不符合任何預測條件")
            return False
            
        except Exception as e:
            bt.logging.error(f"檢查預測條件時發生錯誤: {str(e)}")
            return False
    
    def _make_prediction(self, data: Dict[str, Any]) -> Tuple[float, str]:
        """
        生成預測結果
        """
        try:
            nextplace_id = data.get('nextplace_id', 'unknown')
            
            # 使用 listing price 作為預測價格
            try:
                price = float(data.get('price', 0))
                if price <= 0:
                    bt.logging.error(f"房產 {nextplace_id} 的價格無效: {price}")
                    return None, None
                bt.logging.debug(f"房產 {nextplace_id} 的價格: {price}")
            except (ValueError, TypeError) as e:
                bt.logging.error(f"房產 {nextplace_id} 的價格轉換錯誤: {str(e)}")
                return None, None
            
            # 設定預測日期（當前日期+2天）
            predicted_date = datetime.now() + timedelta(days=2)
            predicted_date_str = predicted_date.strftime("%Y-%m-%d")
            
            bt.logging.info(f"生成預測結果: 房產={nextplace_id}, 價格={price}, 日期={predicted_date_str}")
            return price, predicted_date_str
            
        except Exception as e:
            bt.logging.error(f"生成預測結果時發生錯誤: {str(e)}")
            return None, None