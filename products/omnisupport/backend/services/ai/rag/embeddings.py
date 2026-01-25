"""Embedding service for text vectorization."""

import logging
from abc import ABC, abstractmethod

import httpx

from shared.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BaseEmbeddingModel(ABC):
    """Base class for embedding models."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        pass

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]:
        """Generate embedding for a single query."""
        pass


class YandexGPTEmbeddings(BaseEmbeddingModel):
    """YandexGPT Embeddings API."""

    def __init__(self):
        self.api_key = settings.yandex_gpt_api_key
        self.folder_id = settings.yandex_gpt_folder_id
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/textEmbedding"
        self.model_uri = f"emb://{self.folder_id}/text-search-doc/latest"
        self.query_model_uri = f"emb://{self.folder_id}/text-search-query/latest"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for documents."""
        if not self.api_key or not self.folder_id:
            logger.warning("YandexGPT credentials not configured")
            return []

        embeddings = []
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            for text in texts:
                try:
                    response = await client.post(
                        self.api_url,
                        headers=headers,
                        json={
                            "modelUri": self.model_uri,
                            "text": text[:8000],  # Limit text length
                        },
                    )

                    if response.status_code == 200:
                        data = response.json()
                        embeddings.append(data["embedding"])
                    else:
                        logger.error(f"YandexGPT embedding error: {response.text}")
                        embeddings.append([])

                except Exception as e:
                    logger.error(f"Error generating embedding: {e}")
                    embeddings.append([])

        return embeddings

    async def embed_query(self, text: str) -> list[float]:
        """Generate embedding for a search query."""
        if not self.api_key or not self.folder_id:
            return []

        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json={
                        "modelUri": self.query_model_uri,
                        "text": text[:8000],
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["embedding"]
                else:
                    logger.error(f"YandexGPT query embedding error: {response.text}")

            except Exception as e:
                logger.error(f"Error generating query embedding: {e}")

        return []


class GigaChatEmbeddings(BaseEmbeddingModel):
    """GigaChat Embeddings API."""

    def __init__(self):
        self.client_id = settings.gigachat_client_id
        self.client_secret = settings.gigachat_client_secret
        self.auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        self.api_url = "https://gigachat.devices.sberbank.ru/api/v1/embeddings"
        self._access_token: str | None = None

    async def _get_access_token(self) -> str | None:
        """Get or refresh access token."""
        if self._access_token:
            return self._access_token

        if not self.client_id or not self.client_secret:
            return None

        import base64

        credentials = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            try:
                response = await client.post(
                    self.auth_url,
                    headers={
                        "Authorization": f"Basic {credentials}",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    data={"scope": "GIGACHAT_API_PERS"},
                )

                if response.status_code == 200:
                    data = response.json()
                    self._access_token = data["access_token"]
                    return self._access_token
                else:
                    logger.error(f"GigaChat auth error: {response.text}")

            except Exception as e:
                logger.error(f"Error getting GigaChat token: {e}")

        return None

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        token = await self._get_access_token()
        if not token:
            return []

        async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
            try:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "Embeddings",
                        "input": [t[:8000] for t in texts],
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    return [item["embedding"] for item in data["data"]]
                else:
                    logger.error(f"GigaChat embedding error: {response.text}")

            except Exception as e:
                logger.error(f"Error generating GigaChat embeddings: {e}")

        return []

    async def embed_query(self, text: str) -> list[float]:
        """Generate embedding for query."""
        embeddings = await self.embed([text])
        return embeddings[0] if embeddings else []


class LocalEmbeddings(BaseEmbeddingModel):
    """
    Local embeddings using sentence-transformers.
    Fallback when cloud APIs are not configured.
    """

    def __init__(self, model_name: str = "intfloat/multilingual-e5-large"):
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        """Lazy load model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Loaded embedding model: {self.model_name}")
            except ImportError:
                logger.error("sentence-transformers not installed")
                raise
        return self._model

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings locally."""
        try:
            model = self._get_model()
            # Add instruction prefix for e5 models
            prefixed = [f"passage: {t}" for t in texts]
            embeddings = model.encode(prefixed, normalize_embeddings=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating local embeddings: {e}")
            return []

    async def embed_query(self, text: str) -> list[float]:
        """Generate query embedding."""
        try:
            model = self._get_model()
            embedding = model.encode(f"query: {text}", normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating local query embedding: {e}")
            return []


class EmbeddingService:
    """Unified embedding service with fallback."""

    def __init__(self):
        self._provider: BaseEmbeddingModel | None = None

    def _get_provider(self) -> BaseEmbeddingModel:
        """Get embedding provider based on configuration."""
        if self._provider is not None:
            return self._provider

        # Try YandexGPT first
        if settings.yandex_gpt_api_key and settings.yandex_gpt_folder_id:
            self._provider = YandexGPTEmbeddings()
            logger.info("Using YandexGPT embeddings")
        # Then try GigaChat
        elif settings.gigachat_client_id and settings.gigachat_client_secret:
            self._provider = GigaChatEmbeddings()
            logger.info("Using GigaChat embeddings")
        # Fallback to local
        else:
            self._provider = LocalEmbeddings()
            logger.info("Using local embeddings")

        return self._provider

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple documents."""
        provider = self._get_provider()
        return await provider.embed(texts)

    async def embed_query(self, text: str) -> list[float]:
        """Embed a search query."""
        provider = self._get_provider()
        return await provider.embed_query(text)


# Singleton
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Get embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
