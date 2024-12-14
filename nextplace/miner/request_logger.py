import sqlite3
import json
from datetime import datetime, timedelta
import bittensor as bt
from typing import Dict, Any, List

class RequestLogger:
    def __init__(self):
        self.db_path = '/home/ubuntu/Nextplace/requests_log.db'
        self._init_db()
    
    def _get_connection(self):
        try:
            conn = sqlite3.connect(self.db_path, timeout=30, isolation_level=None)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=30000')
            return conn
        except sqlite3.Error as e:
            print(f"資料庫連線錯誤: {e}")
            raise
    
    def _init_db(self):
        """初始化數據庫表"""
        conn = self._get_connection()
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

    def log_request(self, request_data: Dict[str, Any], predictions: List[Dict[str, Any]]) -> int:
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 插入請求記錄
            cursor.execute('''
                INSERT INTO request_logs (
                    hotkey, timestamp, request_type
                ) VALUES (?, ?, ?)
            ''', (
                request_data.get('hotkey'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'prediction'
            ))
            
            request_id = cursor.lastrowid
            
            # 插入原始請求詳情
            for pred in request_data.get('original_predictions', []):
                cursor.execute('''
                    INSERT INTO request_details (
                        request_id, nextplace_id, property_id, listing_id,
                        address, city, state, zip_code, price, beds,
                        baths, sqft, lot_size, year_built, days_on_market,
                        latitude, longitude, property_type, last_sale_date,
                        hoa_dues, query_date, market
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    request_id, pred.get('nextplace_id'), pred.get('property_id'),
                    pred.get('listing_id'), pred.get('address'), pred.get('city'),
                    pred.get('state'), pred.get('zip_code'), pred.get('price'),
                    pred.get('beds'), pred.get('baths'), pred.get('sqft'),
                    pred.get('lot_size'), pred.get('year_built'),
                    pred.get('days_on_market'), pred.get('latitude'),
                    pred.get('longitude'), pred.get('property_type'),
                    pred.get('last_sale_date'), pred.get('hoa_dues'),
                    pred.get('query_date'), pred.get('market')
                ))
            
            # 插入預測詳情
            for pred in predictions:
                cursor.execute('''
                    INSERT INTO prediction_details (
                        request_id, nextplace_id, predicted_sale_price,
                        predicted_sale_date, market
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    request_id,
                    str(pred.get('nextplace_id')),
                    float(pred.get('predicted_sale_price', 0)),
                    pred.get('predicted_sale_date'),
                    pred.get('market')
                ))
            
            conn.commit()
            return request_id
        
        except Exception as e:
            print(f"記錄請求錯誤: {e}")
            if conn:
                conn.rollback()
            return -1
        finally:
            if conn:
                conn.close()

    def log_response(self, request_id: int, response_data: str, processing_time: float):
        """記錄響應到數據庫"""
        conn = self._get_connection()
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
        conn = self._get_connection()
        cursor = conn.cursor()
        
        stats = {
            'total_requests': 0,
            'avg_processing_time': 0,
            'requests_by_validator': {},
            'predictions_by_market': {}
        }
        
        # 實現統計查詢...
        
        return stats