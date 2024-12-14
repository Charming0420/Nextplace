import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

class PriceVarianceAnalyzer:
    def __init__(self, csv_path):
        try:
            self.df = pd.read_csv(
                csv_path,
                on_bad_lines='skip',
                escapechar='\\',
                encoding='utf-8',
                low_memory=False
            )
            self.clean_data()
            self.df['price_variance'] = (self.df['sale_price'] - self.df['listing_price']) / self.df['listing_price']
            self.remove_outliers()
            
        except Exception as e:
            print(f"讀取資料時發生錯誤: {str(e)}")
            raise
    
    def clean_data(self):
        """清理資料"""
        required_columns = ['listing_price', 'sale_price', 'market', 'property_type', 'sqft', 'year_built']
        for col in required_columns:
            if col not in self.df.columns:
                raise ValueError(f"缺少必要欄位: {col}")
        
        self.df = self.df[
            (self.df['listing_price'].notna()) & 
            (self.df['sale_price'].notna()) &
            (self.df['listing_price'] > 0) & 
            (self.df['sale_price'] > 0)
        ]
        
        numeric_columns = ['listing_price', 'sale_price', 'sqft', 'year_built']
        for col in numeric_columns:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
    
    def remove_outliers(self):
        """移除極端值"""
        Q1 = self.df['price_variance'].quantile(0.05)
        Q3 = self.df['price_variance'].quantile(0.95)
        IQR = Q3 - Q1
        self.df = self.df[
            (self.df['price_variance'] >= Q1 - 1.5 * IQR) & 
            (self.df['price_variance'] <= Q3 + 1.5 * IQR)
        ]

    def analyze_market_variance(self):
        """分析各市場的價格變異率"""
        # 計算絕對值的價格變異率
        self.df['abs_price_variance'] = self.df['price_variance'].abs()
        
        # 計算各市場的統計數據
        market_stats = self.df.groupby('market').agg({
            'price_variance': ['mean', 'count', 'std'],
            'abs_price_variance': 'mean'
        })
        
        # 整理列名
        market_stats.columns = ['mean', 'count', 'std', 'abs_mean']
        
        # 篩選出樣本數足夠的市場
        valid_markets = market_stats[market_stats['count'] >= 50]
        
        # 儲存50名最準確的市場（絕對值平均最小）
        self.top_20_accurate_markets = valid_markets.sort_values('abs_mean').head(50).index.tolist()
        
        # 返回所有絕對值平均小於5%的市場
        return valid_markets[valid_markets['abs_mean'] < 0.05].sort_values('abs_mean')
    
    def analyze_sqft_variance(self):
        """分析不同面積範圍的價格變異率"""
        # 使用 .copy() 避免 SettingWithCopyWarning
        valid_df = self.df[self.df['sqft'].notna() & (self.df['sqft'] > 0)].copy()
        valid_df['sqft_range'] = pd.cut(
            valid_df['sqft'], 
            bins=[0, 1000, 2000, 3000, 4000, float('inf')],
            labels=['<1000', '1000-2000', '2000-3000', '3000-4000', '>4000']
        )
        return valid_df.groupby('sqft_range', observed=True)['price_variance'].agg([
            'mean', 'count', 'std'
        ]).sort_values('mean', ascending=False)
    
    def analyze_property_type_variance(self):
        """分析不同物業類型的價格變異率"""
        # 定義物業類型對應
        property_type_mapping = {
            '1': 'Single Family Residential',
            '2': 'Condo/Co-op',
            '3': 'Townhouse',
            '4': 'Multi-Family',
            '5': 'Mobile/Manufactured',
            '6': 'House',
            '7': 'Apartment',
            '8': 'Lot/Land',
            '10': 'Other',
            '13': 'Residential'
        }
        
        valid_df = self.df[self.df['property_type'].notna()].copy()
        valid_df['property_type'] = valid_df['property_type'].astype(str).map(property_type_mapping)
        
        stats = valid_df.groupby('property_type', observed=True)['price_variance'].agg([
            'mean', 'count', 'std'
        ]).sort_values('mean', ascending=False)
        return stats[stats['count'] >= 20]
    
    def analyze_year_built_variance(self):
        """分析不同建造年份的價格變異率"""
        valid_df = self.df[
            (self.df['year_built'].notna()) & 
            (self.df['year_built'] > 1800) & 
            (self.df['year_built'] <= 2024)
        ].copy()
        
        valid_df['year_range'] = pd.cut(
            valid_df['year_built'],
            bins=[1800, 1950, 1980, 2000, 2010, 2024],
            labels=['<1950', '1950-1980', '1980-2000', '2000-2010', '2010-2024']
        )
        return valid_df.groupby('year_range', observed=True)['price_variance'].agg([
            'mean', 'count', 'std'
        ]).sort_values('mean', ascending=False)

