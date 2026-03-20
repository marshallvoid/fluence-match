from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from match.config import Settings


class ChatOpenAIFactory:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def __call__(self, temperature: float = 0.8, model: str | None = None) -> ChatOpenAI:
        model = model or self._settings.openai_model
        api_key = SecretStr(self._settings.openai_api_key)
        if not model or not api_key:
            msg = "OpenAI model and API key must be provided in settings."
            raise ValueError(msg)

        return ChatOpenAI(model=model, temperature=temperature, max_retries=2, api_key=api_key)
