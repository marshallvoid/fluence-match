import hashlib
from typing import Annotated

from fastapi import Header, HTTPException, Request, status

from match.infrastructure.api_key_manager.api_key_manager import APIKeyManager
from match.infrastructure.rate_limit import RateLimitManager


class APIKeyAuthentication:
    """
    API Key Validation and Rate Limiting Dependency
    """

    def __init__(self, requests_limit: int = 10, time_window: int = 10) -> None:
        """
        :param requests_limit: Number of requests allowed in the time window
        :param time_window: Time window in seconds
        """
        self.requests_limit = requests_limit
        self.time_window = time_window

    async def __call__(self, request: Request, api_key: Annotated[str, Header(alias="X-API-Key")]) -> str:
        container = request.app.state.dishka_container
        async with container() as request_container:
            api_key_manager: APIKeyManager = await request_container.get(APIKeyManager)
            rate_limit_manager: RateLimitManager = await request_container.get(RateLimitManager)

            # Hash the API key
            hash_api_key = hashlib.sha256(api_key.encode()).hexdigest()
            try:
                payload = await api_key_manager.verify(api_key)
                # Check the API Key Quota Limit
                if await rate_limit_manager.check(
                    key=f"match:api_rate_limit:{hash_api_key}",
                    times=payload.rate_limit,
                    milliseconds=payload.rate_limit_type.rate_limit_milliseconds,
                ):
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate Limit Exceeded, Try again later!"
                    )

                # Check the Endpoint-specific Rate Limit
                if await rate_limit_manager.check(
                    key=f"match:api_rate_limit:{request.url.path}:{hash_api_key}",
                    times=self.requests_limit,
                    milliseconds=self.time_window * 1000,
                ):
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate Limit Exceeded, Try again later!"
                    )
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

            return hash_api_key
