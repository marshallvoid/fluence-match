from typing import ClassVar

from dishka import Provider, Scope, provide
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from llama_index.llms.litellm import LiteLLM
from pydantic import SecretStr

from match.config import Settings
from match.providers.factory.base import LLMFactory
from match.providers.factory.llm import ChatOpenAIFactory


class ClaudeLiteLLMLLamaIndex(LiteLLM):
    internal_model_name: ClassVar[str] = "claude-llama-index-litellm"


class LLMProvider(Provider):
    @provide(scope=Scope.APP)
    def chat_openai(self, settings: Settings) -> ChatOpenAI:
        if not settings.openai_model or not settings.openai_api_key:
            msg = "OpenAI model and API key must be provided in settings"
            raise ValueError(msg)

        return ChatOpenAI(
            model=settings.openai_model,
            temperature=0.8,
            max_retries=2,
            api_key=SecretStr(settings.openai_api_key),
        )

    @provide(scope=Scope.REQUEST)
    def chat_openai_factory(self, settings: Settings) -> LLMFactory[ChatOpenAI]:
        return ChatOpenAIFactory(
            settings=settings,
        )

    @provide(scope=Scope.APP)
    def chat_gemini(self, settings: Settings) -> ChatGoogleGenerativeAI:
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            api_key=settings.gemini_api_key,
        )

    @provide(scope=Scope.APP)
    def chat_claude(self, settings: Settings) -> ChatAnthropic:
        return ChatAnthropic(
            model=settings.anthropic_model,
            temperature=0.1,
            api_key=settings.anthropic_api_key,
        )
