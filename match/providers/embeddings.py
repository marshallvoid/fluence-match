from dishka import Provider, Scope, provide
from langchain_openai import OpenAIEmbeddings

from match.config import Settings


class EmbeddingsProvider(Provider):
    @provide(scope=Scope.APP)
    def openai_embeddings(self, settings: Settings) -> OpenAIEmbeddings:
        return OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            openai_api_key=settings.openai_api_key,
        )
