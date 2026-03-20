import hashlib
import json
from functools import wraps
from inspect import Parameter, iscoroutinefunction
from typing import Any, Awaitable, Callable, List, Optional, ParamSpec, TypeVar, Union, cast, get_type_hints

from fastapi import BackgroundTasks, Request, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.dependencies.utils import (
    get_typed_signature,
)
from fastapi.encoders import jsonable_encoder
from redis.asyncio import ConnectionPool, Redis

from match.utils.func import augment_annotations, augment_signature, locate_param

P = ParamSpec("P")
R = TypeVar("R")


def cache_api(  # noqa: C901
    use_identifier: bool = False,
    ttl: int = 60,
    injected_dependency_namespace: str = "__fastapi_cache",
) -> Callable:
    """
    A decorator that adds caching to API response.

    :param ttl: Cache Time-to-live in seconds (optional).
    :param use_identifier: Whether to use api_key identifier in cache key (optional).
    :param injected_dependency_namespace: Namespace for injected dependencies (optional).
    """

    injected_request = Parameter(
        name=f"{injected_dependency_namespace}_request",
        annotation=Request,
        kind=Parameter.KEYWORD_ONLY,
    )

    injected_background_tasks = Parameter(
        name=f"{injected_dependency_namespace}_background_tasks",
        annotation=BackgroundTasks,
        kind=Parameter.KEYWORD_ONLY,
    )

    async def _save_to_cache(redis_pool: ConnectionPool, cache_key: str, data: Any, ttl: int) -> None:
        # Convert the data into a serializable format using jsonable_encoder
        serializable_data = jsonable_encoder(data)

        async with Redis(connection_pool=redis_pool) as redis:
            await redis.setex(name=f"match:fastapi_cache:{cache_key}", time=ttl, value=json.dumps(serializable_data))

    def _uncacheable(request: Optional[Request]) -> bool:
        """Determine if this request should not be cached

        Returns true if:
        - This is not a GET request
        - The request has a Cache-Control header with a value of "no-store"

        """
        if request is None:
            return True
        if request.method != "GET":
            return True
        return request.headers.get("Cache-Control") == "no-store"

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[Union[R, Response]]]:
        to_inject: List[Parameter] = []
        wrapped_signature = get_typed_signature(func)
        wrapped_annotations = get_type_hints(func, include_extras=True)
        request_param = locate_param(wrapped_signature, injected_request, to_inject)
        background_tasks_param = locate_param(wrapped_signature, injected_background_tasks, to_inject)

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Union[R, Response]:
            async def ensure_async_func(*args: P.args, **kwargs: P.kwargs) -> R:
                """Run cached sync functions in thread pool just like FastAPI."""
                kwargs.pop(background_tasks_param.name, None)
                kwargs.pop(request_param.name, None)

                if iscoroutinefunction(func):
                    # async, return as is
                    return await func(*args, **kwargs)
                else:
                    # sync, wrap in thread and return async
                    return await run_in_threadpool(func, *args, **kwargs)  # type: ignore[arg-type]

            copy_kwargs = kwargs.copy()
            request: Optional[Request] = copy_kwargs.pop(request_param.name, None)  # type: ignore[assignment]
            background_tasks: Optional[BackgroundTasks] = copy_kwargs.pop(background_tasks_param.name, None)  # type: ignore[assignment]

            if _uncacheable(request=request) or not request:
                return await ensure_async_func(*args, **kwargs)

            # Get optional api_key info
            user_identifier = (
                f"&api_key={api_key}" if (api_key := request.headers.get("X-API-Key")) and use_identifier else ""
            )
            # Access the DI container and Redis connection
            container = request.app.state.dishka_container
            async with container() as request_container:
                redis_pool = await request_container.get(ConnectionPool)
                async with Redis(connection_pool=redis_pool) as redis:
                    # Generate a cache key using request path, query params, and user_id (if present)
                    query_params = request.query_params.items()
                    query_string = "&".join(f"{key}={value}" for key, value in sorted(query_params))
                    key_raw = f"{request.url.path}?{query_string}{user_identifier}"
                    cache_key = hashlib.sha256(key_raw.encode()).hexdigest()

                    # Attempt to retrieve data from Redis
                    cached_data = await redis.get(f"match:fastapi_cache:{cache_key}")
                    if cached_data:
                        return cast(R, json.loads(cached_data))

                    # Execute the original function
                    response = await ensure_async_func(*args, **kwargs)

                    # Save the result in the cache after the response is completed
                    if response and background_tasks:
                        background_tasks.add_task(
                            _save_to_cache,
                            redis_pool=redis_pool,
                            cache_key=cache_key,
                            data=response,
                            ttl=ttl,
                        )

                    return response

        wrapper.__signature__ = augment_signature(wrapped_signature, *to_inject)  # type: ignore[attr-defined]
        wrapper.__annotations__ = augment_annotations(wrapped_annotations, *to_inject)
        return wrapper

    return decorator
