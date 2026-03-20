from abc import ABC, abstractmethod
from typing import Dict, Optional

import pandas as pd


class BaseFilter(ABC):
    @abstractmethod
    def filter(
        self, creator_df: pd.DataFrame, support_df: Optional[Dict[str, pd.DataFrame]] = None
    ) -> pd.DataFrame: ...