def format_percentage(value):
    """將數值格式化為百分比"""
    if pd.isna(value):
        return "N/A"
    return f"{value * 100:.2f}%"

def plot_variance_analysis(data, title, filename):
    """Plot price variance analysis chart"""
    if title == "Market Price Variance":
        # 只繪製絕對值平均小於2%的市場
        data = data[data['abs_mean'] < 0.02]
    
    plt.figure(figsize=(14, max(8, len(data) * 0.4)))  # 依據數據量調整圖表高度
    
    # 繪製平均值長條圖
    means = data['mean'].sort_values(ascending=True)
    bars = plt.barh(range(len(means)), means)
    
    # 設定圖表標籤
    plt.title(title, fontsize=12, pad=20)
    plt.xlabel('Price Variance', fontsize=10)
    plt.ylabel('Market', fontsize=10)
    
    # 設定y軸標籤
    plt.yticks(range(len(means)), means.index, fontsize=9)
    
    # 在每個長條後面添加數值標籤
    for i, v in enumerate(means):
        plt.text(v, i, f' {v:.2%}', va='center', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(filename, bbox_inches='tight', dpi=300)
    plt.close()

def main():
    current_dir = Path(__file__).parent
    csv_path = "/home/ubuntu/Nextplace/nextplace/miner/ml/strategies/data_analytics/nextplace_training_data.csv"
    
    analyzer = PriceVarianceAnalyzer(csv_path)
    
    # 市場價格變異分析
    market_variance = analyzer.analyze_market_variance()
    print("\n=== Market Price Variance Analysis ===")
    print("Markets with Absolute Variance < 5%:")
    detailed_market = market_variance.copy()
    detailed_market['abs_mean'] = detailed_market['abs_mean'].apply(format_percentage)
    detailed_market['mean'] = detailed_market['mean'].apply(format_percentage)
    detailed_market['std'] = detailed_market['std'].apply(format_percentage)
    detailed_market.columns = ['Mean Variance', 'Sample Count', 'Std Dev', 'Abs Mean']
    pd.set_option('display.max_rows', None)  # 設置顯示所有行
    pd.set_option('display.max_columns', None)  # 設置顯示所有列
    pd.set_option('display.width', None)  # 設置顯示寬度
    pd.set_option('display.max_colwidth', None)  # 設置列寬度
    print(detailed_market)
    pd.reset_option('all')  # 重置所有顯示設置
    
    print("\nTop 20 Most Accurate Markets:")
    print(analyzer.top_20_accurate_markets)
    
    # 2. 面積範圍價格變異分析
    sqft_variance = analyzer.analyze_sqft_variance()
    print("\n=== Square Footage Price Variance Analysis ===")
    detailed_sqft = sqft_variance.copy()
    detailed_sqft['mean'] = detailed_sqft['mean'].apply(format_percentage)
    detailed_sqft['std'] = detailed_sqft['std'].apply(format_percentage)
    detailed_sqft.columns = ['Mean Variance', 'Sample Count', 'Std Dev']
    print("Analysis by Square Footage Range:")
    print(detailed_sqft)
    
    # 3. 物業類型價格變異分析
    property_variance = analyzer.analyze_property_type_variance()
    print("\n=== Property Type Price Variance Analysis ===")
    detailed_property = property_variance.copy()
    detailed_property['mean'] = detailed_property['mean'].apply(format_percentage)
    detailed_property['std'] = detailed_property['std'].apply(format_percentage)
    detailed_property.columns = ['Mean Variance', 'Sample Count', 'Std Dev']
    print("Analysis by Property Type (min 20 samples):")
    print(detailed_property)
    
    # 4. 建造年份價格變異分析
    year_variance = analyzer.analyze_year_built_variance()
    print("\n=== Construction Year Price Variance Analysis ===")
    detailed_year = year_variance.copy()
    detailed_year['mean'] = detailed_year['mean'].apply(format_percentage)
    detailed_year['std'] = detailed_year['std'].apply(format_percentage)
    detailed_year.columns = ['Mean Variance', 'Sample Count', 'Std Dev']
    print("Analysis by Construction Year Range:")
    print(detailed_year)
    
    # 儲存最準確的市場列表到檔案
    with open('accurate_markets.txt', 'w') as f:
        f.write("Top 20 Most Accurate Markets:\n")
        for market in analyzer.top_20_accurate_markets:
            f.write(f"{market}\n")

if __name__ == "__main__":
    main()