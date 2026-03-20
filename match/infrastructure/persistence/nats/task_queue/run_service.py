from faststream.nats import NatsBroker

from match.config import Settings
from match.infrastructure.persistence.nats.task_queue.base import EnqueuesWithNats


class EnqueueRunServiceWithNats(EnqueuesWithNats):
    def __init__(self, settings: Settings) -> None:
        self._topic = "match_apply_service"
        super().__init__(settings)

    async def __call__(self, *, payload: dict) -> None:
        async with NatsBroker(self.get_nats_url()) as br:
            await br.publish(payload, self._topic)
