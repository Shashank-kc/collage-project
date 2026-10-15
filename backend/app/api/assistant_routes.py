"""
CodeGuard AI - AI Assistant API Endpoints
=========================================
Provides endpoints for AI conversations, message history, status,
and per-user rate limiting, strictly isolated to the authenticated user.
"""

from collections import defaultdict
import json
import time
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.config import (
    AI_RATE_LIMIT_REQUESTS,
    AI_RATE_LIMIT_WINDOW_SECONDS,
    OPENAI_MODEL,
)
from app.database.session import (
    create_conversation,
    delete_conversation,
    get_conversation,
    get_conversation_messages,
    get_user_conversations,
    save_message,
)
from app.schemas.assistant import (
    AIStatusResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationDetail,
    ConversationSummary,
    FindingContextModel,
)
from app.schemas.auth import UserResponse
from app.services.auth_service import get_current_user
from app.services.openai_service import openai_service

router = APIRouter(prefix="/api/v1/assistant", tags=["AI Assistant"])

# Per-user sliding-window rate limiter for expensive AI requests
_ai_user_request_history: dict[int, list[float]] = defaultdict(list)


def check_ai_rate_limit(user_id: int) -> None:
    """Enforces rate limiting on AI requests per user to prevent quota exhaustion."""
    now = time.time()
    cutoff = now - AI_RATE_LIMIT_WINDOW_SECONDS

    # Clean old requests
    timestamps = [t for t in _ai_user_request_history[user_id] if t > cutoff]
    timestamps.append(now)
    _ai_user_request_history[user_id] = timestamps

    if len(timestamps) > AI_RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: You can make up to {AI_RATE_LIMIT_REQUESTS} AI requests per minute. Please pause for a moment."
        )


@router.get("/status", response_model=AIStatusResponse)
async def get_assistant_status():
    """
    Returns public status of the AI Assistant integration.
    Never exposes API secrets or internal keys.
    """
    configured = openai_service.is_configured
    return AIStatusResponse(
        available=configured,
        model=openai_service.model,
        message="OpenAI Assistant online and ready." if configured else "OpenAI API key is not configured on the server."
    )


@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(current_user: UserResponse = Depends(get_current_user)):
    """
    Returns all AI conversation threads belonging exclusively to the authenticated user.
    """
    rows = get_user_conversations(current_user.id)
    return [
        ConversationSummary(
            id=r["id"],
            title=r["title"],
            created_at=r["created_at"],
            updated_at=r["updated_at"]
        )
        for r in rows
    ]


@router.post("/conversations", response_model=ConversationSummary, status_code=status.HTTP_201_CREATED)
async def start_new_conversation(
    title: Optional[str] = "New Conversation",
    current_user: UserResponse = Depends(get_current_user)
):
    """Creates a new empty conversation thread for the authenticated user."""
    conv_id = f"conv_{uuid.uuid4().hex[:16]}"
    clean_title = (title or "New Conversation").strip()[:80]
    conv = create_conversation(conv_id, current_user.id, clean_title)
    return ConversationSummary(
        id=conv["id"],
        title=conv["title"],
        created_at=conv["created_at"],
        updated_at=conv["updated_at"]
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation_history(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Retrieves full message history for a conversation thread.
    Enforces authorization: returns 404 if conversation belongs to another user.
    """
    conv = get_conversation(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access is unauthorized."
        )

    raw_messages = get_conversation_messages(conversation_id, current_user.id) or []
    messages = []
    for m in raw_messages:
        finding_ctx = None
        if m.get("finding_context"):
            try:
                parsed = json.loads(m["finding_context"])
                finding_ctx = FindingContextModel(**parsed)
            except Exception:
                pass

        messages.append(
            ChatMessageResponse(
                id=m["id"],
                conversation_id=m["conversation_id"],
                sender=m["sender"],
                content=m["content"],
                created_at=m["created_at"],
                finding_context=finding_ctx,
                is_ai=(m["sender"] == "assistant")
            )
        )

    return ConversationDetail(
        id=conv["id"],
        title=conv["title"],
        created_at=conv["created_at"],
        updated_at=conv["updated_at"],
        messages=messages
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_200_OK)
async def delete_conversation_endpoint(
    conversation_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Deletes an AI conversation thread and all contained messages.
    Enforces strict user ownership verification.
    """
    success = delete_conversation(conversation_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access is unauthorized."
        )
    return {"message": "Conversation deleted successfully."}


@router.post("/chat", response_model=ChatMessageResponse)
async def send_chat_message(
    payload: ChatMessageRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Authenticated chat endpoint: accepts user question/prompt, optionally
    enclosing scanner finding context, and returns real OpenAI assistant response.
    """
    check_ai_rate_limit(current_user.id)

    # 1. Resolve or create conversation
    conv_id = payload.conversation_id
    if not conv_id:
        # Create fresh conversation thread with title from prompt
        title_summary = payload.message.strip()[:40]
        if len(payload.message.strip()) > 40:
            title_summary += "..."
        conv_id = f"conv_{uuid.uuid4().hex[:16]}"
        create_conversation(conv_id, current_user.id, title_summary)
    else:
        # Verify ownership of existing conversation
        existing = get_conversation(conv_id, current_user.id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found or access is unauthorized."
            )

    # 2. Serialize finding context if present
    finding_json_str = None
    finding_dict = None
    if payload.finding_context:
        finding_dict = payload.finding_context.model_dump()
        finding_json_str = json.dumps(finding_dict)

    # 3. Store user message in database
    user_msg_id = f"msg_{uuid.uuid4().hex[:16]}"
    save_message(
        msg_id=user_msg_id,
        conv_id=conv_id,
        sender="user",
        content=payload.message,
        finding_context=finding_json_str
    )

    # 4. Fetch recent conversation history for LLM context
    history_rows = get_conversation_messages(conv_id, current_user.id) or []
    history_context = [
        {"sender": r["sender"], "content": r["content"]}
        for r in history_rows[:-1]  # Exclude the just-added user message
    ]

    # 5. Invoke OpenAI service
    try:
        assistant_content = openai_service.generate_chat_response(
            user_message=payload.message,
            conversation_history=history_context,
            finding_context=finding_dict,
            include_code=payload.include_code
        )
    except ValueError as val_err:
        error_msg = str(val_err)
        if "rate limit" in error_msg.lower() or "quota" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_msg
            )
        elif "not configured" in error_msg.lower() or "unavailable" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=error_msg
            )

    # 6. Store assistant response in database
    asst_msg_id = f"msg_{uuid.uuid4().hex[:16]}"
    saved_asst = save_message(
        msg_id=asst_msg_id,
        conv_id=conv_id,
        sender="assistant",
        content=assistant_content,
        finding_context=None
    )

    return ChatMessageResponse(
        id=asst_msg_id,
        conversation_id=conv_id,
        sender="assistant",
        content=assistant_content,
        created_at=saved_asst["created_at"],
        finding_context=payload.finding_context,
        is_ai=True
    )
