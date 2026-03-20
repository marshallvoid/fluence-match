from typing import Protocol


class EnqueueRunService(Protocol):
    async def __call__(
        self,
        *,
        payload: dict,
    ) -> None:
        raise NotImplementedError
