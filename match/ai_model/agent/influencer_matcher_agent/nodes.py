import re
from typing import cast

import pandas as pd
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.runnables import RunnableLambda
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from match.ai_model.agent.core.prompts.matching_influencers_prompts import (
    input_metadata_extraction_prompt,
    match_product_system_prompt,
    match_product_user_prompt,
    plan_generation_system_prompt,
    plan_generation_user_prompt,
    plan_reflection_system_prompt,
    plan_summary_prompt,
    table_devision_extraction_prompt,
)
from match.ai_model.agent.core.tools.matching_influencer.check_availability import InfluencerStats
from match.ai_model.agent.influencer_matcher_agent.state import State
from match.ai_model.agent.influencer_matcher_agent.structured_output import (
    RelevantIndustries,
    TableDevisionPlan,
    UserQueryExtraction,
)
from match.config import Settings


async def determine_product_type(state: State, llm: BaseLanguageModel) -> dict:
    """
    Determine the product type based on the input.
    """
    # Define the list of allowed industries that match the product's type
    logger.info("Determining product type...")

    match_product_template = ChatPromptTemplate.from_messages(
        [
            ("system", match_product_system_prompt),
            ("user", match_product_user_prompt),
        ]
    )
    match_product_chain = match_product_template | llm.with_structured_output(RelevantIndustries).with_fallbacks(
        [RunnableLambda(lambda x: RelevantIndustries(industries=["Fashion", "Beauty", "Travel"]))]
    )

    # Use cast to tell the type checker that the result is RelevantIndustries
    result = cast(
        RelevantIndustries,
        await match_product_chain.ainvoke(
            {
                "input": state["input"],
            }
        ),
    )

    product_type_list = result.industries

    return {
        "product_type": product_type_list,
    }


async def check_total_num_influencers(state: State, settings: Settings, session_factory: AsyncSession) -> dict:
    """
    Check the total number of influencers in the database.
    """
    logger.info("Checking total number of influencers...")
    # Check if the product type is empty
    if not state["product_type"]:
        error_msg = "Product type is empty. Cannot check total number of influencers."
        raise ValueError(error_msg)

    # Get the product type from the state
    product_type = state["product_type"]
    brand_id = state["brand_id"]

    num_influencers = await InfluencerStats(settings, session_factory).invoke(
        {"industries": product_type, "brand_id": brand_id}
    )

    # Update the state with the total number of influencers

    return {
        "total_num_influencers": num_influencers[1],
        "influencer_info_table": num_influencers[0],
        "brand_creators: ": num_influencers[2],
        # Workaround because cannot assign in conditional edge. Will be re-assigned in the plan_summary node.
        # But this can lead to implicit things.
        # To do: Find a better way to do this
        "rec_plan_summary": "Con số yêu cầu của bạn quá cao so với số lượng influencer hiện có nên bọn mình không thể tạo plan được. Vui lòng điều chỉnh lại hoặc liên hệ với team nhé!",  # noqa: E501
    }


async def plan_generation(state: State, llm: BaseLanguageModel) -> dict:
    """
    Generate a plan based on the input and product type.
    """
    logger.info("Generating plan...")

    plan_generation_chain = (
        ChatPromptTemplate.from_messages(
            [
                ("system", plan_generation_system_prompt),
                MessagesPlaceholder(variable_name="messages"),
                (
                    "human",
                    "Remember to ensure to re-include influencers division table and campaign strategy (very important) in the plan.",  # noqa: E501
                ),
            ]
        )
        | llm
    )

    if len(state["generate_plan_messages"]) == 0:
        logger.debug("No messages in generate_plan_messages, adding initial message.")
        # If there are no messages, add the initial message
        state["generate_plan_messages"].append(
            HumanMessage(
                content=plan_generation_user_prompt.format(
                    input=state["input"],
                    brand_template=state["brand_template"],
                    num_influencers=state["total_num_influencers"],
                    additional_instructions=state.get("additional_instructions", ""),
                    product_type=state["product_type"],
                    expected_num_influencers=state["extracted_input_metadata"].number_of_video_or_koc,
                    initial_budget_plan=state["extracted_input_metadata"].initial_budget_plan,
                )
            )
        )
    if "The plan is good".strip().lower() in state["generate_plan_messages"][-1].content.strip().lower():
        logger.info("Plan is good, no need to generate a new one.")
        return {"Plan generation status": "Finished"}
    generate_plan_message = await plan_generation_chain.ainvoke(
        {
            "messages": state["generate_plan_messages"],
        }
    )

    return {
        "generate_plan": [generate_plan_message.content],
        "generate_plan_messages": [generate_plan_message],
    }


