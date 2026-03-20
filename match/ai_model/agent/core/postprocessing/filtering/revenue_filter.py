from datetime import datetime, timedelta
from typing import Dict, Optional

import pandas as pd

from match.ai_model.agent.core.postprocessing.filtering.base_filter import BaseFilter
from match.ai_model.agent.core.postprocessing.filtering.models.revenue_criteria import (
    RevenueCriteria,
)


class RevenueFilter5Min2Month(BaseFilter):
    """
    Filter creators of all segments based on their revenue in the last 30 days.
    Criteria:
    - Minimum revenue: e.g. 5M VND
    - Maximum consider days: e.g. 60 days
    - Period in days: e.g. 30 days
    - There has to be one revenue table and one creator table
    """

    def __init__(
        self,
        rev_criteria: RevenueCriteria,
    ):
        self.min_revenue = rev_criteria.min_revenue
        self.max_consider_days = rev_criteria.max_consider_days
        self.period_in_day = rev_criteria.period_in_day

    def filter(self, creator_df: pd.DataFrame, support_df: Optional[Dict[str, pd.DataFrame]] = None) -> pd.DataFrame:
        # Check if the required dataframes are provided
        assert support_df is not None, "Support dataframe is required for filtering."

        if "revenue_df" not in support_df:
            error_msg = "Revenue dataframe is required for filtering."
            raise ValueError(error_msg)
        to_retain_cretor_ids = self._get_quality_creators(support_df["revenue_df"])
        # Filter the creator dataframe based on the creator IDs
        filtered_creators_df = creator_df.loc[lambda df: df["id"].isin(to_retain_cretor_ids)]

        return filtered_creators_df  # type: ignore

    def _get_start_consider_date(self) -> datetime:
        """
        Get the start date for considering revenue.
        The start date is calculated as the current date minus the maximum consider days.
        """
        return datetime.now() - timedelta(days=self.max_consider_days)

    def _get_quality_creators(self, rev_df: pd.DataFrame) -> pd.DataFrame:
        """
        Get the quality creators based on the revenue criteria.
        """
        # Make sure state_date is in datetime format
        rev_df["state_date"] = pd.to_datetime(rev_df["state_date"], errors="coerce")
        # Get data from the last 60 days
        creator_revenues_df = rev_df.loc[lambda df: df["state_date"] >= self._get_start_consider_date()]
        # Compute the revenue per creator for the last 30 days since the most recent state date of each creator
        creator_revenues_df = creator_revenues_df.assign(
            min_consider_date=lambda df: df.groupby("creator_id")["state_date"].transform(
                lambda x: x.max() - timedelta(days=self.period_in_day)
            ),
        )
        creator_revenues_df = (
            creator_revenues_df.pipe(lambda df: df.loc[lambda df: df["state_date"] >= (df["min_consider_date"])])
            .pipe(lambda df: df.groupby("creator_id", as_index=False)["revenue"].agg("sum"))  # add sum revenue
            .pipe(lambda df: df.rename(columns={"revenue": "revenue_30_days"}))
            .pipe(lambda df: df.loc[df["revenue_30_days"] >= self.min_revenue])
        )
        to_retain_cretor_ids = creator_revenues_df["creator_id"].unique()

        return to_retain_cretor_ids
