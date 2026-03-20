from typing import Dict, List, Optional

import pandas as pd
from loguru import logger

from match.ai_model.agent.core.postprocessing.filtering.base_filter import BaseFilter


class FilterContainer:
    """
    A container for multiple filters.
    """

    def __init__(self) -> None:
        self.filters: List[BaseFilter] = []

    def add_filter(self, filter: BaseFilter) -> None:
        """
        Add a filter to the container.
        """
        if not isinstance(filter, BaseFilter):
            value_error_msg = "Filter must be an instance of BaseFilter."
            raise ValueError(value_error_msg)
        self.filters.append(filter)

    def filter(self, creator_df: pd.DataFrame, support_df: Optional[Dict[str, pd.DataFrame]] = None) -> pd.DataFrame:
        for filter in self.filters:
            creator_df = filter.filter(creator_df, support_df)
            logger.info(f"Filter {filter.__class__.__name__} applied. Remaining rows: {len(creator_df)}")
        return creator_df
