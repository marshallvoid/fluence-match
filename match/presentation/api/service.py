from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from redis.asyncio import ConnectionPool, Redis

from match.application.commands.run_service import RunServiceCommand
from match.application.common.task_queue.run_service import EnqueueRunService
from match.schemas.enums.service import ServiceSessionStatus

router = APIRouter(prefix="/service")


@router.post(
    "/trigger",
    response_model=dict,
    summary="Trigger a service execution",
    description="This endpoint triggers a service execution by enqueuing a task and storing its status in Redis.",
)
@inject
async def trigger_run_service(
    *,
    redis_pool: Annotated[ConnectionPool, FromDishka()],  # type: ignore
    enqueue_run_service: Annotated[EnqueueRunService, FromDishka()],  # type: ignore
    command: RunServiceCommand,
) -> JSONResponse:
    async with Redis(connection_pool=redis_pool) as redis:
        await redis.hset(
            f"match:service_sessions:{command.session_id}",
            mapping={
                "status": ServiceSessionStatus.PENDING,
            },
        )

    # Enqueue Run Service
    await enqueue_run_service(payload=command.model_dump())
    return JSONResponse(status_code=status.HTTP_200_OK, content={"session_id": command.session_id})


@router.get(
    "/session/{session_id}",
    response_model=dict,
    summary="Get service session status",
    description="This endpoint retrieves the status and data of a service session from Redis.",
)
@inject
async def get_service_session(
    *,
    redis_pool: Annotated[ConnectionPool, FromDishka()],  # type: ignore
    session_id: str,
) -> JSONResponse:
    async with Redis(connection_pool=redis_pool) as redis:
        if not (service_session_payload := await redis.hgetall(f"match:service_sessions:{session_id}")):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND, content={"message": f"ServiceSession[{session_id}] not found"}
            )

        # Decode byte values to string
        service_session_payload = {k.decode(): v.decode() for k, v in service_session_payload.items()}  # type: ignore

        # Truncate the lifetime of session if it is finished
        if service_session_payload.get("status") in ServiceSessionStatus.finished_statuses():  # type: ignore
            await redis.expire(
                name=f"match:service_sessions:{session_id}",
                time=60 * 60 * 5,  # 5 hours
            )

    return JSONResponse(status_code=status.HTTP_200_OK, content=service_session_payload)
