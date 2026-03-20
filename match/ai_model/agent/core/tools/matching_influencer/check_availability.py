# pyright: reportIndexIssue=false
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, cast

import pandas as pd
from langchain_core.callbacks import (
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from langchain_core.tools.base import ArgsSchema
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from match.ai_model.agent.core.postprocessing.filtering.commerce_user_level_filter import CommerceUserLevelFilter
from match.ai_model.agent.core.postprocessing.filtering.filter_container import FilterContainer
from match.ai_model.agent.core.postprocessing.filtering.models.revenue_criteria import RevenueCriteria
from match.ai_model.agent.core.postprocessing.filtering.revenue_filter import RevenueFilter5Min2Month
from match.ai_model.agent.core.tools.matching_influencer.utils import calc_followers_bucket
from match.ai_model.agent.influencer_matcher_agent.constants import ALLOWED_INDUSTRIES
from match.config import Settings

CACHE_DIR = Path("data_for_ai")
CACHE_DIR.mkdir(exist_ok=True)


class InfluencerStatsInput(BaseModel):
    industries: List[ALLOWED_INDUSTRIES] = Field(
        description="List of industries to check for influencer availability. Must be one of the allowed industries."
    )
    brand_id: Optional[str] = Field(
        default=None,
        description="Optional brand ID to filter influencers by brand partnership",
    )


class InfluencerStats(BaseTool):
    """
    Encapsulates influencer data loading and statistics calculation.
    """

    name: str = "influencer_stats"
    description: str = "Counts influencers in specified industries and segments them by follower buckets."
    args_schema: Optional[ArgsSchema] = InfluencerStatsInput
    return_direct: bool = True

    # Type annotations for attributes set via __dict__ - for type checking only
    settings: Optional[Settings] = None
    engine: Optional[Engine] = None
    session_factory: Optional[AsyncSession] = None

    # Product category of content
    content_cat_table: Optional[str] = None
    creator_content_cat_table: Optional[str] = None

    # Product category of video
    video_content_cat_table: Optional[str] = None
    creator_video_content_cat_table: Optional[str] = None

    creator_metadata_table: Optional[str] = None
    revenue_table: Optional[str] = None

    final_metadata_df: Optional[pd.DataFrame] = None
    final_metadata_df_path: Optional[str] = None

    # Optional: Add model_config to explicitly allow extra attributes
    model_config = {"extra": "allow"}

    def __init__(self, settings: Settings, session_factory: AsyncSession) -> None:
        # First call super().__init__() without any arguments
        super().__init__()

        # Then set instance attributes directly in __dict__ to bypass validation
        self.__dict__["settings"] = settings
        self.__dict__["session_factory"] = session_factory
        self.__dict__["content_cat_table"] = "content_categories"
        self.__dict__["creator_content_cat_table"] = "creator_content_categories"
        self.__dict__["creator_metadata_table"] = "creators"
        self.__dict__["revenue_table"] = "creator_revenues"
        self.__dict__["video_content_cat_table"] = "ecommerce_product_categories"
        self.__dict__["creator_video_content_cat_table"] = "creator_product_categories"

        # table_info = await self._load_metadata()

        # # Load metadata after initialization
        # self.__dict__["final_metadata_df"] = table_info[0]
        # self.__dict__["final_metadata_df_path"] = table_info[1]

    async def initialize(self) -> None:
        """Asynchronous initialization that should be called after __init__"""
        table_info = await self._load_metadata()
        self.__dict__["final_metadata_df"] = table_info[0]
        self.__dict__["final_metadata_df_path"] = table_info[1]

    async def _load_data(
        self,
        table_name: str,
        columns: Optional[List[str]] = None,
        partition: int = 100,
        join_clause: Optional[str] = None,
        where_clause: Optional[str] = None,
        params: Optional[dict] = None,
    ) -> pd.DataFrame:
        """
        Load a SQL table into a pandas DataFrame using streaming with optional JOINs and filters.
        :param table_name: Main table to query from
        :param columns: Columns to select (defaults to all)
        :param partition: Rows per streamed batch
        :param join_clause: Optional SQL JOIN clause (e.g. "JOIN X ON Y")
        :param where_clause: Optional SQL WHERE condition (e.g. "X = :x")
        :param params: Dictionary of bind parameters for the query
        :return: pandas DataFrame
        """
        assert self.session_factory is not None, "Session factory must be initialized before loading data"
        async with self.session_factory() as session:
            async with session.begin():
                # Validate table
                table_check = text(
                    """
                    SELECT COUNT(*) FROM information_schema.tables WHERE table_name = :table_name
                    """
                )
                exists = (await session.execute(table_check, {"table_name": table_name})).scalar() > 0
                if not exists:
                    msg = f"Table '{table_name}' does not exist"
                    raise ValueError(msg)

                # Validate and build SELECT clause
                if columns:
                    select_clause = ", ".join(columns)
                else:
                    select_clause = "*"

                # Build query with optional JOIN and WHERE
                query_str = f"SELECT {select_clause} FROM {table_name}"
                if join_clause:
                    query_str += f" {join_clause}"
                if where_clause:
                    query_str += f" WHERE {where_clause}"

                query = text(query_str)
                result = await session.stream(query, params or {})
                all_rows = []
                async for batch in result.partitions(partition):
                    all_rows.extend(batch)

                df = pd.DataFrame(all_rows, columns=result.keys())
                return df

    async def _cached_load(self, table_name: str, columns: list[str] | None = None) -> pd.DataFrame:
        """
        Load a DataFrame from cache if fresh; otherwise reload from DB and overwrite cache.

        Args:
            table_name: identifier for cache file (will be {table_name}.csv)
            columns: optional list of columns to select via self._load_data
        """
        cache_ttl = timedelta(hours=1)
        # Define cache file path
        cache_file = Path(CACHE_DIR) / f"{table_name}.csv"
        cache_file = cache_file.resolve()

        # Check if cache exists and is fresh
        if cache_file.exists():
            modified_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - modified_time < cache_ttl:
                logger.info(f"Loading '{table_name}' from cache (last modified: {modified_time.isoformat()})")
                df = pd.read_csv(cache_file)
                logger.info(f"'{table_name}': Length = {len(df)}")
                return df
            logger.info(f"Cache stale for '{table_name}'. Reloading from DB.")
        else:
            logger.info(f"No cache found for '{table_name}'. Loading from DB.")

        # Load fresh data from DB
        df = await self._load_data(table_name, columns) if columns is not None else await self._load_data(table_name)
        # Save to cache for next time
        try:
            df.to_csv(cache_file, index=False)
            logger.info(f"Cached '{table_name}' to '{cache_file}'")
        except Exception as e:
            logger.warning(f"Failed to write cache for '{table_name}': {e}")

        logger.info(f"'{table_name}': Length = {len(df)}")
        return df

    async def _load_metadata(self) -> tuple:
        """
        Merge influencer info with their categories into one DataFrame.
        """
        # Type assertions
        content_cat_table = cast(str, self.content_cat_table)
        creator_content_cat_table = cast(str, self.creator_content_cat_table)
        creator_metadata_table = cast(str, self.creator_metadata_table)
        revenue_table = cast(str, self.revenue_table)
        video_content_cat_table = cast(str, self.video_content_cat_table)
        creator_video_content_cat_table = cast(str, self.creator_video_content_cat_table)

        try:
            content_cat_df = await self._cached_load(content_cat_table, ["id", "title"])

            creator_content_cat_df = await self._cached_load(
                creator_content_cat_table, ["creator_id", "content_category_id"]
            )

            video_content_cat_df = await self._cached_load(video_content_cat_table, ["id", "name"])

            creator_video_content_cat_df = await self._cached_load(
                creator_video_content_cat_table, ["creator_id", "product_category_id"]
            )

            creator_metadata_df = await self._cached_load(
                creator_metadata_table,
                ["id", "unique_id", "nickname", "signature", "total_followers", "commerce_user_level", "seller_id"],
            )

            revenue_df = await self._cached_load(revenue_table, ["creator_id", "revenue", "state_date"])

        except Exception as e:
            logger.error(f"Failed to load data from the database: {str(e)}")
            error_msg = f"Failed to load data from the database: {str(e)}"
            raise RuntimeError(error_msg)

        # Merge creator metadata with revenue data to get the revenue information
        creator_metadata_df = creator_metadata_df.merge(
            revenue_df.groupby("creator_id")["revenue"].sum().reset_index()[["creator_id", "revenue"]],
            left_on="id",
            right_on="creator_id",
            how="left",
        )
        logger.info(f"Length of creator_metadata_df after merge with revenue_df: {len(creator_metadata_df)}")
        # Filter
        filter_container = self._construct_filter_container()
        creator_metadata_df = filter_container.filter(
            creator_df=creator_metadata_df,
            support_df={
                "revenue_df": revenue_df,
            },
        )

        creator_content_cat_df = creator_content_cat_df.pipe(
            lambda df: df.merge(
                content_cat_df[["id", "title"]],
                left_on="content_category_id",
                right_on="id",
                how="left",
            )
            .pipe(lambda df: df.groupby("creator_id")["title"].apply(list))
            .reset_index()
        )

        video_creator_content_cat_df = creator_video_content_cat_df.pipe(
            lambda df: df.merge(
                video_content_cat_df[["id", "name"]],
                left_on="product_category_id",
                right_on="id",
                how="left",
            )
            .pipe(lambda df: df.groupby("creator_id")["name"].apply(list))
            .reset_index()
        )

        metadata_cols = [
            "id",
            "unique_id",
            "nickname",
            "signature",
            "total_followers",
            "seller_id",
            "revenue",
        ]

        result_df = creator_metadata_df.pipe(
            lambda df: df.merge(
                creator_content_cat_df,
                left_on="id",
                right_on="creator_id",
                how="left",
            )
            .pipe(lambda df: df.rename(columns={"title": "content_categories"}))
            .pipe(
                lambda df: df.assign(
                    content_categories=df["content_categories"].apply(lambda x: x if isinstance(x, list) else [])
                )
            )
            .pipe(
                lambda df: df.merge(
                    video_creator_content_cat_df,
                    left_on="id",
                    right_on="creator_id",
                    how="left",
                )
            )
            .pipe(lambda df: df.rename(columns={"name": "video_content_categories"}))
            .pipe(
                lambda df: df.assign(
                    video_content_categories=lambda x: x["video_content_categories"].apply(
                        lambda x: x if isinstance(x, list) else []
                    )
                )
            )
            .pipe(
                lambda df: df.assign(
                    main_category=lambda x: x["content_categories"] + x["video_content_categories"], axis=1
                )
            )
        )[metadata_cols + ["main_category"]]

        # Save to current dir and get the absolute path
        # Create data_for_ai directory if it doesn't exist
        # os.makedirs("data_for_ai", exist_ok=True)

        # result_df.to_csv("data_for_ai/influencer_metadata.csv", index=False)
        result_df_path = os.path.abspath("data_for_ai/influencer_metadata.csv")
        return (result_df, result_df_path)

    def _construct_filter_container(self) -> FilterContainer:
        """
        Construct a filter container with the necessary filters.
        """
        filter_container = FilterContainer()
        commerce_user_level_filter = CommerceUserLevelFilter(
            commerce_user_level="PERSONAL",
        )
        revenue_filter = RevenueFilter5Min2Month(rev_criteria=RevenueCriteria())
        filter_container.add_filter(commerce_user_level_filter)
        filter_container.add_filter(revenue_filter)
        return filter_container

    async def _run(
        self,
        industries: List[ALLOWED_INDUSTRIES],
        brand_id: Optional[str] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> tuple:
        """`
        Count influencers in specified industries and segment them by follower buckets.

        Returns:
            A dict with overall total and per-industry segment breakdown.
        """
        await self.initialize()
        # Type assertion
        final_metadata_df = cast(pd.DataFrame, self.final_metadata_df)

        result_df = final_metadata_df.loc[
            lambda df: df["main_category"].apply(lambda x: any(item in x for item in industries))
        ]

        pd.set_option("display.max_columns", None)
        logger.info(f"Fetch success. Length of result_df : {len(result_df)}")
        logger.info(f"Dataframe: {result_df.head()}")

        follower_segment_df = result_df.pipe(
            lambda df: df.assign(followers_segment=df.apply(calc_followers_bucket, axis=1))
        ).pipe(lambda df: df.groupby("followers_segment").size().reset_index(name="count"))

        total_influencers = result_df.shape[0]

        # Brand Creators
        brand_creators = (
            (
                await self._load_data(
                    table_name="creators",
                    columns=[
                        "creators.id",
                        "creators.uid",
                        "creators.unique_id",
                        "creators.nickname",
                        "creators.signature",
                        "creators.total_followers",
                    ],
                    join_clause="""
                JOIN creator_partnered_brands cpb ON cpb.creator_id = creators.id
            """,
                    where_clause="cpb.partnered_brand_id = :brand_id",
                    params={"brand_id": str(brand_id)},
                )
            )
            if brand_id
            else None
        )

        result = {
            "total_influencers": total_influencers,
            "follower_segment_df": follower_segment_df.to_dict(orient="records"),
        }

        # result_df.to_csv(self.final_metadata_df_path, index=False)

        # logger.info(f"Data saved to {self.final_metadata_df_path}")

        return (result_df, result, brand_creators)
