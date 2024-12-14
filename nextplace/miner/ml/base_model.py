from abc import ABC, abstractmethod
from nextplace.protocol import RealEstateSynapse
from nextplace.miner.ml.model_loader import ModelArgs
from nextplace.miner.ml.strategies.custom import CustomStrategy

class BaseModel:
    def __init__(self, model_args: ModelArgs):
        self.model_args = model_args
        self.strategy = CustomStrategy()
    
    def run_inference(self, synapse: RealEstateSynapse) -> None:
        for prediction in synapse.real_estate_predictions.predictions:
            try:
                if not self._validate_prediction(prediction):
                    continue
                    
                # 使用策略進行預測
                price, date = self.strategy.predict(prediction.__dict__)
                
                # 設置預測結果
                prediction.predicted_sale_price = price
                prediction.predicted_sale_date = date
                prediction.market = str(prediction.market)
                prediction.nextplace_id = str(prediction.nextplace_id)
                
            except Exception as e:
                continue
                
    def _validate_prediction(self, prediction) -> bool:
        required_fields = ['price', 'query_date', 'market', 'nextplace_id']
        return all(hasattr(prediction, field) for field in required_fields)
