from match.config import get_settings
from match.main.api.factory import APIFactory
from match.providers.factory import make_container

settings = get_settings()
container = make_container(settings)
factory = APIFactory(container, settings)
app = factory.make()
