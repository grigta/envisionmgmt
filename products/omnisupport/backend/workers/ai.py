"""AI processing worker.

Handles asynchronous AI tasks like:
- Document indexing and embedding
- RAG query processing
- AI suggestions generation
- Conversation summarization
"""

import asyncio
import json
import logging
from uuid import UUID
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_session
from shared.models.knowledge import KnowledgeDocument, KnowledgeChunk, DocumentStatus
from shared.events.types import EventType
from shared.events.publisher import get_publisher

from workers.base import BaseWorker

logger = logging.getLogger(__name__)

QUEUE_INDEXING = "queue:ai:indexing"
QUEUE_SUGGESTIONS = "queue:ai:suggestions"
QUEUE_SUMMARIZE = "queue:ai:summarize"


class AIWorker(BaseWorker):
    """Worker for AI processing tasks."""

    name = "ai_worker"

    def __init__(self):
        super().__init__()
        self.qdrant_client = None
        self.embedding_model = None

    async def setup(self):
        """Initialize AI resources."""
        await super().setup()

        # Initialize Qdrant client
        try:
            from qdrant_client import QdrantClient
            from shared.config import get_settings

            settings = get_settings()
            self.qdrant_client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
            )
            logger.info("Qdrant client initialized")
        except Exception as e:
            logger.warning(f"Qdrant not available: {e}")

    async def process(self):
        """Main processing loop - handle multiple queues."""
        tasks = [
            asyncio.create_task(self.process_indexing_queue()),
            asyncio.create_task(self.process_suggestions_queue()),
            asyncio.create_task(self.process_summarize_queue()),
        ]
        self._tasks.extend(tasks)

        await asyncio.gather(*tasks, return_exceptions=True)

    async def process_indexing_queue(self):
        """Process document indexing requests."""
        while not self._shutdown:
            try:
                item = await self.pop_from_queue(QUEUE_INDEXING, timeout=5)
                if item:
                    await self.index_document(item)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing indexing: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def process_suggestions_queue(self):
        """Process AI suggestion requests."""
        while not self._shutdown:
            try:
                item = await self.pop_from_queue(QUEUE_SUGGESTIONS, timeout=5)
                if item:
                    await self.generate_suggestions(item)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing suggestions: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def process_summarize_queue(self):
        """Process summarization requests."""
        while not self._shutdown:
            try:
                item = await self.pop_from_queue(QUEUE_SUMMARIZE, timeout=5)
                if item:
                    await self.summarize_conversation(item)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing summarize: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def index_document(self, item: dict):
        """Index a document for RAG."""
        document_id = item.get("document_id")
        tenant_id = item.get("tenant_id")

        logger.info(f"Indexing document {document_id}")

        async with get_session() as session:
            # Get document
            result = await session.execute(
                select(KnowledgeDocument).where(
                    KnowledgeDocument.id == UUID(document_id)
                )
            )
            document = result.scalar_one_or_none()

            if not document:
                logger.warning(f"Document {document_id} not found")
                return

            try:
                # Update status
                document.status = DocumentStatus.PROCESSING
                await session.commit()

                # Extract text based on type
                text = await self.extract_text(document)

                if not text:
                    document.status = DocumentStatus.ERROR
                    document.error_message = "Failed to extract text"
                    await session.commit()
                    return

                # Chunk the text
                chunks = self.chunk_text(text, chunk_size=500, overlap=50)

                # Generate embeddings and store in Qdrant
                for i, chunk_text in enumerate(chunks):
                    embedding = await self.generate_embedding(chunk_text)

                    # Store chunk in database
                    chunk = KnowledgeChunk(
                        document_id=document.id,
                        content=chunk_text,
                        chunk_index=i,
                        embedding_id=f"{document_id}_{i}",
                        metadata={"position": i, "total_chunks": len(chunks)},
                    )
                    session.add(chunk)

                    # Store in Qdrant
                    if self.qdrant_client and embedding:
                        await self.store_in_qdrant(
                            collection_name=f"tenant_{tenant_id}",
                            doc_id=f"{document_id}_{i}",
                            embedding=embedding,
                            payload={
                                "document_id": str(document_id),
                                "chunk_index": i,
                                "content": chunk_text[:1000],
                            },
                        )

                document.status = DocumentStatus.INDEXED
                document.chunk_count = len(chunks)
                await session.commit()

                logger.info(f"Document {document_id} indexed with {len(chunks)} chunks")

                # Publish event
                publisher = get_publisher()
                await publisher.publish(
                    EventType.KNOWLEDGE_DOCUMENT_INDEXED,
                    {"document_id": str(document_id), "tenant_id": tenant_id},
                )

            except Exception as e:
                document.status = DocumentStatus.ERROR
                document.error_message = str(e)[:500]
                await session.commit()
                logger.error(f"Error indexing document {document_id}: {e}")

    async def extract_text(self, document: KnowledgeDocument) -> str | None:
        """Extract text from document based on type."""
        # Placeholder - implement based on document type
        if document.source_type == "text":
            return document.content
        elif document.source_type == "url":
            # Fetch and parse URL content
            return await self.fetch_url_content(document.source_url)
        elif document.source_type == "file":
            # Parse uploaded file
            return await self.parse_file(document.file_path, document.mime_type)
        return None

    async def fetch_url_content(self, url: str) -> str | None:
        """Fetch and extract text from URL."""
        import httpx
        from bs4 import BeautifulSoup

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    # Remove scripts and styles
                    for tag in soup(["script", "style", "nav", "footer"]):
                        tag.decompose()
                    return soup.get_text(separator="\n", strip=True)
        except Exception as e:
            logger.error(f"Error fetching URL {url}: {e}")
        return None

    async def parse_file(self, file_path: str, mime_type: str) -> str | None:
        """Parse file and extract text."""
        # Placeholder - implement file parsing
        # Use pypdf for PDF, python-docx for DOCX, etc.
        return None

    def chunk_text(
        self, text: str, chunk_size: int = 500, overlap: int = 50
    ) -> list[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        chunks = []
        start = 0

        while start < len(words):
            end = start + chunk_size
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            start = end - overlap

        return chunks

    async def generate_embedding(self, text: str) -> list[float] | None:
        """Generate embedding for text."""
        # Placeholder - implement with actual embedding model
        # Use sentence-transformers, OpenAI API, or YandexGPT embeddings
        return None

    async def store_in_qdrant(
        self,
        collection_name: str,
        doc_id: str,
        embedding: list[float],
        payload: dict,
    ):
        """Store embedding in Qdrant."""
        if not self.qdrant_client:
            return

        try:
            from qdrant_client.models import PointStruct

            self.qdrant_client.upsert(
                collection_name=collection_name,
                points=[
                    PointStruct(
                        id=doc_id,
                        vector=embedding,
                        payload=payload,
                    )
                ],
            )
        except Exception as e:
            logger.error(f"Error storing in Qdrant: {e}")

    async def generate_suggestions(self, item: dict):
        """Generate AI suggestions for a message."""
        conversation_id = item.get("conversation_id")
        message_text = item.get("message_text")
        tenant_id = item.get("tenant_id")

        logger.info(f"Generating suggestions for conversation {conversation_id}")

        # Search relevant knowledge
        context = await self.search_knowledge(tenant_id, message_text)

        # Generate suggestions using LLM
        suggestions = await self.call_llm(
            prompt=f"""Based on the customer message and context, suggest helpful responses.

Customer message: {message_text}

Relevant context:
{context}

Generate 2-3 brief, helpful response suggestions.""",
            max_tokens=500,
        )

        # Publish suggestions
        publisher = get_publisher()
        await publisher.publish(
            EventType.AI_SUGGESTION_READY,
            {
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
                "suggestions": suggestions,
            },
        )

    async def search_knowledge(self, tenant_id: str, query: str) -> str:
        """Search knowledge base for relevant context."""
        if not self.qdrant_client:
            return ""

        try:
            query_embedding = await self.generate_embedding(query)
            if not query_embedding:
                return ""

            results = self.qdrant_client.search(
                collection_name=f"tenant_{tenant_id}",
                query_vector=query_embedding,
                limit=5,
            )

            context_parts = []
            for hit in results:
                content = hit.payload.get("content", "")
                context_parts.append(content)

            return "\n---\n".join(context_parts)

        except Exception as e:
            logger.error(f"Error searching knowledge: {e}")
            return ""

    async def call_llm(self, prompt: str, max_tokens: int = 500) -> list[str]:
        """Call LLM for text generation."""
        # Placeholder - implement with YandexGPT, GigaChat, or other LLM
        return []

    async def summarize_conversation(self, item: dict):
        """Summarize a conversation."""
        conversation_id = item.get("conversation_id")
        messages = item.get("messages", [])
        tenant_id = item.get("tenant_id")

        logger.info(f"Summarizing conversation {conversation_id}")

        # Format messages for summarization
        formatted = "\n".join(
            f"{m['sender']}: {m['text']}" for m in messages
        )

        summary = await self.call_llm(
            prompt=f"""Summarize this customer support conversation briefly:

{formatted}

Summary:""",
            max_tokens=200,
        )

        # Publish summary
        publisher = get_publisher()
        await publisher.publish(
            EventType.AI_SUMMARY_READY,
            {
                "conversation_id": conversation_id,
                "tenant_id": tenant_id,
                "summary": summary[0] if summary else "",
            },
        )


async def main():
    """Run AI worker."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    worker = AIWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
