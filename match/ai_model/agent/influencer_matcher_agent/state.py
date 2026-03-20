from operator import add
from typing import Annotated, Any, Dict, List, Optional, TypedDict

import pandas as pd
from langgraph.graph.message import add_messages

from match.ai_model.agent.influencer_matcher_agent.structured_output import TableDevisionPlan, UserQueryExtraction


class State(TypedDict):
    input: str
    description: Optional[str]
    additional_instructions: Optional[str]
    extracted_input_metadata: UserQueryExtraction
    product_type: List[str]
    total_num_influencers: Dict[str, Any]
    influencer_info_table: pd.DataFrame
    generate_plan: Annotated[list[str], add]
    generate_plan_messages: Annotated[list, add_messages]
    pandas_query: str
    rec_table_division: TableDevisionPlan
    rec_plan_summary: str
    rec_influencer: List[Any]
    brand_template: Optional[Dict[str, Any]]
    brand_id: Optional[str]
    brand_creators: pd.DataFrame
