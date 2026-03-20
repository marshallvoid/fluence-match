from typing import Dict, Optional

import pandas as pd

from match.ai_model.agent.core.postprocessing.filtering.base_filter import BaseFilter


class CommerceUserLevelFilter(BaseFilter):
    """
    Filter creators who has the desired commerce user level.
    """

    def __init__(
        self,
        commerce_user_level_col: str = "commerce_user_level",
        commerce_user_level: str = "PERSONAL",
    ):
        self.commerce_user_level_col = commerce_user_level_col
        self.commerce_user_level = commerce_user_level

    def filter(
        self,
        creator_df: pd.DataFrame,
        support_df: Optional[Dict[str, pd.DataFrame]] = None,
    ) -> pd.DataFrame:
        # Check if the commerce user level column exists
        if not self._check_column_exists(creator_df):
            error_msg = f"Column '{self.commerce_user_level_col}' does not exist in the DataFrame."
            raise ValueError(error_msg)

        # Filter the DataFrame based on the commerce user level
        filtered_creators_df = creator_df.loc[lambda df: df[self.commerce_user_level_col] == self.commerce_user_level]

        return filtered_creators_df  # type: ignore

    def _check_column_exists(self, creator_df: pd.DataFrame) -> bool:
        """
        Check if a column exists in the DataFrame.
        """
        return self.commerce_user_level_col in creator_df.columns
