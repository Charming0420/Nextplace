import pandas as pd
import numpy as np
import json
from tabulate import tabulate

class PropertyAnalyzer:
    def __init__(self, df):
        self.df = df
        
    def analyze_by_category(self, column):
        """按類別分析價格差異"""
        analysis = self.df.groupby(column, observed=True)['price_difference_ratio'].agg([
            'mean',
            'median',
            'std',
            'count'
        ]).reset_index()
        
        analysis = analysis.sort_values('mean')
        
        # 添加百分比格式化
        analysis['mean_percentage'] = analysis['mean'].map('{:.2%}'.format)
        analysis['median_percentage'] = analysis['median'].map('{:.2%}'.format)
        analysis['std_percentage'] = analysis['std'].map('{:.2%}'.format)
        
        return analysis
    
    def analyze_by_bins(self, column, bins):
        """按數值區間分析價格差異"""
        self.df[f'{column}_bin'] = pd.cut(self.df[column], bins)
        
        analysis = self.df.groupby(f'{column}_bin', observed=True)['price_difference_ratio'].agg([
            'mean',
            'median',
            'std',
            'count'
        ]).reset_index()
        
        # 添加百分比格式化
        analysis['mean_percentage'] = analysis['mean'].map('{:.2%}'.format)
        analysis['median_percentage'] = analysis['median'].map('{:.2%}'.format)
        analysis['std_percentage'] = analysis['std'].map('{:.2%}'.format)
        
        return analysis
    
    def analyze_by_date_periods(self, date_column):
        """按時間區間分析價格差異"""
        self.df[f'{date_column}_year'] = self.df[date_column].dt.year
        
        analysis = self.df.groupby(f'{date_column}_year', observed=True)['price_difference_ratio'].agg([
            'mean',
            'median',
            'std',
            'count'
        ]).reset_index()
        
        # 添加百分比格式化
        analysis['mean_percentage'] = analysis['mean'].map('{:.2%}'.format)
        analysis['median_percentage'] = analysis['median'].map('{:.2%}'.format)
        analysis['std_percentage'] = analysis['std'].map('{:.2%}'.format)
        
        return analysis
    
    def generate_text_report(self, results):
        """生成詳細的文本報告"""
        report = {
            "分析報告": {
                "總數據量": len(self.df),
                "分析時間": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                "詳細分析結果": {}
            }
        }
        
        for analysis_name, data in results.items():
            category_name = analysis_name.replace('_analysis', '').replace('_', ' ').title()
            
            # 轉換DataFrame為易讀的格式
            results_list = []
            for _, row in data.iterrows():
                result_dict = {
                    "類別/區間": str(row.iloc[0]) if isinstance(row.iloc[0], (pd.Interval, pd.Period)) else str(row[data.columns[0]]),
                    "平均差異": row['mean_percentage'],
                    "中位數差異": row['median_percentage'],
                    "標準差": row['std_percentage'],
                    "樣本數": int(row['count'])
                }
                results_list.append(result_dict)
            
            # 排序結果（按平均差異）
            results_list = sorted(results_list, key=lambda x: float(x['平均差異'].rstrip('%')))
            
            # 添加到報告中
            report["分析報告"]["詳細分析結果"][category_name] = {
                "樣本總數": sum(r['樣本數'] for r in results_list),
                "最小差異組": results_list[0],
                "最大差異組": results_list[-1],
                "詳細數據": results_list
            }
        
        return report
    
    def save_to_excel(self, results, filename=None):
        """將分析結果保存為Excel文件，每個分析項目一個工作表"""
        try:
            # 如果沒有提供文件名，則使用時間戳創建文件名
            if filename is None:
                current_time = pd.Timestamp.now().strftime("%m%d%H%M")
                filename = f'analysis_results_{current_time}.xlsx'
            
            # 創建ExcelWriter對象
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                for analysis_name, data in results.items():
                    # 獲取可讀的sheet名稱
                    sheet_name = analysis_name.replace('_analysis', '').replace('_', ' ').title()
                    
                    # 創建用於保存的DataFrame
                    export_data = []
                    for _, row in data.iterrows():
                        # 使用列名而不是位置索引
                        category_value = row[data.columns[0]]  # 使用第一列的列名
                        export_dict = {
                            "類別/區間": str(category_value),
                            "平均差異": float(row['mean']),
                            "平均差異(%)": row['mean_percentage'],
                            "中位數差異": float(row['median']),
                            "中位數差異(%)": row['median_percentage'],
                            "標準差": float(row['std']),
                            "標準差(%)": row['std_percentage'],
                            "樣本數": int(row['count'])
                        }
                        export_data.append(export_dict)
                    
                    # 轉換為DataFrame
                    df_export = pd.DataFrame(export_data)
                    
                    # 按平均差異排序
                    df_export = df_export.sort_values('平均差異')
                    
                    # 將DataFrame寫入Excel工作表
                    df_export.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # 自動調整列寬
                    worksheet = writer.sheets[sheet_name]
                    for idx, col in enumerate(df_export.columns):
                        max_length = max(
                            df_export[col].astype(str).apply(len).max(),
                            len(col)
                        )
                        worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2
                
                print(f"\nExcel報告已保存至: {filename}")
                
        except Exception as e:
            print(f"保存Excel文件時發生錯誤: {str(e)}")

    def print_report(self, report):
        """打印格式化的報告"""
        print("\n" + "="*80)
        print(f"房產價格差異分析報告")
        print(f"生成時間: {report['分析報告']['分析時間']}")
        print(f"總數據量: {report['分析報告']['總數據量']:,} 筆")
        print("="*80)
        
        for category, results in report['分析報告']['詳細分析結果'].items():
            print(f"\n{category} 分析結果:")
            print("-"*80)
            print(f"樣本總數: {results['樣本總數']:,} 筆")
            print(f"\n最小差異組:")
            print(f"類別/區間: {results['最小差異組']['類別/區間']}")
            print(f"平均差異: {results['最小差異組']['平均差異']}")
            print(f"中位數差異: {results['最小差異組']['中位數差異']}")
            print(f"樣本數: {results['最小差異組']['樣本數']:,} 筆")
            
            print(f"\n最大差異組:")
            print(f"類別/區間: {results['最大差異組']['類別/區間']}")
            print(f"平均差異: {results['最大差異組']['平均差異']}")
            print(f"中位數差異: {results['最大差異組']['中位數差異']}")
            print(f"樣本數: {results['最大差異組']['樣本數']:,} 筆")
            
            print("\n詳細數據:")
            headers = results['詳細數據'][0].keys()
            rows = [r.values() for r in results['詳細數據']]
            print(tabulate(rows, headers=headers, tablefmt='grid'))
            print("-"*80)
        
        # 保存報告到JSON文件
        with open('analysis_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 在最後添加Excel文件的保存
        print("\n正在生成Excel報告...")
        self.save_to_excel(self.results) 