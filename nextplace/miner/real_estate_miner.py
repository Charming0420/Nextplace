import bittensor as bt
from template.base.miner import BaseMinerNeuron
from typing import Tuple
from nextplace.protocol import RealEstateSynapse
from nextplace.miner.ml.base_model import BaseModel as Model
from nextplace.miner.ml.model_loader import ModelArgs
from nextplace.miner.request_logger import RequestLogger
from datetime import datetime
import json
import time


class RealEstateMiner(BaseMinerNeuron):

    def __init__(self, model_args: ModelArgs, force_update_past_predictions: bool, config=None):
        super(RealEstateMiner, self).__init__(config=config)
        self.logger = RequestLogger()
        if force_update_past_predictions:
            bt.logging.trace("🦬 強制更新過去的預測")
        self.model = Model(model_args)
        self.force_update_past_predictions = force_update_past_predictions
        
    def forward(self, synapse: RealEstateSynapse) -> RealEstateSynapse:
        start_time = datetime.now()
        
        try:
            # 記錄請求
            stake, uid = self.get_validator_stake_and_uid(synapse.dendrite.hotkey)
            
            # 將 synapse 轉換為可序列化的字典 (用於資料庫存儲)
            db_request_data = {
                'hotkey': synapse.dendrite.hotkey,
                'validator_uid': uid,
                'validator_stake': stake,
                'original_predictions': [],
                'predictions': []
            }
            
            # 用於回傳給 Validator 的資料
            validator_response = {
                'hotkey': synapse.dendrite.hotkey,
                'predictions': []
            }
            
            # 首先記錄所有原始資料
            if hasattr(synapse, 'real_estate_predictions') and hasattr(synapse.real_estate_predictions, 'predictions'):
                total_predictions = len(synapse.real_estate_predictions.predictions)
                
                # 先保存所有原始資料
                for pred in synapse.real_estate_predictions.predictions:
                    try:
                        # 存儲原始資料 (用於資料庫)
                        original_pred = {
                            'nextplace_id': getattr(pred, 'nextplace_id', None),
                            'property_id': getattr(pred, 'property_id', None),
                            'listing_id': getattr(pred, 'listing_id', None),
                            'address': getattr(pred, 'address', None),
                            'city': getattr(pred, 'city', None),
                            'state': getattr(pred, 'state', None),
                            'zip_code': getattr(pred, 'zip_code', None),
                            'price': getattr(pred, 'price', None),
                            'beds': getattr(pred, 'beds', None),
                            'baths': getattr(pred, 'baths', None),
                            'sqft': getattr(pred, 'sqft', None),
                            'lot_size': getattr(pred, 'lot_size', None),
                            'year_built': getattr(pred, 'year_built', None),
                            'days_on_market': getattr(pred, 'days_on_market', None),
                            'latitude': getattr(pred, 'latitude', None),
                            'longitude': getattr(pred, 'longitude', None),
                            'property_type': getattr(pred, 'property_type', None),
                            'last_sale_date': getattr(pred, 'last_sale_date', None),
                            'hoa_dues': getattr(pred, 'hoa_dues', None),
                            'query_date': getattr(pred, 'query_date', None),
                            'market': getattr(pred, 'market', None)
                        }
                        db_request_data['original_predictions'].append(original_pred)
                    except Exception:
                        bt.logging.error("記錄原始資料時發生錯誤")
                
            # 執行預測
            self.model.run_inference(synapse)
            
            # 記錄預測結果
            if hasattr(synapse, 'real_estate_predictions') and hasattr(synapse.real_estate_predictions, 'predictions'):
                successful_predictions = 0
                for pred in synapse.real_estate_predictions.predictions:
                    if hasattr(pred, 'predicted_sale_price') and pred.predicted_sale_price is not None:
                        # 存儲預測結果
                        prediction_result = {
                            'nextplace_id': str(pred.nextplace_id),
                            'predicted_sale_price': float(pred.predicted_sale_price),
                            'predicted_sale_date': str(pred.predicted_sale_date),
                            'market': str(pred.market),
                            'force_update_past_predictions': bool(pred.force_update_past_predictions)
                        }
                        db_request_data['predictions'].append(prediction_result)
                        validator_response['predictions'].append(prediction_result)
                        successful_predictions += 1
            
            # 計算處理時間
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 記錄到資料庫
            request_id = self.logger.log_request(
                request_data={
                    'hotkey': synapse.dendrite.hotkey,
                    'validator_uid': uid,
                    'validator_stake': stake,
                    'original_predictions': db_request_data['original_predictions']
                },
                predictions=db_request_data['predictions']
            )
            
            # 記錄回應
            self.logger.log_response(
                request_id=request_id,
                response_data=json.dumps(validator_response),
                processing_time=processing_time
            )
            
            # 輸出處理結果統計
            bt.logging.info(f"📊 預測統計：總請求={total_predictions}，成功={successful_predictions}，耗時={processing_time:.2f}秒")
            
            return synapse
            
        except Exception as e:
            bt.logging.error(f"❌ 處理請求時發生錯誤: {str(e)}")
            return synapse

    def _set_force_update_prediction_flag(self, synapse: RealEstateSynapse):
        for prediction in synapse.real_estate_predictions.predictions:
            prediction.force_update_past_predictions = self.force_update_past_predictions

    def blacklist(self, synapse: RealEstateSynapse) -> Tuple[bool, str]:
        # Check if synapse hotkey is in the metagraph
        if synapse.dendrite.hotkey not in self.metagraph.hotkeys:
            return True, f"❌ 未知的 hotkey: {synapse.dendrite.hotkey}"

        stake, uid = self.get_validator_stake_and_uid(synapse.dendrite.hotkey)

        # Check if validator has sufficient stake
        validator_min_stake = 0.0
        if stake < validator_min_stake:
            return True, f"❌ 驗證者 {synapse.dendrite.hotkey} 質押不足: {stake}"

        return False, f"✅ 已接受 hotkey: {synapse.dendrite.hotkey}"

    def priority(self, synapse: RealEstateSynapse) -> float:
        stake, uid = self.get_validator_stake_and_uid(synapse.dendrite.hotkey)
        return stake

    def get_validator_stake_and_uid(self, hotkey):
        uid = self.metagraph.hotkeys.index(hotkey)
        return float(self.metagraph.S[uid]), uid
