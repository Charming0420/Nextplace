import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from scipy import stats
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import cross_val_score
from sklearn.feature_selection import mutual_info_regression
from data_processor import DataProcessor
from scipy.stats import chi2_contingency
import warnings
warnings.filterwarnings('ignore')

class FeatureImportanceAnalyzer:
    def __init__(self, df):
        self.df = df
        self.target_name = 'price_difference_ratio'
        self.target = (df['sale_price'] - df['listing_price']) / df['listing_price']
        self.features_to_analyze = [
            'city', 'state', 'beds', 'sqft', 'year_built',
            'property_type', 'market', 'listing_price'
        ]
        
    def prepare_data(self):
        """準備數據進行分析"""
        print("\n數據預處理開始...")
        
        # 複製需要的列
        df_prepared = self.df[self.features_to_analyze].copy()
        
        # 顯示初始缺失值情況
        print("\n特徵缺失值情況：")
        print(df_prepared.isnull().sum())
        
        # 處理缺失值
        for col in self.features_to_analyze:
            if df_prepared[col].dtype.name in ['float64', 'int64']:
                # 數值型特徵用中位數填充
                df_prepared[col] = df_prepared[col].fillna(df_prepared[col].median())
            else:
                # 類別型特徵用眾數填充
                df_prepared[col] = df_prepared[col].fillna(df_prepared[col].mode()[0])
        
        print("\n處理缺失值後的數據形狀:", df_prepared.shape)
        
        # 對類別變量進行編碼
        le = LabelEncoder()
        for col in ['city', 'state', 'property_type', 'market']:
            df_prepared[col] = le.fit_transform(df_prepared[col].astype(str))
        
        # 標準化數值特徵
        scaler = StandardScaler()
        for col in ['beds', 'sqft', 'year_built', 'listing_price']:
            df_prepared[col] = scaler.fit_transform(df_prepared[[col]])
        
        # 確保沒有無限值
        df_prepared = df_prepared.replace([np.inf, -np.inf], np.nan)
        df_prepared = df_prepared.fillna(0)
        
        print("數據預處理完成")
        return df_prepared
    
    def analyze_price_ranges(self):
        """分析不同價格區間的價格差異"""
        # 創建價格區間（每10萬美元一個區間）
        bins = pd.qcut(self.df['listing_price'], q=20)
        price_analysis = pd.DataFrame({
            'price_range': bins,
            'difference_ratio': self.target
        })
        
        # 計算每個區間的統計數據
        stats = price_analysis.groupby('price_range').agg({
            'difference_ratio': ['count', 'mean', 'median', 'std']
        }).round(4)
        
        return stats
        
    def analyze_feature_importance(self):
        """使用多種方法分析特徵重要性"""
        # 準備數據
        X = self.prepare_data()
        y = self.target
        
        # 1. 隨機森林特徵重要性
        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        rf.fit(X, y)
        rf_importance = pd.Series(rf.feature_importances_, index=self.features_to_analyze)
        
        # 2. 相關性分析
        correlations = {}
        for feature in self.features_to_analyze:
            if X[feature].dtype in ['int64', 'float64']:
                corr = stats.spearmanr(X[feature], y)[0]
            else:
                # 對於類別變量，使用均值編碼
                means = y.groupby(X[feature]).mean()
                encoded_feature = X[feature].map(means)
                corr = stats.spearmanr(encoded_feature, y)[0]
            correlations[feature] = abs(corr)
        
        correlation_importance = pd.Series(correlations)
        
        # 3. 互信息分析
        mi_scores = mutual_info_regression(X, y)
        mi_importance = pd.Series(mi_scores, index=self.features_to_analyze)
        
        # 4. 條件方差分析
        variance_importance = self.analyze_conditional_variance(X, y)
        
        # 綜合所有方法的結果
        importance_df = pd.DataFrame({
            '隨機森林重要性': rf_importance,
            '相關性重要性': correlation_importance,
            '互信息重要性': mi_importance,
            '條件方差重要性': variance_importance
        })
        
        # 標準化所有分數
        scaler = StandardScaler()
        importance_scaled = pd.DataFrame(
            scaler.fit_transform(importance_df),
            columns=importance_df.columns,
            index=importance_df.index
        )
        
        # 計算綜合得分
        importance_scaled['綜合重要性'] = importance_scaled.mean(axis=1)
        
        return importance_scaled.sort_values('綜合重要性', ascending=False)
    
    def analyze_conditional_variance(self, X, y):
        """分析條件方差"""
        variance_scores = {}
        
        for feature in self.features_to_analyze:
            if X[feature].dtype in ['int64', 'float64']:
                # 對數值特徵進行分箱
                bins = pd.qcut(X[feature], q=10, duplicates='drop')
            else:
                bins = X[feature]
            
            # 計算條件方差
            grouped_variance = y.groupby(bins).var()
            variance_scores[feature] = grouped_variance.mean()
        
        return pd.Series(variance_scores)
    
    def generate_detailed_report(self):
        """生成詳細的分析報告"""
        # 獲取特徵重要性
        importance_scores = self.analyze_feature_importance()
        
        # 分析價格區間
        price_range_stats = self.analyze_price_ranges()
        
        # 生成報告
        report = {
            "特徵重要性排名": importance_scores['綜合重要性'].to_dict(),
            "價格區間分析": price_range_stats.to_dict(),
            "詳細分析": {
                feature: self.analyze_feature_detail(feature)
                for feature in self.features_to_analyze
            }
        }
        
        return report
    
    def analyze_feature_detail(self, feature):
        """分析單個特徵的詳細情況"""
        try:
            result = {}
            if self.df[feature].dtype in ['int64', 'float64']:
                # 數值型特徵
                bins = pd.qcut(self.df[feature], q=10, duplicates='drop')
                stats = self.target.groupby(bins).agg({
                    'price_difference': [
                        ('count', 'count'),
                        ('mean', 'mean'),
                        ('median', 'median'),
                        ('std', 'std')
                    ]
                }).round(4)
                
                # 將統計結果轉換為字典格式
                for bin_range in stats.index:
                    result[str(bin_range)] = {
                        'count': int(stats.loc[bin_range, ('price_difference', 'count')]),
                        'mean': float(stats.loc[bin_range, ('price_difference', 'mean')]),
                        'median': float(stats.loc[bin_range, ('price_difference', 'median')]),
                        'std': float(stats.loc[bin_range, ('price_difference', 'std')])
                    }
            else:
                # 類別型特徵
                stats = self.target.groupby(self.df[feature]).agg({
                    'price_difference': [
                        ('count', 'count'),
                        ('mean', 'mean'),
                        ('median', 'median'),
                        ('std', 'std')
                    ]
                }).round(4)
                
                # 將統計結果轉換為字典格式
                for category in stats.index:
                    result[str(category)] = {
                        'count': int(stats.loc[category, ('price_difference', 'count')]),
                        'mean': float(stats.loc[category, ('price_difference', 'mean')]),
                        'median': float(stats.loc[category, ('price_difference', 'median')]),
                        'std': float(stats.loc[category, ('price_difference', 'std')])
                    }
            
            return result
        except Exception as e:
            print(f"分析 {feature} 時發生錯誤: {str(e)}")
            # 返回空結果而不是失敗
            return {
                'error': {
                    'count': 0,
                    'mean': 0.0,
                    'median': 0.0,
                    'std': 0.0
                }
            }
    
    def plot_importance_analysis(self):
        """繪製特徵重要性分析圖表"""
        importance_scores = self.analyze_feature_importance()
        
        plt.figure(figsize=(12, 8))
        sns.barplot(x=importance_scores['綜合重要性'], 
                   y=importance_scores.index,
                   palette='viridis')
        plt.title('特徵重要性綜合分析')
        plt.xlabel('標準化重要性得分')
        plt.tight_layout()
        plt.savefig('feature_importance_analysis.png')
        plt.close()
    
    def print_summary(self, report):
        """打印分析總結"""
        try:
            print("\n" + "="*80)
            print("房產價格差異影響因素分析總結")
            print("="*80)
            
            # 特徵影響力排名（使用絕對值）
            print("\n【特徵影響力排名】")
            print("註：數值越大表示該特徵對價格差異的影響力越強")
            for rank, (feature, score) in enumerate(sorted(report["特徵重要性排名"].items(), 
                                                         key=lambda x: abs(x[1]), 
                                                         reverse=True), 1):
                impact = "高" if abs(score) > 0.5 else "中" if abs(score) > 0.2 else "低"
                print(f"{rank}. {feature}: {abs(score):.4f} ({impact}影響力)")
            
            # 最重要的三個特徵的詳細分析
            top_features = sorted(report["特徵重要性排名"].items(), 
                                key=lambda x: abs(x[1]), 
                                reverse=True)[:3]
            
            print("\n【主要影響因素詳細分析】")
            for feature, score in top_features:
                print(f"\n{feature}:")
                print(f"- 影響力得分: {abs(score):.4f}")
                print("- 各區間/類別的價格差異情況:")
                
                if feature in report["詳細分析"]:
                    for category, stats in report["詳細分析"][feature].items():
                        if isinstance(stats, dict) and 'count' in stats:
                            print(f"  {category}:")
                            print(f"    樣本數: {stats['count']}")
                            print(f"    平均價格差異: {abs(stats['mean']*100):.2f}%")
                            print(f"    中位數價格差異: {abs(stats['median']*100):.2f}%")
                            print(f"    標準差: {stats['std']*100:.2f}%")
            
            print("\n【結論與建議】")
            print("在進行模型篩選時，建議按以下順序優先考慮：")
            for i, (feature, score) in enumerate(top_features, 1):
                impact = "高" if abs(score) > 0.5 else "中" if abs(score) > 0.2 else "低"
                print(f"{i}. {feature}")
                print(f"   - 影響力得分: {abs(score):.4f}")
                print(f"   - 影響程度: {impact}")
                print(f"   - 建議: {self._generate_feature_recommendation(feature, abs(score))}")
        
        except Exception as e:
            print(f"生成總結時發生錯誤: {str(e)}")

    def _generate_feature_recommendation(self, feature, abs_score):
        """根據特徵和絕對影響力生成具體建議"""
        if feature == 'listing_price':
            return "此特徵對價格差異影響最大，建議優先考慮不同價格區間的特性"
        elif feature == 'state':
            return "地理位置因素影響顯著，建議考慮各州的市場特性"
        elif feature == 'year_built':
            return "建造年份是重要因素，建議根據房齡進行分類分析"
        elif feature == 'property_type':
            return "房產類型對價格差異有重要影響，建議分類處理"
        elif feature == 'market':
            return "市場特性是重要考量因素"
        else:
            return f"{feature}可作為輔助參考指標"

    def save_markdown_report(self, report, input_file_path):
        """生成 Markdown 格式的分析報告"""
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        file_name = input_file_path.split('/')[-1].replace('.csv', '').replace('.xlsx', '')
        
        markdown = f"""# 房產價格差異影響因素分析報告
分析時間: {timestamp}
數據來源: {file_name}
總樣本數: {len(self.df):,} 筆

## 特徵影響力排名總表

| 排名 | 特徵 | 影響力得分 | 影響程度 | 建議優先度 |
|------|------|------------|----------|------------|
"""
        # 添加特徵影響力排名（使用絕對值）
        for rank, (feature, score) in enumerate(sorted(report["特徵重要性排名"].items(), 
                                                     key=lambda x: abs(x[1]), 
                                                     reverse=True), 1):
            impact = "高" if abs(score) > 0.5 else "中" if abs(score) > 0.2 else "低"
            priority = "最優先" if rank <= 3 else "次要" if rank <= 5 else "參考"
            markdown += f"| {rank} | {feature} | {abs(score):.4f} | {impact} | {priority} |\n"

        markdown += "\n## 各特徵詳細分析\n"
        
        # 依照重要性排序分析每個特徵
        sorted_features = sorted(report["特徵重要性排名"].items(), 
                               key=lambda x: abs(x[1]), 
                               reverse=True)
        
        for feature, score in sorted_features:
            markdown += f"\n### {feature}\n"
            markdown += f"- 重要性得分: {score:.4f}\n"
            markdown += f"- 影響方向: {'正面影響' if score > 0 else '負面影響'}\n"
            markdown += f"- 影響程度: {'高' if abs(score) > 0.5 else '中' if abs(score) > 0.2 else '低'}\n"
            
            detail = report["詳細分析"][feature]
            markdown += "- 區間/類別分析:\n"
            
            # 將統計數據轉換為表格形式
            markdown += "\n| 區間/類別 | 樣本數 | 平均差異 | 中位數差異 | 標準差 |\n"
            markdown += "|-----------|--------|----------|------------|--------|\n"
            
            for category, stats in detail.items():
                markdown += (f"| {category} | {stats['count']:,} | "
                           f"{stats['mean']*100:.2f}% | "
                           f"{stats['median']*100:.2f}% | "
                           f"{stats['std']*100:.2f}% |\n")

        markdown += "\n## 分析結論\n\n"
        
        # 添加高影響力特徵的分析
        high_impact = [(f, s) for f, s in sorted_features if abs(s) > 0.5]
        medium_impact = [(f, s) for f, s in sorted_features if 0.2 < abs(s) <= 0.5]
        
        markdown += "### 高影響力特徵\n"
        for feature, score in high_impact:
            markdown += f"- **{feature}** ({score:.4f}): "
            markdown += f"{'增加' if score < 0 else '減少'}價格差異的主要因素\n"
        
        markdown += "\n### 中等影響力特徵\n"
        for feature, score in medium_impact:
            markdown += f"- **{feature}** ({score:.4f}): "
            markdown += f"對價格差異有{'負面' if score < 0 else '正面'}影響\n"

        markdown += "\n## 實務建議\n\n"
        markdown += "### 優先考慮因素（依序）：\n"
        for i, (feature, score) in enumerate(sorted_features[:3], 1):
            markdown += f"{i}. **{feature}**\n"
            markdown += f"   - 影響力得分: {score:.4f}\n"
            markdown += f"   - 建議: {self._generate_feature_recommendation(feature, abs(score))}\n"

        # 保存報告
        output_filename = f'price_difference_analysis_{file_name}_{timestamp}.md'
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        return output_filename

