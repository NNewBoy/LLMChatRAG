"""对话请求/响应模型"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ConversationCreate(BaseModel):
    mode: str = Field(..., pattern="^(chat|rag)$")
    title: str = ""


class ConversationResponse(BaseModel):
    id: str
    title: str
    mode: str
    created_at: str
    updated_at: str


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    thinking: Optional[str] = None
    tool_calls: Optional[str] = None
    is_correct: Optional[int] = None
    parent_message_id: Optional[str] = None
    created_at: str


class MessageListResponse(BaseModel):
    messages: list[MessageResponse]


class ChatMessageRequest(BaseModel):
    content: str
    model: str
    image: Optional[str] = None
    parent_message_id: Optional[str] = None
    enable_intent_recognition: bool = True


class RegenerateRequest(BaseModel):
    model: str


class StopResponse(BaseModel):
    status: str
    message_id: str
