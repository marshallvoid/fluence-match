import functools

from langchain.base_language import BaseLanguageModel
from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from match.ai_model.agent.influencer_matcher_agent.conditional_edge import (
    should_continue_generate_plan,
    should_generate_plan,
)
from match.ai_model.agent.influencer_matcher_agent.nodes import (
    check_total_num_influencers,
    determine_product_type,
    extract_table_devision,
    get_influencer_table,
    get_input_metadata,
    plan_generation,
    plan_reflection,
    plan_summary,
)
from match.ai_model.agent.influencer_matcher_agent.state import State
from match.config import Settings


class InfluencerMatcherGraph:
    """
    Influencer Matcher Graph
    """

    def __init__(
        self,
        settings: Settings,
        session_factory: AsyncSession,
        openai_llm: BaseLanguageModel,
        gemini_llm: BaseLanguageModel,
        claude_llm: BaseLanguageModel | None,
    ) -> None:
        self.settings = settings
        self.session_factory = session_factory
        self.graph = StateGraph(State)
        self.openai_llm = openai_llm
        self.gemini_llm = gemini_llm
        self.claude_llm = claude_llm
        self._build_graph()

    def _add_nodes(self) -> None:
        """
        Add nodes to the graph.
        """
        self.graph.add_node("get_input_metadata", functools.partial(get_input_metadata, llm=self.openai_llm))
        self.graph.add_node("determine_product_type", functools.partial(determine_product_type, llm=self.openai_llm))
        self.graph.add_node(
            "check_total_num_influencers",
            functools.partial(
                check_total_num_influencers, settings=self.settings, session_factory=self.session_factory
            ),
        )
        self.graph.add_node("plan_generation", functools.partial(plan_generation, llm=self.openai_llm))
        self.graph.add_node("plan_reflection", functools.partial(plan_reflection, llm=self.openai_llm))
        self.graph.add_node("plan_summary", functools.partial(plan_summary, llm=self.openai_llm))
        self.graph.add_node("extract_table_devision", functools.partial(extract_table_devision, llm=self.openai_llm))
        self.graph.add_node("get_creators", get_influencer_table)

    def _add_edges(self) -> None:
        """
        Add edges to the graph.
        """
        self.graph.add_edge(START, "get_input_metadata")
        self.graph.add_edge("get_input_metadata", "determine_product_type")
        self.graph.add_edge("determine_product_type", "check_total_num_influencers")
        self.graph.add_conditional_edges("check_total_num_influencers", should_generate_plan)
        self.graph.add_conditional_edges("plan_generation", should_continue_generate_plan)
        self.graph.add_edge("plan_reflection", "plan_generation")
        self.graph.add_edge("extract_table_devision", "get_creators")
        self.graph.add_edge("plan_summary", END)
        self.graph.add_edge("get_creators", END)

    def _build_graph(self) -> None:
        """
        Build the graph.
        """
        self._add_nodes()
        self._add_edges()
        self.compiled_graph = self.graph.compile()

    async def invoke(
        self,
        input_data: str,
        description: str | None = None,
        brand_template: dict | None = None,
        brand_id: str | None = None,
    ) -> dict:
        """
        Invoke the graph with the given text.
        """
        return await self.compiled_graph.ainvoke(
            {
                "input": input_data,
                "description": description,
                "brand_template": brand_template,
                "brand_id": brand_id,
            }
        )
