import asyncio

from dishka import AsyncContainer

from match.config import Settings
from match.main.worker.factory import WorkerFactory


def run_worker(settings: Settings, container: AsyncContainer) -> None:
    factory = WorkerFactory(container, settings)
    app = factory.make()

    asyncio.run(app.run())
