import matplotlib.pyplot as plt
import seaborn as sns

class DataVisualizer:
    def __init__(self, results):
        self.results = results
        
    def plot_category_analysis(self, data, title, filename):
        """繪製類別分析圖表"""
        plt.figure(figsize=(12, 6))
        sns.barplot(data=data, x=data.columns[0], y='mean')
        plt.title(title)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f'reports/{filename}.png')
        plt.close()
    
    def generate_reports(self):
        """生成所有分析報告"""
        # 確保報告目錄存在
        import os
        os.makedirs('reports', exist_ok=True)
        
        # 為每個分析結果生成視覺化
        for analysis_name, data in self.results.items():
            title = f'{analysis_name.replace("_", " ").title()} vs Price Difference Ratio'
            self.plot_category_analysis(data, title, analysis_name) 