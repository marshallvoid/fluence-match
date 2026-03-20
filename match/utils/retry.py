import asyncio
import traceback
from typing import Any, Callable

from loguru import logger


def async_retry(max_retries: int = 3, delay: int = 1) -> Callable:
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            traceback_exc = None
            for attempt in range(1, max_retries + 1):
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    last_exception = e
                    traceback_exc = traceback.format_exc()

                    logger.error(f"Attempt {attempt} failed: {str(e)}")
                    traceback.print_exc()
                    await asyncio.sleep(delay)

            # If all attempts fail, log full traceback
            err_msg = f"Failed after {max_retries} attempts:\n{traceback_exc}"
            logger.error(err_msg)
            raise RuntimeError(err_msg) from last_exception

        return wrapper

    return decorator
