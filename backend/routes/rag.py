"""RAG 对话路由 /api/rag/*"""

import uuid
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from typing import Optional
from schemas.chat import (
    ConversationCreate,
    ConversationResponse,
    ConversationListResponse,
    MessageResponse,
    MessageListResponse,
    RegenerateRequest,
    StopResponse,
)
from models.database import get_db
from services.rag_service import rag_service
from utils.logger import logger

router = APIRouter(prefix="/api/rag", tags=["rag"])


class RAGMessageRequest(BaseModel):
    content: str
    model: str
    parent_message_id: Optional[str] = None
    embedding_model: str = "BAAI/bge-large-zh-v1.5"
    enable_query_rewriting: bool = True
    enable_hybrid_search: bool = False
    enable_reranking: bool = False


class FeedbackRequest(BaseModel):
    is_correct: bool


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations():
    """获取 RAG 历史会话列表"""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM conversations WHERE mode = 'rag' ORDER BY updated_at DESC"
        )
        rows = await cursor.fetchall()
        conversations = [ConversationResponse(**dict(r)) for r in rows]
        return ConversationListResponse(conversations=conversations)
    finally:
        await db.close()


@router.post("/conversations", response_model=dict)
async def create_conversation(req: ConversationCreate):
    """创建 RAG 新会话"""
    conv_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO conversations (id, title, mode, created_at, updated_at) "
            "VALUES (?, ?, 'rag', ?, ?)",
            (conv_id, req.title, now, now),
        )
        await db.commit()
    finally:
        await db.close()

    return {
        "conversation": ConversationResponse(
            id=conv_id, title=req.title, mode="rag",
            created_at=now, updated_at=now,
        ).model_dump()
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """删除 RAG 会话"""
    db = await get_db()
    try:
        await db.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        await db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        await db.commit()
    finally:
        await db.close()
    return Response(status_code=204)


@router.get("/conversations/{conversation_id}/messages", response_model=MessageListResponse)
async def get_messages(conversation_id: str):
    """获取 RAG 会话消息历史"""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conversation_id,),
        )
        rows = await cursor.fetchall()
        messages = [MessageResponse(**dict(r)) for r in rows]
        return MessageListResponse(messages=messages)
    finally:
        await db.close()


@router.post("/conversations/{conversation_id}/messages")
async def send_message(conversation_id: str, req: RAGMessageRequest):
    """发送 RAG 消息 (SSE 流式，无需意图识别)"""
    logger.info(f"RAG 消息: conv={conversation_id}, model={req.model}")

    async def event_stream():
        async for event in rag_service.send_message_stream(
            conversation_id=conversation_id,
            content=req.content,
            model=req.model,
            parent_message_id=req.parent_message_id,
            embedding_model=req.embedding_model,
            enable_query_rewriting=req.enable_query_rewriting,
            enable_hybrid_search=req.enable_hybrid_search,
            enable_reranking=req.enable_reranking,
        ):
            yield event

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/conversations/{conversation_id}/messages/{message_id}/stop", response_model=StopResponse)
async def stop_generation(conversation_id: str, message_id: str):
    """停止生成"""
    return StopResponse(status="stopped", message_id=message_id)


@router.post("/conversations/{conversation_id}/messages/{message_id}/regenerate")
async def regenerate_message(conversation_id: str, message_id: str, req: RegenerateRequest):
    """重新生成 RAG 回答 (SSE 流式)"""
    async def event_stream():
        async for event in rag_service.send_message_stream(
            conversation_id=conversation_id,
            content="",  # 从历史消息获取
            model=req.model,
            parent_message_id=None,
        ):
            yield event

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.delete("/conversations/{conversation_id}/messages/{message_id}")
async def delete_message(conversation_id: str, message_id: str):
    """删除指定消息"""
    db = await get_db()
    try:
        await db.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        await db.commit()
    finally:
        await db.close()
    return Response(status_code=204)


@router.post("/conversations/{conversation_id}/messages/{message_id}/feedback")
async def submit_feedback(conversation_id: str, message_id: str, req: FeedbackRequest):
    """标记答案正确/错误"""
    result = await rag_service.submit_feedback(conversation_id, message_id, req.is_correct)
    return result
