from dishka import Provider, Scope, provide

from match.config import Settings
from match.infrastructure.api_key_manager.encrypt_computer import EncryptComputer


class ComputersProvider(Provider):
    @provide(scope=Scope.APP)
    def encrypt_computer(
        self,
        settings: Settings,
    ) -> EncryptComputer:
        return EncryptComputer(
            secret_key=settings.secret_key,
        )
