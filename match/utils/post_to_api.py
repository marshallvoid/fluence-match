from typing import Any, Dict

import aiohttp
from aiohttp import ContentTypeError


async def post_campaign_result(result: Dict[str, Any], url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Posts the `result` dict to the given URL as JSON.

    :param result: dict to send in the body
    :param url:    endpoint to POST to
    :param timeout: request timeout in seconds
    :returns: the parsed JSON response (or raises)
    """
    # Define a timeout for the request
    request_timeout = aiohttp.ClientTimeout(total=timeout)

    async with aiohttp.ClientSession(timeout=request_timeout) as session:
        # You can add custom headers if needed, e.g. auth tokens
        headers = {
            "Content-Type": "application/json",
            # "Authorization": "Bearer YOUR_TOKEN_HERE",
        }

        async with session.post(url, json=result, headers=headers) as resp:
            resp.raise_for_status()  # raise an error for 4xx/5xx responses
            try:
                return await resp.json()
            except ContentTypeError:
                text = await resp.text()
                # you can log the raw text if you like
                return {"status": resp.status, "text": text}