def main():
    try:
        # 載入數據
        print("正在載入數據...")
        data_processor = DataProcessor('/home/ubuntu/Nextplace/data_analyze/input/nextplace_training_data_0210.csv')
        df = data_processor.preprocess_data()
        
        print("\n正在進行特徵重要性分析...")
        # 初始化分析器
        analyzer = FeatureImportanceAnalyzer(df)
        
        # 生成報告
        report = analyzer.generate_detailed_report()
        
        # 生成視覺化
        analyzer.plot_importance_analysis()
        print("\n特徵重要性圖表已保存為 'feature_importance_analysis.png'")
        
        # 打印總結
        analyzer.print_summary(report)
        
        # 保存 Markdown 報告
        report_filename = analyzer.save_markdown_report(report, '/home/ubuntu/Nextplace/data_analyze/input/nextplace_training_data_0210.csv')
        print(f"\nMarkdown 報告已保存為 '{report_filename}'")
        
    except ImportError as e:
        print(f"錯誤：無法導入必要的模組。請確保已安裝所有依賴項。\n詳細信息：{str(e)}")
    except FileNotFoundError as e:
        print(f"錯誤：找不到數據文件。請確保文件路徑正確。\n詳細信息：{str(e)}")
    except Exception as e:
        print(f"錯誤：程序執行過程中發生錯誤。\n詳細信息：{str(e)}")

if __name__ == "__main__":
    main() 