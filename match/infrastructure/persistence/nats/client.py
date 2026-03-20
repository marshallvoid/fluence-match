import json

from nats.aio.client import Client as NATS  # noqa: N814


class NatsClient:
    def __init__(self, url: str):
        self.url = url
        self.nc = NATS()

    async def connect(self) -> None:
        await self.nc.connect(
            servers=[self.url],
            max_reconnect_attempts=60,
            connect_timeout=30,
            reconnect_time_wait=2,
            max_outstanding_pings=2,
        )

    async def publish(self, subject: str, message: dict, drain: bool = True) -> None:
        await self.connect()
        if self.nc.is_connected:
            json_message = json.dumps(message)
            await self.nc.publish(subject, json_message.encode())
            await self.nc.flush()
            if drain:
                await self.nc.drain()

    async def close(self) -> None:
        if self.nc.is_connected:
            await self.nc.flush()
            await self.nc.drain()
            await self.nc.close()
