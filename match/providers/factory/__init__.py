from dishka import AsyncContainer, make_async_container

from match.config import Settings
from match.providers.agent import AgentProvider
from match.providers.computers import ComputersProvider
from match.providers.configs import ConfigsProvider
from match.providers.connections import ConnectionsProvider
from match.providers.embeddings import EmbeddingsProvider
from match.providers.llm import LLMProvider
from match.providers.managers import ManagersProvider
from match.providers.services import ServicesProvider
from match.providers.task_queue import TaskQueueAdaptersProvider


def make_container(settings: Settings) -> AsyncContainer:
    container = make_async_container(
        ConfigsProvider(settings=settings),
        ConnectionsProvider(),
        LLMProvider(),
        EmbeddingsProvider(),
        ComputersProvider(),
        ManagersProvider(),
        TaskQueueAdaptersProvider(),
        ServicesProvider(),
        AgentProvider(),
    )
    return container
