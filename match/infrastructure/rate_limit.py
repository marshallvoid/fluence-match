from typing import Annotated

from pydantic import Field
from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import NoScriptError


class RateLimitManager:
    lua_sha: str | None = None

    def __init__(
        self,
        redis_pool: ConnectionPool,
    ):
        self._redis_pool = redis_pool

    async def load_script(
        self,
    ) -> None:
        lua_script = self.get_lua_script()
        async with Redis(connection_pool=self._redis_pool) as redis:
            self.lua_sha = await redis.script_load(lua_script)

    def get_lua_script(self) -> str:
        return """
            local key = KEYS[1]
            local limit = tonumber(ARGV[1])
            local expire_time = ARGV[2]

            local current = tonumber(redis.call('get', key) or "0")
            if current > 0 then
             if current + 1 > limit then
             return redis.call("PTTL",key)
             else
                    redis.call("INCR", key)
             return 0
             end
            else
                redis.call("SET", key, 1,"px",expire_time)
             return 0
            end
        """

    async def _check_from_redis_script(
        self,
        key: str,
        times: Annotated[int, Field(ge=0)],
        milliseconds: Annotated[int, Field(ge=-1)],
    ) -> int:
        async with Redis(connection_pool=self._redis_pool) as redis:
            return await redis.evalsha(
                self.lua_sha,
                1,
                key,
                times,
                milliseconds,
            )

    async def check(
        self,
        key: str,
        times: Annotated[int, Field(ge=0)],
        milliseconds: Annotated[int, Field(ge=-1)],
    ) -> bool:
        try:
            if not self.lua_sha:
                await self.load_script()
            result = await self._check_from_redis_script(key, times, milliseconds)
        except NoScriptError:
            await self.load_script()
            result = await self._check_from_redis_script(key, times, milliseconds)

        if result != 0:
            return True
        return False