async def plan_reflection(state: State, llm: BaseLanguageModel) -> dict:
    """
    Reflect on the generated plan and provide feedback.
    """
    logger.info("Reflecting on the plan...")

    def format_msg(msg: str) -> str:
        cleaned = re.sub(r"<think>.*?</think>", "", msg, flags=re.DOTALL)

        # Now match everything else
        matches = re.findall(r"[^<]+", cleaned)
        result = " ".join(matches).strip()
        return result

    for msg in state["generate_plan_messages"]:
        msg.content = format_msg(msg.content)

    reflect_chain = (
        ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    plan_reflection_system_prompt,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )
        | llm
    )

    cls_map = {"ai": HumanMessage, "human": AIMessage}

    translated = [state["generate_plan_messages"][0]] + [
        cls_map[msg.type](content=msg.content) for msg in state["generate_plan_messages"][1:]
    ]

    reflection_message = await reflect_chain.ainvoke({"messages": translated})

    return {
        "generate_plan_messages": [HumanMessage(content=reflection_message.content)],
    }


async def extract_table_devision(state: State, llm: BaseLanguageModel) -> dict:
    """
    Extract the table division from the generated plan.
    """
    logger.info("Extracting table division...")

    # Extract the table division from the generated plan
    rec_plan = state["generate_plan"][-1]

    # Convert the table division to a pandas dataframe
    table_devision_extraction_prompt_template = PromptTemplate.from_template(
        table_devision_extraction_prompt,
    )

    table_devision_extraction_chain = table_devision_extraction_prompt_template | llm.with_structured_output(
        TableDevisionPlan
    )

    # Use cast to tell the type checker that the result is TableDevisionPlan
    result = cast(
        TableDevisionPlan,
        await table_devision_extraction_chain.ainvoke(
            {
                "plan_str": rec_plan,
            }
        ),
    )
    return {
        "rec_table_division": result,
    }


def get_influencer_table(state: State) -> dict:
    """
    Get influencer recommendation with priority given to brand creators.
    Brand creators are included first (no sorting), remaining are selected from the pool sorted by seller and revenue.
    """
    logger.info("Getting influencer recommendation...")

    rec_table_division = state["rec_table_division"]

    if not rec_table_division.table_available:
        error_msg = "No table available for influencer recommendation."
        logger.error(error_msg)
        raise ValueError(error_msg)

    rec_influencer_plan = rec_table_division.plans
    creator_df = state["influencer_info_table"]
    brand_creators = state.get("brand_creators", None)

    result_df = pd.DataFrame()

    for segment_plan in rec_influencer_plan:
        lower = segment_plan.segment.lower_bound
        upper = segment_plan.segment.upper_bound
        count = segment_plan.number

        # Filter pool for this segment
        segment_df = creator_df[(creator_df["total_followers"] >= lower) & (creator_df["total_followers"] < upper)]

        if segment_df.empty:
            logger.info(f"Warning: No data found in segment {lower}-{upper}")
            continue

        segment_df = segment_df.copy()
        segment_df["has_seller"] = segment_df["seller_id"].notnull().astype(int)

        brand_segment_df = pd.DataFrame()
        if brand_creators is not None:
            brand_segment_df = segment_df[segment_df["id"].isin(set(brand_creators["creators.id"]))]

        # No sorting for brand creators — include all
        num_from_brand = len(brand_segment_df)
        num_remaining = count - num_from_brand

        # Remove brand creators from general pool
        non_brand_segment_df = (
            segment_df[~segment_df["id"].isin(brand_segment_df["id"])] if not brand_segment_df.empty else segment_df
        )
        non_brand_sample = pd.DataFrame()
        if num_remaining > 0:
            non_brand_sample = non_brand_segment_df.sort_values(
                by=["has_seller", "revenue"], ascending=[False, False]
            ).head(num_remaining)

        segment_sample = pd.concat([brand_segment_df, non_brand_sample], ignore_index=True).drop(columns="has_seller")

        available_total = len(segment_df)
        if available_total < count:
            logger.info(
                f"Note: Only {available_total} total records available in segment {lower}-{upper} (requested {count})"
            )
        logger.info(
            f"Segment {lower}-{upper}: selected {len(segment_sample)} "
            f"(brand: {len(brand_segment_df)}, others: {len(non_brand_sample)})"
        )

        result_df = pd.concat([result_df, segment_sample], ignore_index=True)

    logger.info(f"Selected {len(result_df)} records across all segments")
    return {"rec_influencer": result_df.to_dict(orient="records")}


async def get_input_metadata(state: State, llm: BaseLanguageModel) -> dict:
    """
    Get input metadata
    """
    logger.info("Extracting input metadata...")

    extracted_input_metadata_chain = PromptTemplate.from_template(
        input_metadata_extraction_prompt
    ) | llm.with_structured_output(UserQueryExtraction)

    # Use cast to tell the type checker that the result is UserQueryExtraction
    result = cast(
        UserQueryExtraction,
        await extracted_input_metadata_chain.ainvoke(
            {
                "requirements": state["input"],
                "description": state.get("description", ""),
            }
        ),
    )

    return {"extracted_input_metadata": result}


async def plan_summary(state: State, llm: BaseLanguageModel) -> dict:
    """
    Summarize the plan
    """
    logger.info("Summarizing the plan...")

    plan_summary_chain = PromptTemplate.from_template(plan_summary_prompt) | llm

    result = await plan_summary_chain.ainvoke(
        {
            "plan_str": state["generate_plan"][-1],
        }
    )

    return {"rec_plan_summary": result.content}
