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
        total_predictions = len(synapse.real_estate_predictions.predictions)
        bt.logging.info(f"收到 {total_predictions} 個預測請求")
        
        valid_predictions = []
        error_count = 0
        
        for prediction in synapse.real_estate_predictions.predictions:
            try:
                # 驗證必要欄位
                if not self._validate_prediction(prediction):
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
                
            except Exception as e:
                error_count += 1
                continue
        
        # 更新預測列表，只保留有效預測
        synapse.real_estate_predictions.predictions = valid_predictions
        
        # 輸出批次處理統計
        bt.logging.info(f"預測處理完成:")
        bt.logging.info(f"- 總請求數: {total_predictions}")
        bt.logging.info(f"- 成功預測: {len(valid_predictions)}")
        bt.logging.info(f"- 不符合條件: {total_predictions - len(valid_predictions) - error_count}")
        if error_count > 0:
            bt.logging.info(f"- 處理錯誤: {error_count}")
    
    def _validate_prediction(self, prediction) -> bool:
        """
        驗證預測請求的必要欄位
        """
        required_fields = ['price', 'query_date', 'market', 'nextplace_id', 'property_type', 'sqft', 'year_built']
        
        try:
            for field in required_fields:
                # 檢查欄位是否存在
                if not hasattr(prediction, field):
                    return False
                
                # 檢查欄位值是否為 None
                value = getattr(prediction, field)
                if value is None:
                    return False
                
                # 特別處理數值型欄位
                if field in ['price', 'sqft']:
                    try:
                        float_value = float(value)
                        if float_value <= 0:
                            return False
                    except (ValueError, TypeError):
                        return False
                
                # 特別處理年份欄位
                if field == 'year_built':
                    try:
                        year = int(value)
                        if year <= 0:
                            return False
                    except (ValueError, TypeError):
                        return False
            
            return True
            
        except Exception:
            return False
