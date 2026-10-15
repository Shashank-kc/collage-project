"""
CodeGuard AI - AI Assistant Request & Response Schemas
======================================================
Defines schemas for chat messages, finding context, conversation threads,
and structured AI responses.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class FindingContextModel(BaseModel):
    """Metadata for a scanner finding passed to the AI Assistant."""
    rule_id: str
    tool: str = "scanner"
    severity: str = "INFO"
    message: str
    line: Optional[int] = None
    code_snippet: Optional[str] = None


class ChatMessageRequest(BaseModel):
    """Incoming user message payload to the AI Assistant."""
    message: str = Field(..., min_length=1, max_length=10000, description="User prompt or question")
    conversation_id: Optional[str] = Field(default=None, description="Existing conversation ID or null for new thread")
    finding_context: Optional[FindingContextModel] = Field(default=None, description="Optional finding context for explanation")
    include_code: bool = Field(default=False, description="Explicit user consent to include code snippet with prompt")

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Message cannot be empty or whitespace only.")
        return trimmed


class ChatMessageResponse(BaseModel):
    """Single message within an AI Assistant conversation."""
    id: str
    conversation_id: str
    sender: str  # 'user' | 'assistant'
    content: str
    created_at: str
    finding_context: Optional[FindingContextModel] = None
    is_ai: bool = False


class ConversationSummary(BaseModel):
    """Conversation thread metadata for conversation lists."""
    id: str
    title: str
    created_at: str
    updated_at: str


class ConversationDetail(BaseModel):
    """Full conversation history including ordered messages."""
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[ChatMessageResponse]


class AIStatusResponse(BaseModel):
    """Status of OpenAI configuration."""
    available: bool
    model: str
    message: str
