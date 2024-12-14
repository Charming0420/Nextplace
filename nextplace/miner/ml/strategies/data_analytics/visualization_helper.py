import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def plot_variance_analysis(data, title, filename):
    """繪製價格變異率分析圖表"""
    plt.figure(figsize=(12, 6))
    
    # 繪製平均值長條圖
    ax = sns.barplot(x=data.index, y=data['mean'])
    
    # 添加標題和標籤
    plt.title(title)
    plt.xlabel('類別')
    plt.ylabel('價格變異率')
    
    # 旋轉 x 軸標籤
    plt.xticks(rotation=45)
    
    # 在每個長條上添加數值標籤
    for i, v in enumerate(data['mean']):
        ax.text(i, v, f'{v:.2%}', ha='center', va='bottom')
    
    # 儲存圖表
    output_path = Path(__file__).parent / 'plots' / filename
    output_path.parent.mkdir(exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()