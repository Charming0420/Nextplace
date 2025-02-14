import pandas as pd
from data_processor import DataProcessor
from analyzer import PropertyAnalyzer
from visualizer import DataVisualizer
from utils import create_bins

def create_sqft_bins(df):
    """創建以200 sqft為單位的區間"""
    min_sqft = (df['sqft'].min() // 200) * 200  # 向下取整到最近的200
    max_sqft = ((df['sqft'].max() // 200) + 1) * 200  # 向上取整到最近的200
    return pd.interval_range(start=min_sqft, end=max_sqft, freq=200)

def create_year_bins(df):
    """創建以5年為單位的區間"""
    min_year = (df['year_built'].min() // 5) * 5  # 向下取整到最近的5年
    max_year = ((df['year_built'].max() // 5) + 1) * 5  # 向上取整到最近的5年
    return pd.interval_range(start=min_year, end=max_year, freq=5)

def create_price_bins(df):
    """創建以10000美元為單位的區間"""
    min_price = (df['listing_price'].min() // 10000) * 10000  # 向下取整到最近的10000
    max_price = ((df['listing_price'].max() // 10000) + 1) * 10000  # 向上取整到最近的10000
    return pd.interval_range(start=min_price, end=max_price, freq=10000)

def main():
    # 初始化數據處理器
    data_processor = DataProcessor('/home/ubuntu/Nextplace/data_analyze/input/nextplace_training_data_0210.csv')
    
    # 預處理數據
    df = data_processor.preprocess_data()
    
    # 初始化分析器
    analyzer = PropertyAnalyzer(df)
    
    # 創建自定義區間
    sqft_bins = create_sqft_bins(df)
    year_bins = create_year_bins(df)
    price_bins = create_price_bins(df)
    
    # 執行各項分析
    results = {
        'city_analysis': analyzer.analyze_by_category('city'),
        'state_analysis': analyzer.analyze_by_category('state'),
        'beds_analysis': analyzer.analyze_by_category('beds'),
        'sqft_analysis': analyzer.analyze_by_bins('sqft', sqft_bins),
        'year_built_analysis': analyzer.analyze_by_bins('year_built', year_bins),
        'property_type_analysis': analyzer.analyze_by_category('property_type'),
        'last_sale_date_analysis': analyzer.analyze_by_date_periods('last_sale_date'),
        'market_analysis': analyzer.analyze_by_category('market'),
        'listing_price_analysis': analyzer.analyze_by_bins('listing_price', price_bins)
    }
    
    # 保存results到分析器實例中
    analyzer.results = results
    
    # 生成報告
    report = analyzer.generate_text_report(results)
    analyzer.print_report(report)
    
    # 生成視覺化
    visualizer = DataVisualizer(results)
    visualizer.generate_reports()

if __name__ == "__main__":
    main() 