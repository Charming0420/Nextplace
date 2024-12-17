import bittensor as bt
from template.base.miner import BaseMinerNeuron
from typing import Tuple
from nextplace.protocol import RealEstateSynapse
from nextplace.miner.ml.base_model import BaseModel as Model
from nextplace.miner.ml.model_loader import ModelArgs
from nextplace.miner.request_logger import RequestLogger
from datetime import datetime
import json


class RealEstateMiner(BaseMinerNeuron):

    def __init__(self, model_args: ModelArgs, force_update_past_predictions: bool, config=None):
        super(RealEstateMiner, self).__init__(config=config)  # call superclass constructor
        self.logger = RequestLogger()  # Initialize the logger
        if force_update_past_predictions:
            bt.logging.trace("🦬 Forcing update of past predictions")
        else:
            bt.logging.trace("🐨 Not forcing update of past predictions")
        self.model = Model(model_args)
        self.force_update_past_predictions = force_update_past_predictions
        
        # 設置詳細的日誌級別
        bt.logging.info("🔄 初始化 RealEstateMiner，設置詳細日誌")
        
    # OVERRIDE | Required
    def forward(self, synapse: RealEstateSynapse) -> RealEstateSynapse:
        start_time = datetime.now()
        
        # 記錄請求
        stake, uid = self.get_validator_stake_and_uid(synapse.dendrite.hotkey)
        
        # 將 synapse 轉換為可序列化的字典 (用於資料庫存儲)
        db_request_data = {
            'hotkey': synapse.dendrite.hotkey,
            'validator_uid': uid,
            'validator_stake': stake,
            'original_predictions': [],  # 用於存儲原始資料
            'predictions': []  # 用於存儲預測結果
        }
        
        # 用於回傳給 Validator 的資料
        validator_response = {
            'hotkey': synapse.dendrite.hotkey,
            'predictions': []
        }
        
        # 首先記錄所有原始資料
        if hasattr(synapse, 'real_estate_predictions') and hasattr(synapse.real_estate_predictions, 'predictions'):
            bt.logging.debug(f"收到 {len(synapse.real_estate_predictions.predictions)} 個原始預測請求")
            
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
                    bt.logging.debug(f"記錄原始資料: ID={original_pred['nextplace_id']}, Market={original_pred['market']}")
                except Exception as e:
                    bt.logging.error(f"記錄原始資料時發生錯誤: {str(e)}")
        
        # 執行預測
        self.model.run_inference(synapse)
        
        # 添加預測結果日誌
        for pred in synapse.real_estate_predictions.predictions:
            bt.logging.debug(f"預測結果: ID={pred.nextplace_id}, 價格={pred.predicted_sale_price}, 日期={pred.predicted_sale_date}")
            
            # 只有成功預測的結果才加入回應
            if hasattr(pred, 'predicted_sale_price') and pred.predicted_sale_price is not None:
                # 存儲預測結果 (用於資料庫)
                pred_dict = {
                    'nextplace_id': pred.nextplace_id,
                    'predicted_sale_price': pred.predicted_sale_price,
                    'predicted_sale_date': pred.predicted_sale_date,
                    'market': pred.market,
                    'force_update_past_predictions': True
                }
                db_request_data['predictions'].append(pred_dict)
                
                # 存儲給 Validator 的回應
                validator_pred = {
                    'nextplace_id': pred.nextplace_id,
                    'predicted_sale_price': pred.predicted_sale_price,
                    'predicted_sale_date': pred.predicted_sale_date,
                    'market': pred.market,
                    'force_update_past_predictions': True
                }
                validator_response['predictions'].append(validator_pred)
        
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
        
        return synapse

    def _set_force_update_prediction_flag(self, synapse: RealEstateSynapse):
        for prediction in synapse.real_estate_predictions.predictions:
            prediction.force_update_past_predictions = self.force_update_past_predictions

    # OVERRIDE | Required
    def blacklist(self, synapse: RealEstateSynapse) -> Tuple[bool, str]:

        # Check if synapse hotkey is in the metagraph
        if synapse.dendrite.hotkey not in self.metagraph.hotkeys:
            bt.logging.info(f"❗Blacklisted unknown hotkey: {synapse.dendrite.hotkey}")
            return True, f"❗Hotkey {synapse.dendrite.hotkey} was not found from metagraph.hotkeys",

        stake, uid = self.get_validator_stake_and_uid(synapse.dendrite.hotkey)

        # Check if validator has sufficient stake
        validator_min_stake = 0.0
        if stake < validator_min_stake:
            bt.logging.info(f"❗Blacklisted validator {synapse.dendrite.hotkey} with insufficient stake: {stake}")
            return True, f"❗Hotkey {synapse.dendrite.hotkey} has insufficient stake: {stake}",

        # Valid hotkey
        bt.logging.info(f"✅ Accepted hotkey: {synapse.dendrite.hotkey} (UID: {uid} - Stake: {stake})")
        return False, f"✅ Accepted hotkey: {synapse.dendrite.hotkey}"

    # OVERRIDE | Required
    def priority(self, synapse: RealEstateSynapse) -> float:
        bt.logging.debug(f"🧮 Calculating priority for synapse from {synapse.dendrite.hotkey}")
        stake, uid = self.get_validator_stake_and_uid(synapse.dendrite.hotkey)
        bt.logging.debug(f"🏆 Prioritized: {synapse.dendrite.hotkey} (UID: {uid} - Stake: {stake})")
        return stake

    # HELPER
    def get_validator_stake_and_uid(self, hotkey):
        uid = self.metagraph.hotkeys.index(hotkey)  # get uid
        return float(self.metagraph.S[uid]), uid  # return validator stake
