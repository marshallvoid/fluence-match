from dishka import Provider, Scope, provide
from redis.asyncio import ConnectionPool

from match.ai_model.agent.influencer_matcher_agent.graph import InfluencerMatcherGraph
from match.config import Settings
from match.services.influencer_matching import InfluencerMatcherService


class ServicesProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def influencer_matcher_service(
        self, graph: InfluencerMatcherGraph, redis_pool: ConnectionPool, settings: Settings
    ) -> InfluencerMatcherService:
        """
        This method provides the influencer matcher service.
        """
        return InfluencerMatcherService(graph, redis_pool, settings)
