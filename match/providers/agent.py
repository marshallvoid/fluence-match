from dishka import Provider, Scope, provide
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from match.ai_model.agent.influencer_matcher_agent.graph import InfluencerMatcherGraph
from match.config import Settings


class AgentProvider(Provider):
    scope = Scope.REQUEST

    @provide(scope=Scope.APP)
    def get_influencer_matcher_agent(
        self,
        settings: Settings,
        session_factory: AsyncSession,
        openai_llm: ChatOpenAI,
        gemini_llm: ChatGoogleGenerativeAI,
    ) -> InfluencerMatcherGraph:
        """
        Get the influencer matcher agent.
        """
        # Create the influencer matcher graph
        return InfluencerMatcherGraph(
            settings=settings,
            session_factory=session_factory,
            openai_llm=openai_llm,
            gemini_llm=gemini_llm,
            claude_llm=None,
        )
