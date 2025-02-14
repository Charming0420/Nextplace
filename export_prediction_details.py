import sqlite3
import pandas as pd
from datetime import datetime

# 資料庫連接
DB_PATH = '/home/ubuntu/Nextplace/requests_log.db'

def export_prediction_details():
    try:
        # 建立資料庫連接
        conn = sqlite3.connect(DB_PATH)
        
        # 使用 SQL 查詢讀取整個表格
        query = "SELECT * FROM prediction_details"
        
        # 使用 pandas 讀取 SQL 查詢結果
        df = pd.read_sql_query(query, conn)
        
        # 生成包含時間戳的檔案名稱
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'prediction_details_{timestamp}.csv'
        
        # 導出為 CSV 檔案
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        
        print(f'資料已成功導出至: {output_filename}')
        
    except Exception as e:
        print(f'導出過程中發生錯誤: {str(e)}')
    
    finally:
        # 關閉資料庫連接
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    export_prediction_details() 