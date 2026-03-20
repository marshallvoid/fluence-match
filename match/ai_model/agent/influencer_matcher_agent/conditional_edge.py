from typing import Any

from langgraph.graph import END
from loguru import logger

from match.ai_model.agent.influencer_matcher_agent.state import State


def should_continue_generate_plan(state: State) -> Any:
    if len(state["generate_plan_messages"]) > 6:
        # End after 3 iterations
        logger.info("End of plan generation because of too many iterations.")
        return ["extract_table_devision", "plan_summary"]
    if (
        len(state["generate_plan_messages"]) > 1
        and "The plan is good".strip().lower() in state["generate_plan_messages"][-1].content.strip().lower()
    ):
        logger.info("Plan is good, no need to generate a new one.")
        return ["extract_table_devision", "plan_summary"]

    return "plan_reflection"


def should_generate_plan(state: State) -> Any:
    expected_num_influencers = state["extracted_input_metadata"].number_of_video_or_koc
    expected_budget = state["extracted_input_metadata"].initial_budget_plan
    total_num_influencers = len(state["influencer_info_table"])
    logger.info(f"Expected {expected_num_influencers} influencers, found {total_num_influencers}.")

    # Check for invalid inputs
    if expected_num_influencers == 0 or expected_num_influencers is None:
        logger.info("No influencers expected, cannot generate plan.")
        state["rec_plan_summary"] = (
            "Không có số lượng influencer được yêu cầu, nên bọn mình không thể tạo plan được. Vui lòng điều chỉnh lại hoặc liên hệ với team nhé!"  # noqa: E501"
        )
        return END

    if expected_budget == 0:
        logger.info("No budget expected, cannot generate plan.")
        state["rec_plan_summary"] = (
            "Không có ngân sách được yêu cầu, nên bọn mình không thể tạo plan được. Vui lòng điều chỉnh lại hoặc liên hệ với team nhé!"  # noqa: E501"
        )
        return END

    # Check if database has sufficient influencers (at least 5% of expected)
    min_required_ratio = 0.05
    if total_num_influencers < expected_num_influencers * min_required_ratio:
        logger.info("DB has too few influencers, cannot generate plan.")
        state["rec_plan_summary"] = (
            "Con số yêu cầu của bạn quá cao so với số lượng influencer hiện có nên bọn mình không thể tạo plan được. Vui lòng điều chỉnh lại hoặc liên hệ với team nhé!"  # noqa: E501
        )
        return END

    return "plan_generation"
