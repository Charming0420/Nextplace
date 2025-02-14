import numpy as np

def create_bins(series, num_bins):
    """創建等寬的數值區間"""
    return np.linspace(series.min(), series.max(), num_bins + 1) 