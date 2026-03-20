from dishka import Provider, Scope, provide
from redis.asyncio import ConnectionPool

from match.infrastructure.api_key_manager.api_key_manager import APIKeyManager
from match.infrastructure.api_key_manager.encrypt_computer import EncryptComputer
from match.infrastructure.rate_limit import RateLimitManager


class ManagersProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def api_key_manager(
        self,
        redis_pool: ConnectionPool,
        encrypt_computer: EncryptComputer,
    ) -> APIKeyManager:
        return APIKeyManager(
            encrypt_computer=encrypt_computer,
            redis_pool=redis_pool,
        )

    @provide(scope=Scope.REQUEST)
    def rate_limit_manager(
        self,
        redis_pool: ConnectionPool,
    ) -> RateLimitManager:
        return RateLimitManager(
            redis_pool=redis_pool,
        )
