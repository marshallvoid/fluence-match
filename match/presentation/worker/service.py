import json
from datetime import datetime, timezone
from typing import Annotated

from dishka import AsyncContainer, FromDishka
from dishka.integrations.faststream import inject
from fastapi.encoders import jsonable_encoder
from loguru import logger
from redis.asyncio import ConnectionPool, Redis

from match.application.commands.run_service import RunServiceCommand
from match.core.task.service import run_service
from match.schemas.enums.service import ServiceSessionStatus


@inject
async def apply_service(
    container: Annotated[AsyncContainer, FromDishka()],
    redis_pool: Annotated[ConnectionPool, FromDishka()],
    command: RunServiceCommand,
) -> None:
    async with Redis(connection_pool=redis_pool) as redis:
        service_session_key = f"match:service_sessions:{command.session_id}"

        # Fetch session payload
        service_session_payload = await redis.hgetall(service_session_key)
        if not service_session_payload:
            msg = f"Service Session[{command.session_id}] not found"
            raise ValueError(msg)

        # Update session status
        await redis.hset(
            service_session_key,
            mapping={
                "status": ServiceSessionStatus.IN_PROGRESS,
                "msg": f"[Running] {command.service}:{command.func} - {datetime.now(tz=timezone.utc)}",
            },
        )

        try:
            # Execute the service function
            result = await run_service(
                ctx={"AsyncContainer": container},
                service_name=command.service_name,
                func_name=command.func,
                params=command.params,
            )

            # Update session with success result
            await redis.hset(
                service_session_key,
                mapping={
                    "status": ServiceSessionStatus.COMPLETED,
                    "msg": f"[Completed] - {datetime.now(tz=timezone.utc)}",
                    "data": json.dumps(jsonable_encoder(result)),
                },
            )
        except Exception as err:
            logger.exception(f"Error Running Service [{command.service}.{command.func}]: {err}")
            await redis.hset(
                service_session_key,
                mapping={
                    "status": ServiceSessionStatus.FAILED,
                    "msg": f"[Error] {err}",
                },
            )
