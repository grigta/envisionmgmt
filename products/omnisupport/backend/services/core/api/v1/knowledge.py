"""Knowledge base endpoints."""

import json
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth.dependencies import ActiveUser, get_db, require_permissions
from shared.models.knowledge import (
    KnowledgeDocument,
    KnowledgeChunk,
    CrawlerConfig,
    DocumentSourceType,
    DocumentStatus,
    CrawlerStatus,
)
from shared.models.user import User
from shared.schemas.base import SuccessResponse, PaginatedResponse

from services.ai.rag.retriever import get_rag_service, get_knowledge_indexer
from services.ai.knowledge.crawler import crawl_website
from services.ai.knowledge.processors import DocumentProcessorFactory

logger = logging.getLogger(__name__)
router = APIRouter()


async def _index_document_task(document_id: UUID):
    """Background task to index document."""
    indexer = get_knowledge_indexer()
    success = await indexer.index_document_from_db(document_id)
    logger.info(f"Document {document_id} indexing: {'success' if success else 'failed'}")


async def _run_crawler_task(crawler_id: UUID, tenant_id: UUID):
    """Background task to run crawler."""
    from shared.database import get_session

    async with get_session() as session:
        result = await session.execute(
            select(CrawlerConfig).where(CrawlerConfig.id == crawler_id)
        )
        crawler = result.scalar_one_or_none()

        if not crawler:
            return

        try:
            crawler.status = CrawlerStatus.RUNNING
            await session.commit()

            # Run crawler
            pages = await crawl_website(
                url=crawler.start_url,
                max_pages=crawler.max_pages,
                max_depth=crawler.max_depth,
                include_patterns=crawler.url_patterns,
                exclude_patterns=crawler.exclude_patterns,
            )

            # Index crawled pages
            indexer = get_knowledge_indexer()
            indexed = await indexer.index_crawled_pages(
                tenant_id=tenant_id,
                pages=pages,
                source_url=crawler.start_url,
            )

            crawler.status = CrawlerStatus.COMPLETED
            crawler.last_run_at = func.now()
            crawler.last_run_pages = indexed
            await session.commit()

            logger.info(f"Crawler {crawler_id} completed: {indexed} pages indexed")

        except Exception as e:
            logger.error(f"Crawler {crawler_id} error: {e}")
            crawler.status = CrawlerStatus.ERROR
            crawler.error_message = str(e)[:500]
            await session.commit()


# ==================== Documents ====================

