from match.config import get_settings
from match.main.worker.factory import WorkerFactory
from match.providers.factory import make_container

settings = get_settings()
container = make_container(settings)
factory = WorkerFactory(container, settings)
worker = factory.make()
