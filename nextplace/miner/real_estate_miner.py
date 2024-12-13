import bittensor as bt
from template.base.miner import BaseMinerNeuron
from typing import Tuple
from nextplace.protocol import RealEstateSynapse
from nextplace.miner.ml.model import Model
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
        
        # 添加這行來查看原始資料
        bt.logging.debug(f"收到的原始資料: {synapse.real_estate_predictions.predictions[0].__dict__}")
        
        # 先執行預測
        self.model.run_inference(synapse)
        self._set_force_update_prediction_flag(synapse)
        
        # 添加預測結果日誌
        for pred in synapse.real_estate_predictions.predictions:
            bt.logging.debug(f"預測結果: ID={pred.nextplace_id}, 價格={pred.predicted_sale_price}, 日期={pred.predicted_sale_date}")
        
        # 記錄請求
        stake, uid = self.get_validator_stake_and_uid(synapse.dendrite.hotkey)
        
        # 將 synapse 轉換為可序列化的字典 (用於資料庫存儲)
        db_request_data = {
            'hotkey': synapse.dendrite.hotkey,
            'original_predictions': [],  # 用於存儲原始資料
            'predictions': []  # 用於存儲預測結果
        }
        
        # 用於回傳給 Validator 的資料
        validator_response = {
            'hotkey': synapse.dendrite.hotkey,
            'predictions': []
        }
        
        if hasattr(synapse, 'real_estate_predictions') and hasattr(synapse.real_estate_predictions, 'predictions'):
            for pred in synapse.real_estate_predictions.predictions:
                # 存儲原始資料 (用於資料庫)
                original_pred = {
                    'nextplace_id': pred.nextplace_id,
                    'property_id': pred.property_id,
                    'listing_id': pred.listing_id,
                    'address': pred.address,
                    'city': pred.city,
                    'state': pred.state,
                    'zip_code': pred.zip_code,
                    'price': pred.price,
                    'beds': pred.beds,
                    'baths': pred.baths,
                    'sqft': pred.sqft,
                    'lot_size': pred.lot_size,
                    'year_built': pred.year_built,
                    'days_on_market': pred.days_on_market,
                    'latitude': pred.latitude,
                    'longitude': pred.longitude,
                    'property_type': pred.property_type,
                    'last_sale_date': pred.last_sale_date,
                    'hoa_dues': pred.hoa_dues,
                    'query_date': pred.query_date,
                    'market': pred.market
                }
                db_request_data['original_predictions'].append(original_pred)
                
                # 存儲預測結果 (用於資料庫)
                pred_dict = {
                    'nextplace_id': pred.nextplace_id,
                    'predicted_sale_price': pred.predicted_sale_price if hasattr(pred, 'predicted_sale_price') else None,
                    'predicted_sale_date': pred.predicted_sale_date if hasattr(pred, 'predicted_sale_date') else None,
                    'market': pred.market,
                    'force_update_past_predictions': getattr(pred, 'force_update_past_predictions', False)
                }
                db_request_data['predictions'].append(pred_dict)
                
                # 存儲給 Validator 的回應
                validator_pred = {
                    'nextplace_id': pred.nextplace_id,
                    'predicted_sale_price': pred.predicted_sale_price,
                    'predicted_sale_date': pred.predicted_sale_date,
                    'market': pred.market,
                    'force_update_past_predictions': getattr(pred, 'force_update_past_predictions', False)
                }
                validator_response['predictions'].append(validator_pred)
        
        # 記錄到資料庫
        request_id = self.logger.log_request(
            hotkey=synapse.dendrite.hotkey,
            request_data=json.dumps(db_request_data),
            validator_uid=uid,
            validator_stake=stake
        )
        
        # 記錄處理時間
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 記錄回應
        self.logger.log_response(
            request_id=request_id,
            response_data=json.dumps(validator_response),
            processing_time=processing_time
        )
        
        # 最終驗證
        valid_predictions = []
        for pred in synapse.real_estate_predictions.predictions:
            if (hasattr(pred, 'nextplace_id') and pred.nextplace_id and
                hasattr(pred, 'predicted_sale_price') and isinstance(pred.predicted_sale_price, float) and
                hasattr(pred, 'predicted_sale_date') and pred.predicted_sale_date and
                hasattr(pred, 'market') and pred.market):
                valid_predictions.append(pred)
        
        synapse.real_estate_predictions.predictions = valid_predictions
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
