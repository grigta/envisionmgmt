"""AI endpoints (suggestions, summarization, sentiment)."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.auth.dependencies import ActiveUser, get_db, require_permissions
from shared.models.conversation import Conversation, Message, SenderType
from shared.models.user import User

from services.ai.llm.service import get_llm_service
from services.ai.rag.retriever import get_rag_service

logger = logging.getLogger(__name__)
router = APIRouter()


class SuggestionRequest(BaseModel):
    """Request for AI suggestion."""

    conversation_id: UUID
    context_messages: int = 10
    num_suggestions: int = 3


class SuggestionResponse(BaseModel):
    """AI suggestion response."""

    suggestions: list[str]
    context_used: bool = False
    sources: list[dict] = []


class SummarizeRequest(BaseModel):
    """Request for conversation summary."""

    conversation_id: UUID
    max_length: int = 200


class SummarizeResponse(BaseModel):
    """Conversation summary response."""

    summary: str
    key_points: list[str]
    sentiment: str | None = None


class SentimentRequest(BaseModel):
    """Request for sentiment analysis."""

    text: str


class SentimentResponse(BaseModel):
    """Sentiment analysis response."""

    sentiment: str  # positive, negative, neutral
    score: float
    emotions: list[str] = []


class IntentRequest(BaseModel):
    """Request for intent classification."""

    text: str
    intents: list[str]


class IntentResponse(BaseModel):
    """Intent classification response."""

    intent: str | None
    confidence: float


@router.post("/suggestions", response_model=SuggestionResponse)
async def get_suggestions(
    data: SuggestionRequest,
    current_user: Annotated[User, Depends(require_permissions("ai:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get AI suggestions for conversation response."""
    # Verify conversation access
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == data.conversation_id)
        .where(Conversation.tenant_id == current_user.tenant_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Диалог не найден",
        )

    # Get recent messages
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == data.conversation_id)
        .order_by(Message.created_at.desc())
        .limit(data.context_messages)
    )
    messages = list(reversed(list(result.scalars().all())))

    if not messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нет сообщений для анализа",
        )

    # Get last customer message
    customer_message = None
    for msg in reversed(messages):
        if msg.sender_type == SenderType.CUSTOMER:
            customer_message = msg.content.get("text", "") if msg.content else ""
            break

    if not customer_message:
        return SuggestionResponse(
            suggestions=["Здравствуйте! Чем могу помочь?"],
            context_used=False,
        )

    # Get context from knowledge base
    rag_service = get_rag_service()
    context = await rag_service.retrieve_with_context(
        tenant_id=current_user.tenant_id,
        query=customer_message,
        top_k=3,
        max_context_length=2000,
    )

    # Generate suggestions using LLM
    llm_service = get_llm_service()
    suggestions = await llm_service.generate_suggestions(
        customer_message=customer_message,
        context=context,
        num_suggestions=data.num_suggestions,
    )

    if not suggestions:
        # Fallback if LLM fails
        suggestions = ["Здравствуйте! Спасибо за обращение. Позвольте уточнить детали вашего вопроса."]

    return SuggestionResponse(
        suggestions=suggestions,
        context_used=bool(context),
        sources=[],  # Could add source documents here
    )


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_conversation(
    data: SummarizeRequest,
    current_user: Annotated[User, Depends(require_permissions("ai:read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Summarize conversation."""
    # Verify conversation access
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == data.conversation_id)
        .where(Conversation.tenant_id == current_user.tenant_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Диалог не найден",
        )

    # Get all messages
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == data.conversation_id)
        .order_by(Message.created_at)
    )
    messages = list(result.scalars().all())

    if not messages:
        return SummarizeResponse(
            summary="Диалог пуст",
            key_points=[],
        )

    # Format messages for LLM
    formatted_messages = []
    for msg in messages:
        sender = "customer" if msg.sender_type == SenderType.CUSTOMER else "operator"
        text = msg.content.get("text", "") if msg.content else ""
        if text:
            formatted_messages.append({"sender": sender, "text": text})

    # Generate summary using LLM
    llm_service = get_llm_service()
    summary = await llm_service.summarize_conversation(
        messages=formatted_messages,
        max_length=data.max_length,
    )

    if not summary:
        summary = "Не удалось сгенерировать саммари"

    # Extract key points (simple heuristic)
    key_points = []
    if len(summary) > 50:
        sentences = summary.split(". ")
        key_points = [s.strip() + "." for s in sentences[:3] if s.strip()]

    # Get overall sentiment
    full_text = " ".join(
        msg.content.get("text", "")
        for msg in messages
        if msg.sender_type == SenderType.CUSTOMER and msg.content
    )

    sentiment_result = await llm_service.analyze_sentiment(full_text[:1000])
    sentiment = sentiment_result.get("sentiment", "neutral") if sentiment_result else "neutral"

    return SummarizeResponse(
        summary=summary,
        key_points=key_points,
        sentiment=sentiment,
    )


@router.post("/sentiment", response_model=SentimentResponse)
async def analyze_sentiment(
    data: SentimentRequest,
    current_user: Annotated[User, Depends(require_permissions("ai:read"))],
):
    """Analyze text sentiment."""
    if not data.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Текст не может быть пустым",
        )

    llm_service = get_llm_service()
    result = await llm_service.analyze_sentiment(data.text)

    if result:
        return SentimentResponse(
            sentiment=result.get("sentiment", "neutral"),
            score=result.get("score", 0.5),
            emotions=result.get("emotions", []),
        )

    # Fallback
    return SentimentResponse(
        sentiment="neutral",
        score=0.5,
        emotions=[],
    )


@router.post("/intent", response_model=IntentResponse)
async def classify_intent(
    data: IntentRequest,
    current_user: Annotated[User, Depends(require_permissions("ai:read"))],
):
    """Classify message intent."""
    if not data.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Текст не может быть пустым",
        )

    if not data.intents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Список намерений не может быть пустым",
        )

    llm_service = get_llm_service()
    intent = await llm_service.classify_intent(data.text, data.intents)

    return IntentResponse(
        intent=intent,
        confidence=0.8 if intent else 0.0,
    )


@router.post("/search")
async def search_knowledge(
    query: str,
    top_k: int = 5,
    current_user: Annotated[User, Depends(require_permissions("knowledge:read"))],
):
    """Search knowledge base."""
    if not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поисковый запрос не может быть пустым",
        )

    rag_service = get_rag_service()
    results = await rag_service.retrieve(
        tenant_id=current_user.tenant_id,
        query=query,
        top_k=top_k,
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
    }
