from nextplace.protocol import RealEstateSynapse
from nextplace.miner.ml.model_loader import ModelArgs
from datetime import datetime, timedelta

'''
This class facilitates running inference on data from a synapse using a model specified by the user
'''


class Model:

    def __init__(self, model_args: ModelArgs):
        self.model_args = model_args

    def run_inference(self, synapse: RealEstateSynapse) -> None:
        for prediction in synapse.real_estate_predictions.predictions:
            try:
                # 價格轉換
                if hasattr(prediction, 'price') and prediction.price is not None:
                    prediction.predicted_sale_price = float(prediction.price)
                else:
                    continue

                # 日期處理
                if hasattr(prediction, 'query_date') and prediction.query_date:
                    try:
                        query_date = datetime.strptime(prediction.query_date, "%Y-%m-%dT%H:%M:%SZ")
                        predicted_date = query_date + timedelta(days=30)
                        prediction.predicted_sale_date = predicted_date.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
                else:
                    continue

                # 市場驗證
                if not hasattr(prediction, 'market') or not prediction.market:
                    continue
                prediction.market = str(prediction.market)

                # 確保 nextplace_id 存在
                if not hasattr(prediction, 'nextplace_id') or not prediction.nextplace_id:
                    continue
                prediction.nextplace_id = str(prediction.nextplace_id)

            except (ValueError, TypeError):
                continue
