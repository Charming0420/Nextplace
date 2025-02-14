import pandas as pd
import numpy as np

class DataProcessor:
    def __init__(self, file_path):
        self.file_path = file_path
        
    def load_data(self):
        """載入CSV數據"""
        try:
            # 使用更穩健的CSV讀取參數
            df = pd.read_csv(
                self.file_path,
                escapechar='\\',  # 處理轉義字符
                quoting=1,        # 使用引號包裹的字段
                encoding='utf-8',  # 指定編碼
                on_bad_lines='skip'  # 跳過有問題的行
            )
            print(f"成功載入數據，共 {len(df)} 行")
            return df
        except Exception as e:
            print(f"載入數據時發生錯誤: {str(e)}")
            # 嘗試使用不同的讀取方式
            try:
                df = pd.read_csv(
                    self.file_path,
                    encoding='utf-8',
                    quoting=3,  # 忽略引號
                    sep=',',    # 明確指定分隔符
                    on_bad_lines='skip'
                )
                print(f"使用替代方法成功載入數據，共 {len(df)} 行")
                return df
            except Exception as e2:
                print(f"替代載入方法也失敗: {str(e2)}")
                raise
    
    def calculate_price_difference(self, df):
        """計算價格差異比例"""
        try:
            df['price_difference_ratio'] = (df['sale_price'] - df['listing_price']) / df['listing_price']
            # 移除極端值
            q1 = df['price_difference_ratio'].quantile(0.01)
            q3 = df['price_difference_ratio'].quantile(0.99)
            df = df[(df['price_difference_ratio'] >= q1) & (df['price_difference_ratio'] <= q3)]
            return df
        except Exception as e:
            print(f"計算價格差異時發生錯誤: {str(e)}")
            raise
    
    def clean_data(self, df):
        """清理數據"""
        try:
            # 顯示初始數據信息
            print(f"清理前的數據行數: {len(df)}")
            
            # 檢查並顯示缺失值信息
            missing_info = df.isnull().sum()
            print("\n缺失值信息:")
            print(missing_info[missing_info > 0])
            
            # 移除空值
            df = df.dropna(subset=['listing_price', 'sale_price'])
            
            # 移除異常值
            df = df[df['listing_price'] > 0]
            df = df[df['sale_price'] > 0]
            
            # 轉換日期格式
            try:
                df['last_sale_date'] = pd.to_datetime(df['last_sale_date'], errors='coerce')
            except Exception as e:
                print(f"日期轉換錯誤: {str(e)}")
                # 如果日期轉換失敗，移除無效的日期
                df = df.dropna(subset=['last_sale_date'])
            
            print(f"清理後的數據行數: {len(df)}")
            return df
            
        except Exception as e:
            print(f"數據清理時發生錯誤: {str(e)}")
            raise
    
    def preprocess_data(self):
        """執行完整的數據預處理流程"""
        print("開始數據預處理...")
        df = self.load_data()
        print("\n開始數據清理...")
        df = self.clean_data(df)
        print("\n開始計算價格差異...")
        df = self.calculate_price_difference(df)
        print("數據預處理完成!")
        return df 