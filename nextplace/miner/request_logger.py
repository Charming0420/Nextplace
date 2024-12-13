import sqlite3
import json
from datetime import datetime, timedelta
import bittensor as bt

class RequestLogger:
    def __init__(self, db_path="/home/ubuntu/Nextplace/requests_log.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化數據庫表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 創建請求日誌主表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS request_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                hotkey TEXT,
                validator_uid INTEGER,
                validator_stake REAL,
                request_type TEXT,
                processing_time REAL,
                response_data TEXT
            )
        ''')
        
        # 創建請求詳情表 (存儲 Validator 傳來的原始房產資料)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS request_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER,
                nextplace_id TEXT,
                property_id TEXT,
                listing_id TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                price REAL,
                beds INTEGER,
                baths INTEGER,
                sqft INTEGER,
                lot_size INTEGER,
                year_built INTEGER,
                days_on_market INTEGER,
                latitude REAL,
                longitude REAL,
                property_type TEXT,
                last_sale_date TEXT,
                hoa_dues REAL,
                query_date TEXT,
                market TEXT,
                FOREIGN KEY (request_id) REFERENCES request_logs(id)
            )
        ''')
        
        # 創建預測詳情表 (存儲發送給 Validator 的預測結果)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prediction_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER,
                nextplace_id TEXT,
                predicted_sale_price REAL,
                predicted_sale_date TEXT,
                market TEXT,
                force_update_past_predictions BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (request_id) REFERENCES request_logs(id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def log_request(self, hotkey: str, request_data: str, validator_uid: int, validator_stake: float):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 解析請求數據
            request_obj = json.loads(request_data)
            predictions = request_obj.get('predictions', [])
            current_time = datetime.now().isoformat()
            
            # 插入主請求記錄
            cursor.execute('''
                INSERT INTO request_logs (
                    timestamp, hotkey, validator_uid, validator_stake, request_type
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                current_time,
                hotkey,
                validator_uid,
                validator_stake,
                'prediction_request'
            ))
            
            request_id = cursor.lastrowid
            
            # 插入原始房產資料到 request_details
            for pred in request_obj.get('original_predictions', []):
                cursor.execute('''
                    INSERT INTO request_details (
                        request_id, nextplace_id, property_id, listing_id,
                        address, city, state, zip_code, price, beds,
                        baths, sqft, lot_size, year_built, days_on_market,
                        latitude, longitude, property_type, last_sale_date,
                        hoa_dues, query_date, market
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    request_id,
                    pred.get('nextplace_id'),
                    pred.get('property_id'),
                    pred.get('listing_id'),
                    pred.get('address'),
                    pred.get('city'),
                    pred.get('state'),
                    pred.get('zip_code'),
                    float(pred.get('price')) if pred.get('price') is not None else None,
                    int(pred.get('beds')) if pred.get('beds') is not None else None,
                    float(pred.get('baths')) if pred.get('baths') is not None else None,
                    int(pred.get('sqft')) if pred.get('sqft') is not None else None,
                    int(pred.get('lot_size')) if pred.get('lot_size') is not None else None,
                    int(pred.get('year_built')) if pred.get('year_built') is not None else None,
                    int(pred.get('days_on_market')) if pred.get('days_on_market') is not None else None,
                    float(pred.get('latitude')) if pred.get('latitude') is not None else None,
                    float(pred.get('longitude')) if pred.get('longitude') is not None else None,
                    pred.get('property_type'),
                    pred.get('last_sale_date'),
                    float(pred.get('hoa_dues')) if pred.get('hoa_dues') is not None else None,
                    pred.get('query_date'),
                    pred.get('market')
                ))
                
                # 插入預測詳情
                for pred in request_obj.get('predictions', []):
                    cursor.execute('''
                        INSERT INTO prediction_details (
                            request_id, nextplace_id, predicted_sale_price,
                            predicted_sale_date, market, force_update_past_predictions
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        request_id,
                        pred['nextplace_id'],  # 直接使用字典索引
                        pred['predicted_sale_price'],  # 直接使用字典索引
                        pred['predicted_sale_date'],  # 直接使用字典索引
                        pred['market'],  # 直接使用字典索引
                        pred.get('force_update_past_predictions', False)
                    ))
            
            conn.commit()
            return request_id
        except Exception as e:
            bt.logging.error(f"Error logging request: {e}")
            raise
        finally:
            conn.close()

    def log_response(self, request_id: int, response_data: str, processing_time: float):
        """記錄響應到數據庫"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE request_logs
            SET response_data = ?, processing_time = ?
            WHERE id = ?
        ''', (response_data, processing_time, request_id))
        
        conn.commit()
        conn.close()

    def get_request_stats(self, days=1):
        """獲取請求統計信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {
            'total_requests': 0,
            'avg_processing_time': 0,
            'requests_by_validator': {},
            'predictions_by_market': {}
        }
        
        # 實現統計查詢...
        
        return stats