from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any

class BaseStrategy(ABC):
    @abstractmethod
    def predict(self, input_data: Dict[str, Any]) -> Tuple[float, str]:
        """
        執行預測
        Args:
            input_data: 輸入資料字典
        Returns:
            Tuple[float, str]: (預測價格, 預測日期)
        """
        pass 