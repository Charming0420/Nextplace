import sqlite3

def cleanup_db_connections():
    try:
        # 連接到資料庫
        conn = sqlite3.connect('/home/ubuntu/Nextplace/requests_log.db')
        cursor = conn.cursor()
        
        # 查看當前連線
        cursor.execute("PRAGMA database_list")
        databases = cursor.fetchall()
        
        for db in databases:
            # 關閉所有連線
            cursor.execute("PRAGMA wal_checkpoint(FULL)")
            
        # 強制清理
        cursor.execute("VACUUM")
        
    except Exception as e:
        print(f"清理資料庫錯誤: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    cleanup_db_connections()