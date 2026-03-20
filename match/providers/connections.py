from typing import AsyncIterator

from dishka import Provider, Scope, provide
from loguru import logger
from openai import OpenAI
from redis.asyncio import ConnectionPool
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from match.config import Settings
from match.infrastructure.persistence.nats.client import NatsClient


class ConnectionsProvider(Provider):
    @provide(scope=Scope.APP)
    async def redis_pool(self, settings: Settings) -> AsyncIterator[ConnectionPool]:
        assert settings.redis_url, "Redis URL is required"
        connection_pool: ConnectionPool = ConnectionPool.from_url(
            url=settings.redis_url,
            max_connections=settings.redis_max_connections,
        )

        yield connection_pool
        await connection_pool.disconnect()

    @provide(scope=Scope.APP)
    async def provide_nats_client(self, settings: Settings) -> AsyncIterator[NatsClient]:
        assert settings.nats_url
        nats_client = NatsClient(settings.nats_url)
        yield nats_client
        logger.info("Closing NATS client connection")
        await nats_client.close()

    @provide(scope=Scope.REQUEST)
    def openai_client(self, settings: Settings) -> OpenAI:
        return OpenAI(
            api_key=settings.openai_api_key,
        )

    @provide(scope=Scope.APP)
    async def sqlalchemy_session_factory(self, settings: Settings) -> AsyncSession:
        connection_str = f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_uri}/{settings.postgres_db}"
        async_engine: AsyncEngine = create_async_engine(
            connection_str, pool_size=10, max_overflow=20, pool_timeout=30, pool_recycle=1800
        )
        # Test the connection
        try:
            async with async_engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            logger.info("PostgreSQL connection successful")
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL: {e}")
            error_msg = "Failed to connect to PostgreSQL"
            raise ConnectionError(error_msg)

        async_session_factory = async_sessionmaker(
            bind=async_engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

        return async_session_factory  # type: ignore
