from dishka import AsyncContainer

from match.config import Settings
from match.main.api.factory import APIFactory


def run_api(settings: Settings, container: AsyncContainer, port: int = 8000) -> None:
    factory = APIFactory(container, settings)
    app = factory.make()
    factory.run(app, port=port)
