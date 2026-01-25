"""Vector store service using Qdrant."""

import logging
from typing import Any
from uuid import UUID

from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from shared.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Vector dimension for embeddings (depends on model)
VECTOR_DIMENSION = 1024  # For multilingual-e5-large or similar


class VectorStore:
    """Qdrant vector store for RAG."""

    def __init__(self):
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )

    def get_collection_name(self, tenant_id: UUID) -> str:
        """Get collection name for tenant."""
        return f"tenant_{str(tenant_id).replace('-', '_')}"

    async def ensure_collection(self, tenant_id: UUID) -> bool:
        """Ensure collection exists for tenant."""
        collection_name = self.get_collection_name(tenant_id)

        try:
            collections = self.client.get_collections()
            existing = [c.name for c in collections.collections]

            if collection_name not in existing:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=VECTOR_DIMENSION,
                        distance=models.Distance.COSINE,
                    ),
                    # Optimized for small-medium datasets
                    optimizers_config=models.OptimizersConfigDiff(
                        indexing_threshold=10000,
                    ),
                )
                logger.info(f"Created collection: {collection_name}")

            return True

        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            return False

    async def upsert_vectors(
        self,
        tenant_id: UUID,
        points: list[dict[str, Any]],
    ) -> bool:
        """
        Upsert vectors into collection.

        points: [{"id": str, "vector": list[float], "payload": dict}]
        """
        collection_name = self.get_collection_name(tenant_id)

        try:
            await self.ensure_collection(tenant_id)

            qdrant_points = [
                models.PointStruct(
                    id=p["id"],
                    vector=p["vector"],
                    payload=p.get("payload", {}),
                )
                for p in points
            ]

            self.client.upsert(
                collection_name=collection_name,
                points=qdrant_points,
            )

            logger.debug(f"Upserted {len(points)} points to {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Error upserting vectors: {e}")
            return False

    async def search(
        self,
        tenant_id: UUID,
        query_vector: list[float],
        limit: int = 5,
        score_threshold: float = 0.5,
        filter_conditions: dict | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar vectors.

        Returns: [{"id": str, "score": float, "payload": dict}]
        """
        collection_name = self.get_collection_name(tenant_id)

        try:
            # Build filter if provided
            qdrant_filter = None
            if filter_conditions:
                must_conditions = []
                for key, value in filter_conditions.items():
                    if isinstance(value, list):
                        must_conditions.append(
                            models.FieldCondition(
                                key=key,
                                match=models.MatchAny(any=value),
                            )
                        )
                    else:
                        must_conditions.append(
                            models.FieldCondition(
                                key=key,
                                match=models.MatchValue(value=value),
                            )
                        )
                qdrant_filter = models.Filter(must=must_conditions)

            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=qdrant_filter,
            )

            return [
                {
                    "id": str(hit.id),
                    "score": hit.score,
                    "payload": hit.payload or {},
                }
                for hit in results
            ]

        except UnexpectedResponse as e:
            if "not found" in str(e).lower():
                logger.warning(f"Collection {collection_name} not found")
                return []
            raise
        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            return []

    async def delete_by_document(
        self,
        tenant_id: UUID,
        document_id: UUID,
    ) -> bool:
        """Delete all vectors for a document."""
        collection_name = self.get_collection_name(tenant_id)

        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="document_id",
                                match=models.MatchValue(value=str(document_id)),
                            )
                        ]
                    )
                ),
            )

            logger.info(f"Deleted vectors for document {document_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
            return False

    async def delete_collection(self, tenant_id: UUID) -> bool:
        """Delete entire tenant collection."""
        collection_name = self.get_collection_name(tenant_id)

        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False

    async def get_collection_info(self, tenant_id: UUID) -> dict | None:
        """Get collection statistics."""
        collection_name = self.get_collection_name(tenant_id)

        try:
            info = self.client.get_collection(collection_name)
            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status.value,
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return None


# Singleton instance
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Get vector store singleton."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
