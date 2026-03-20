import hashlib
import json
import secrets

from fastapi.encoders import jsonable_encoder
from redis.asyncio import ConnectionPool, Redis

from .encrypt_api_key import EncryptAPIKey, RateLimitType
from .encrypt_computer import EncryptComputer

API_KEY_DOES_NOT_EXIST_OR_EXPIRED = "API key does not exist or has expired."


class APIKeyManager:
    def __init__(
        self,
        encrypt_computer: EncryptComputer,
        redis_pool: ConnectionPool,
    ) -> None:
        self._encrypt_computer = encrypt_computer
        self._redis_pool = redis_pool
        self._base_redis_key = "match:api_keys"

    async def create(
        self, name: str, rate_limit: int, ttl: int, rate_limit_type: RateLimitType = RateLimitType.MONTH
    ) -> str:
        api_key = f"match_{secrets.token_urlsafe(32)}"
        encrypted_api_key = self._encrypt_computer.encrypt(api_key.encode())
        hash_api_key = hashlib.sha256(api_key.encode()).hexdigest()

        async with Redis(connection_pool=self._redis_pool) as redis:
            await redis.set(
                f"{self._base_redis_key}:{hash_api_key}",
                json.dumps(
                    jsonable_encoder(
                        EncryptAPIKey(
                            name=name,
                            rate_limit=rate_limit,
                            encrypted_api_key=encrypted_api_key,
                            rate_limit_type=rate_limit_type,
                        )
                    )
                ),
                ex=ttl,
            )

        return api_key

    async def verify(self, api_key: str) -> EncryptAPIKey:
        hashed_api_key = hashlib.sha256(api_key.encode()).hexdigest()
        async with Redis(connection_pool=self._redis_pool) as redis:
            api_key_payload = await redis.get(f"{self._base_redis_key}:{hashed_api_key}")
            if not api_key_payload:
                raise ValueError(API_KEY_DOES_NOT_EXIST_OR_EXPIRED)

            return EncryptAPIKey(**json.loads(api_key_payload))
