from dishka import AsyncContainer
from dishka.integrations.faststream import setup_dishka
from faststream import FastStream
from faststream.nats import NatsBroker

from match.config import Settings, get_settings
from match.core.logging import init_logger
from match.presentation.worker.router import router


class WorkerFactory:
    def __init__(self, container: AsyncContainer, settings: Settings | None = None) -> None:
        if settings is None:
            self.settings = get_settings()
        else:
            self.settings = settings
        self.container = container

    def get_nats_url(self) -> str:
        assert self.settings.nats_url is not None, "NATS URL is not set"
        return self.settings.nats_url

    def make(self) -> FastStream:
        broker = NatsBroker(servers=self.get_nats_url())
        broker.include_router(router)
        app = FastStream(broker)

        setup_dishka(self.container, app)
        init_logger(debug=self.settings.debug)
        return app
