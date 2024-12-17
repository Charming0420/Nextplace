from abc import ABC, abstractmethod
from nextplace.protocol import RealEstateSynapse
from nextplace.miner.ml.model_loader import ModelArgs
from nextplace.miner.ml.strategies.custom import CustomStrategy
import bittensor as bt

class BaseModel:
    def __init__(self, model_args: ModelArgs):
        self.model_args = model_args
        self.strategy = CustomStrategy()
    
    def run_inference(self, synapse: RealEstateSynapse) -> None:
        """
        執行預測推理
        """
        bt.logging.debug(f"開始處理 {len(synapse.real_estate_predictions.predictions)} 個預測請求")
        valid_predictions = []
        
        for prediction in synapse.real_estate_predictions.predictions:
            try:
                # 驗證必要欄位
                if not self._validate_prediction(prediction):
                    bt.logging.debug(f"房產 {getattr(prediction, 'nextplace_id', 'unknown')} 缺少必要欄位，跳過")
                    continue
                
                # 使用策略進行預測
                price, date = self.strategy.predict(prediction.__dict__)
                
                # 只保留有效的預測結果
                if price is not None and date is not None:
                    prediction.predicted_sale_price = price
                    prediction.predicted_sale_date = date
                    prediction.market = str(prediction.market)
                    prediction.nextplace_id = str(prediction.nextplace_id)
                    prediction.force_update_past_predictions = True
                    valid_predictions.append(prediction)
                    bt.logging.debug(f"房產 {prediction.nextplace_id} 預測成功: 價格={price}, 日期={date}")
                else:
                    bt.logging.debug(f"房產 {prediction.nextplace_id} 不符合預測條件，跳過")
                
            except Exception as e:
                bt.logging.error(f"處理房產 {getattr(prediction, 'nextplace_id', 'unknown')} 時發生錯誤: {str(e)}")
                continue
        
        # 更新預測列表，只保留有效預測
        synapse.real_estate_predictions.predictions = valid_predictions
        bt.logging.debug(f"預測處理完成，保留 {len(valid_predictions)} 個符合條件的預測")
    
    def _validate_prediction(self, prediction) -> bool:
        """
        驗證預測請求的必要欄位
        """
        required_fields = ['price', 'query_date', 'market', 'nextplace_id', 'property_type', 'sqft', 'year_built']
        
        try:
            for field in required_fields:
                # 檢查欄位是否存在
                if not hasattr(prediction, field):
                    bt.logging.debug(f"房產缺少必要欄位: {field}")
                    return False
                
                # 檢查欄位值是否為 None
                value = getattr(prediction, field)
                if value is None:
                    bt.logging.debug(f"房產欄位 {field} 的值為 None")
                    return False
                
                # 特別處理數值型欄位
                if field in ['price', 'sqft']:
                    try:
                        float_value = float(value)
                        if float_value <= 0:
                            bt.logging.debug(f"房產欄位 {field} 的值必須大於0: {float_value}")
                            return False
                    except (ValueError, TypeError):
                        bt.logging.debug(f"房產欄位 {field} 的值無法轉換為數值: {value}")
                        return False
                
                # 特別處理年份欄位
                if field == 'year_built':
                    try:
                        year = int(value)
                        if year <= 0:
                            bt.logging.debug(f"房產建造年份無效: {year}")
                            return False
                    except (ValueError, TypeError):
                        bt.logging.debug(f"房產建造年份無法轉換為數值: {value}")
                        return False
            
            return True
            
        except Exception as e:
            bt.logging.error(f"驗證預測請求時發生錯誤: {str(e)}")
            return False