@router.get("/documents")
async def list_documents(
    current_user: Annotated[User, Depends(require_permissions("knowledge:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: DocumentStatus | None = None,
    source_type: DocumentSourceType | None = None,
):
    """List knowledge base documents."""
    query = (
        select(KnowledgeDocument)
        .where(KnowledgeDocument.tenant_id == current_user.tenant_id)
    )

    if status:
        query = query.where(KnowledgeDocument.status == status)

    if source_type:
        query = query.where(KnowledgeDocument.source_type == source_type)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(KnowledgeDocument.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    documents = list(result.scalars().all())

    return PaginatedResponse.create(
        items=documents,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/documents/upload")
async def upload_document(
    current_user: Annotated[User, Depends(require_permissions("knowledge:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str | None = None,
    description: str | None = None,
):
    """Upload a document to knowledge base."""
    # Validate file type
    supported_extensions = DocumentProcessorFactory.supported_extensions()
    file_ext = "." + file.filename.split(".")[-1].lower() if file.filename else ""

    if file_ext not in supported_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неподдерживаемый тип файла. Поддерживаемые: {', '.join(supported_extensions)}",
        )

    # Read file content
    content = await file.read()

    # Extract text immediately to validate
    text = DocumentProcessorFactory.extract_text(
        content=content,
        mime_type=file.content_type,
        filename=file.filename,
    )

    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не удалось извлечь текст из документа",
        )

    # Create document record
    document = KnowledgeDocument(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        source_type=DocumentSourceType.FILE,
        file_name=file.filename,
        file_size=len(content),
        mime_type=file.content_type,
        title=title or file.filename,
        description=description,
        content=text,  # Store extracted text
        status=DocumentStatus.PENDING,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Queue for indexing
    background_tasks.add_task(_index_document_task, document.id)

    return document


@router.post("/documents/url")
async def add_document_from_url(
    current_user: Annotated[User, Depends(require_permissions("knowledge:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
    url: str,
    title: str | None = None,
    description: str | None = None,
):
    """Add document from URL."""
    document = KnowledgeDocument(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        source_type=DocumentSourceType.URL,
        source_url=url,
        title=title or url,
        description=description,
        status=DocumentStatus.PENDING,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Queue for indexing (will fetch URL)
    background_tasks.add_task(_index_document_task, document.id)

    return document


@router.post("/documents/text")
async def add_document_from_text(
    current_user: Annotated[User, Depends(require_permissions("knowledge:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
    title: str,
    content: str,
    description: str | None = None,
):
    """Add document from plain text."""
    if len(content) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Текст слишком короткий",
        )

    document = KnowledgeDocument(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        source_type=DocumentSourceType.TEXT,
        title=title,
        content=content,
        description=description,
        status=DocumentStatus.PENDING,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Queue for indexing
    background_tasks.add_task(_index_document_task, document.id)

    return document


@router.get("/documents/{document_id}")
async def get_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("knowledge:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get document details."""
    result = await db.execute(
        select(KnowledgeDocument)
        .where(KnowledgeDocument.id == document_id)
        .where(KnowledgeDocument.tenant_id == current_user.tenant_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Документ не найден",
        )

    return document


@router.get("/documents/{document_id}/chunks")
async def get_document_chunks(
    document_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("knowledge:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get document chunks."""
    # Verify document exists and belongs to tenant
    result = await db.execute(
        select(KnowledgeDocument)
        .where(KnowledgeDocument.id == document_id)
        .where(KnowledgeDocument.tenant_id == current_user.tenant_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Документ не найден",
        )

    # Get chunks
    result = await db.execute(
        select(KnowledgeChunk)
        .where(KnowledgeChunk.document_id == document_id)
        .order_by(KnowledgeChunk.chunk_index)
    )
    chunks = list(result.scalars().all())

    return {"document_id": str(document_id), "chunks": chunks, "total": len(chunks)}


@router.delete("/documents/{document_id}", response_model=SuccessResponse)
async def delete_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("knowledge:delete"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete document from knowledge base."""
    result = await db.execute(
        select(KnowledgeDocument)
        .where(KnowledgeDocument.id == document_id)
        .where(KnowledgeDocument.tenant_id == current_user.tenant_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Документ не найден",
        )

    # Delete from vector store
    rag_service = get_rag_service()
    await rag_service.delete_document(current_user.tenant_id, document_id)

    await db.delete(document)
    await db.commit()

    return SuccessResponse(message="Документ удалён")


@router.post("/documents/{document_id}/reindex", response_model=SuccessResponse)
async def reindex_document(
    document_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("knowledge:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
):
    """Reindex document."""
    result = await db.execute(
        select(KnowledgeDocument)
        .where(KnowledgeDocument.id == document_id)
        .where(KnowledgeDocument.tenant_id == current_user.tenant_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Документ не найден",
        )

    # Delete old vectors
    rag_service = get_rag_service()
    await rag_service.delete_document(current_user.tenant_id, document_id)

    document.status = DocumentStatus.PENDING
    await db.commit()

    # Queue for reindexing
    background_tasks.add_task(_index_document_task, document.id)

    return SuccessResponse(message="Документ поставлен в очередь на переиндексацию")


# ==================== Crawlers ====================

@router.get("/crawlers")
async def list_crawlers(
    current_user: Annotated[User, Depends(require_permissions("knowledge:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List website crawlers."""
    result = await db.execute(
        select(CrawlerConfig)
        .where(CrawlerConfig.tenant_id == current_user.tenant_id)
        .order_by(CrawlerConfig.created_at.desc())
    )
    crawlers = list(result.scalars().all())

    return {"items": crawlers, "total": len(crawlers)}


@router.post("/crawlers")
async def create_crawler(
    current_user: Annotated[User, Depends(require_permissions("knowledge:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    name: str,
    start_url: str,
    max_depth: int = 3,
    max_pages: int = 100,
    url_patterns: list[str] | None = None,
    exclude_patterns: list[str] | None = None,
):
    """Create website crawler."""
    crawler = CrawlerConfig(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        name=name,
        start_url=start_url,
        max_depth=max_depth,
        max_pages=max_pages,
        url_patterns=url_patterns or [],
        exclude_patterns=exclude_patterns or [],
    )
    db.add(crawler)
    await db.commit()
    await db.refresh(crawler)

    return crawler


@router.get("/crawlers/{crawler_id}")
async def get_crawler(
    crawler_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("knowledge:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get crawler details."""
    result = await db.execute(
        select(CrawlerConfig)
        .where(CrawlerConfig.id == crawler_id)
        .where(CrawlerConfig.tenant_id == current_user.tenant_id)
    )
    crawler = result.scalar_one_or_none()

    if not crawler:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Краулер не найден",
        )

    return crawler


@router.post("/crawlers/{crawler_id}/run", response_model=SuccessResponse)
async def run_crawler(
    crawler_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("knowledge:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
):
    """Start crawler run."""
    result = await db.execute(
        select(CrawlerConfig)
        .where(CrawlerConfig.id == crawler_id)
        .where(CrawlerConfig.tenant_id == current_user.tenant_id)
    )
    crawler = result.scalar_one_or_none()

    if not crawler:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Краулер не найден",
        )

    if crawler.status == CrawlerStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Краулер уже запущен",
        )

    # Run in background
    background_tasks.add_task(_run_crawler_task, crawler.id, current_user.tenant_id)

    return SuccessResponse(message="Краулер запущен")


@router.post("/crawlers/{crawler_id}/stop", response_model=SuccessResponse)
async def stop_crawler(
    crawler_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("knowledge:write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Stop running crawler."""
    result = await db.execute(
        select(CrawlerConfig)
        .where(CrawlerConfig.id == crawler_id)
        .where(CrawlerConfig.tenant_id == current_user.tenant_id)
    )
    crawler = result.scalar_one_or_none()

    if not crawler:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Краулер не найден",
        )

    if crawler.status != CrawlerStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Краулер не запущен",
        )

    # Mark as stopped (actual stop is handled by task checking status)
    crawler.status = CrawlerStatus.IDLE
    await db.commit()

    return SuccessResponse(message="Краулер остановлен")


@router.delete("/crawlers/{crawler_id}", response_model=SuccessResponse)
async def delete_crawler(
    crawler_id: UUID,
    current_user: Annotated[User, Depends(require_permissions("knowledge:delete"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete crawler."""
    result = await db.execute(
        select(CrawlerConfig)
        .where(CrawlerConfig.id == crawler_id)
        .where(CrawlerConfig.tenant_id == current_user.tenant_id)
    )
    crawler = result.scalar_one_or_none()

    if not crawler:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Краулер не найден",
        )

    if crawler.status == CrawlerStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить работающий краулер",
        )

    await db.delete(crawler)
    await db.commit()

    return SuccessResponse(message="Краулер удалён")


# ==================== Testing ====================

@router.post("/test")
async def test_knowledge_search(
    current_user: Annotated[User, Depends(require_permissions("knowledge:read"))],
    query: str,
    limit: int = Query(5, ge=1, le=20),
):
    """Test knowledge base search."""
    if not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поисковый запрос не может быть пустым",
        )

    rag_service = get_rag_service()
    results = await rag_service.retrieve(
        tenant_id=current_user.tenant_id,
        query=query,
        top_k=limit,
    )

    return {
        "query": query,
        "results": [
            {
                "content": r.content,
                "score": r.score,
                "document_id": r.document_id,
                "metadata": r.metadata,
            }
            for r in results
        ],
        "total": len(results),
    }
