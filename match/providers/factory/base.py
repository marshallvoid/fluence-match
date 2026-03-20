from typing import Protocol, TypeVar

from match.config import Settings

_H = TypeVar("_H", covariant=True)


class LLMFactory(Protocol[_H]):
    _settings: Settings

    def __call__(self, temperature: float = 0.8, model: str | None = None) -> _H:
        raise NotImplementedError
