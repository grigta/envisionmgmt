"""RAG retriever service - ties everything together."""

import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_session
from shared.models.knowledge import KnowledgeDocument, KnowledgeChunk, DocumentStatus

from services.ai.rag.vector_store import get_vector_store
from services.ai.rag.embeddings import get_embedding_service
from services.ai.knowledge.processors import DocumentProcessorFactory
from services.ai.knowledge.chunking import get_chunker, TextChunk

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Retrieved chunk with relevance info."""

    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: dict


class RAGService:
    """Main RAG service for knowledge retrieval."""

    def __init__(self):
        self.vector_store = get_vector_store()
        self.embedding_service = get_embedding_service()

    async def index_document(
        self,
        tenant_id: UUID,
        document_id: UUID,
        content: bytes | str,
        mime_type: str | None = None,
        filename: str | None = None,
        metadata: dict | None = None,
    ) -> int:
        """
        Index a document for RAG retrieval.

        Returns number of chunks indexed.
        """
        # Extract text if bytes
        if isinstance(content, bytes):
            text = DocumentProcessorFactory.extract_text(content, mime_type, filename)
            if not text:
                logger.error(f"Failed to extract text from document {document_id}")
                return 0
        else:
            text = content

        # Chunk the text
        chunker = get_chunker("semantic", max_chunk_size=800, min_chunk_size=100)
        chunks = chunker.chunk(text)

        if not chunks:
            logger.warning(f"No chunks generated for document {document_id}")
            return 0

        logger.info(f"Generated {len(chunks)} chunks for document {document_id}")

        # Generate embeddings
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = await self.embedding_service.embed_documents(chunk_texts)

        if len(embeddings) != len(chunks):
            logger.error("Embedding count mismatch")
            return 0

        # Prepare points for vector store
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            if not embedding:
                continue

            point_id = f"{document_id}_{i}"
            points.append({
                "id": point_id,
                "vector": embedding,
                "payload": {
                    "document_id": str(document_id),
                    "tenant_id": str(tenant_id),
                    "chunk_index": i,
                    "content": chunk.content[:2000],  # Store truncated for retrieval
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                    **(metadata or {}),
                },
            })

        # Store in vector DB
        success = await self.vector_store.upsert_vectors(tenant_id, points)

        if success:
            logger.info(f"Indexed {len(points)} chunks for document {document_id}")
            return len(points)

        return 0

    async def retrieve(
        self,
        tenant_id: UUID,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
        filter_document_ids: list[UUID] | None = None,
    ) -> list[RetrievalResult]:
        """
        Retrieve relevant chunks for a query.

        Args:
            tenant_id: Tenant ID
            query: Search query
            top_k: Number of results
            score_threshold: Minimum relevance score
            filter_document_ids: Optional list of document IDs to filter

        Returns:
            List of relevant chunks
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_query(query)

        if not query_embedding:
            logger.warning("Failed to generate query embedding")
            return []

        # Build filter
        filter_conditions = None
        if filter_document_ids:
            filter_conditions = {
                "document_id": [str(doc_id) for doc_id in filter_document_ids]
            }

        # Search vector store
        results = await self.vector_store.search(
            tenant_id=tenant_id,
            query_vector=query_embedding,
            limit=top_k,
            score_threshold=score_threshold,
            filter_conditions=filter_conditions,
        )

        # Convert to RetrievalResult
        return [
            RetrievalResult(
                chunk_id=r["id"],
                document_id=r["payload"].get("document_id", ""),
                content=r["payload"].get("content", ""),
                score=r["score"],
                metadata={
                    k: v for k, v in r["payload"].items()
                    if k not in ("content", "document_id", "tenant_id")
                },
            )
            for r in results
        ]

    async def retrieve_with_context(
        self,
        tenant_id: UUID,
        query: str,
        top_k: int = 5,
        max_context_length: int = 3000,
    ) -> str:
        """
        Retrieve and format context for LLM.

        Returns formatted context string.
        """
        results = await self.retrieve(tenant_id, query, top_k)

        if not results:
            return ""

        context_parts = []
        current_length = 0

        for result in results:
            content = result.content
            if current_length + len(content) > max_context_length:
                # Truncate if needed
                remaining = max_context_length - current_length
                if remaining > 100:
                    content = content[:remaining] + "..."
                else:
                    break

            context_parts.append(f"[Релевантность: {result.score:.2f}]\n{content}")
            current_length += len(content)

        return "\n\n---\n\n".join(context_parts)

    async def delete_document(
        self,
        tenant_id: UUID,
        document_id: UUID,
    ) -> bool:
        """Delete document from vector store."""
        return await self.vector_store.delete_by_document(tenant_id, document_id)

    async def get_similar_chunks(
        self,
        tenant_id: UUID,
        chunk_id: str,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """Find chunks similar to a given chunk."""
        # Get the chunk's embedding from vector store
        # This would require storing/retrieving the original vector
        # For now, we'll use the content to search
        logger.warning("get_similar_chunks not fully implemented")
        return []


class KnowledgeIndexer:
    """Service for indexing knowledge documents."""

    def __init__(self):
        self.rag_service = RAGService()

    async def index_document_from_db(
        self,
        document_id: UUID,
    ) -> bool:
        """Index a document from database."""
        async with get_session() as session:
            result = await session.execute(
                select(KnowledgeDocument).where(
                    KnowledgeDocument.id == document_id
                )
            )
            document = result.scalar_one_or_none()

            if not document:
                logger.error(f"Document {document_id} not found")
                return False

            try:
                # Update status
                document.status = DocumentStatus.PROCESSING
                await session.commit()

                # Get content based on source type
                content = None
                mime_type = document.mime_type
                filename = document.title

                if document.source_type == "text":
                    content = document.content or ""
                elif document.source_type == "file" and document.file_path:
                    # Read file
                    try:
                        with open(document.file_path, "rb") as f:
                            content = f.read()
                    except Exception as e:
                        logger.error(f"Failed to read file: {e}")
                elif document.source_type == "url" and document.source_url:
                    # Fetch URL
                    import httpx
                    async with httpx.AsyncClient() as client:
                        response = await client.get(document.source_url, timeout=30.0)
                        if response.status_code == 200:
                            content = response.content
                            mime_type = response.headers.get("content-type", "text/html")

                if not content:
                    document.status = DocumentStatus.ERROR
                    document.error_message = "No content to index"
                    await session.commit()
                    return False

                # Index document
                chunk_count = await self.rag_service.index_document(
                    tenant_id=document.tenant_id,
                    document_id=document_id,
                    content=content,
                    mime_type=mime_type,
                    filename=filename,
                    metadata={
                        "title": document.title,
                        "source_type": document.source_type,
                        "source_url": document.source_url,
                    },
                )

                if chunk_count > 0:
                    document.status = DocumentStatus.INDEXED
                    document.chunk_count = chunk_count

                    # Save chunks to database
                    # (chunks are also in vector store)
                    await session.commit()
                    return True
                else:
                    document.status = DocumentStatus.ERROR
                    document.error_message = "No chunks generated"
                    await session.commit()
                    return False

            except Exception as e:
                logger.error(f"Error indexing document {document_id}: {e}")
                document.status = DocumentStatus.ERROR
                document.error_message = str(e)[:500]
                await session.commit()
                return False

    async def index_crawled_pages(
        self,
        tenant_id: UUID,
        pages: list,  # list[CrawledPage]
        source_url: str,
    ) -> int:
        """Index pages from web crawler."""
        indexed_count = 0

        async with get_session() as session:
            for page in pages:
                # Create document record
                document = KnowledgeDocument(
                    tenant_id=tenant_id,
                    title=page.title or page.url,
                    source_type="url",
                    source_url=page.url,
                    content=page.content,
                    status=DocumentStatus.PROCESSING,
                    metadata={
                        "crawled_from": source_url,
                        "depth": page.depth,
                    },
                )
                session.add(document)
                await session.flush()

                # Index content
                chunk_count = await self.rag_service.index_document(
                    tenant_id=tenant_id,
                    document_id=document.id,
                    content=page.content,
                    metadata={
                        "title": page.title,
                        "source_url": page.url,
                    },
                )

                if chunk_count > 0:
                    document.status = DocumentStatus.INDEXED
                    document.chunk_count = chunk_count
                    indexed_count += 1
                else:
                    document.status = DocumentStatus.ERROR

            await session.commit()

        logger.info(f"Indexed {indexed_count} pages from {source_url}")
        return indexed_count


# Singletons
_rag_service: RAGService | None = None
_knowledge_indexer: KnowledgeIndexer | None = None


def get_rag_service() -> RAGService:
    """Get RAG service singleton."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


def get_knowledge_indexer() -> KnowledgeIndexer:
    """Get knowledge indexer singleton."""
    global _knowledge_indexer
    if _knowledge_indexer is None:
        _knowledge_indexer = KnowledgeIndexer()
    return _knowledge_indexer
