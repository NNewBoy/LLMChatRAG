"""普通对话路由 /api/chat/*"""

import uuid
from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse, JSONResponse, Response
from schemas.chat import (
    ConversationCreate,
    ConversationResponse,
    ConversationListResponse,
    MessageResponse,
    MessageListResponse,
    ChatMessageRequest,
    RegenerateRequest,
    StopResponse,
)
from models.database import get_db
from services.chat_service import chat_service
from utils.logger import logger

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations():
    """获取历史会话列表"""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT * FROM conversations WHERE mode = 'chat' ORDER BY updated_at DESC"
        )
        rows = await cursor.fetchall()
        conversations = [ConversationResponse(**dict(r)) for r in rows]
        return ConversationListResponse(conversations=conversations)
    finally:
        await db.close()


@router.post("/conversations", response_model=dict)
async def create_conversation(req: ConversationCreate):
    """创建新会话"""
    conv_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO conversations (id, title, mode, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (conv_id, req.title, "chat", now, now),
        )
        await db.commit()
    finally:
        await db.close()

    return {
        "conversation": ConversationResponse(
            id=conv_id, title=req.title, mode="chat",
            created_at=now, updated_at=now,
        ).model_dump()
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """删除会话及其所有消息"""
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
    """获取会话消息历史"""
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
async def send_message(conversation_id: str, req: ChatMessageRequest):
    """发送消息 (SSE 流式)"""
    logger.info(f"Chat 消息: conv={conversation_id}, model={req.model}, intent={req.enable_intent_recognition}")

    async def event_stream():
        async for event in chat_service.chat_stream(
            conversation_id=conversation_id,
            content=req.content,
            model=req.model,
            image=req.image,
            parent_message_id=req.parent_message_id,
            enable_intent_recognition=req.enable_intent_recognition,
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
    chat_service.request_stop(message_id)
    return StopResponse(status="stopped", message_id=message_id)


@router.post("/conversations/{conversation_id}/messages/{message_id}/regenerate")
async def regenerate_message(conversation_id: str, message_id: str, req: RegenerateRequest):
    """重新生成回答 (SSE 流式)"""
    logger.info(f"重新生成: conv={conversation_id}, msg={message_id}")

    async def event_stream():
        async for event in chat_service.regenerate_stream(
            conversation_id=conversation_id,
            message_id=message_id,
            model=req.model,
        ):
            yield event

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.delete("/conversations/{conversation_id}/messages/{message_id}")
async def delete_message(conversation_id: str, message_id: str):
    """删除指定消息，若为助手回答则同时删除对应的用户提问"""
    db = await get_db()
    try:
        # 查询该消息的 role 和 parent_message_id
        cursor = await db.execute(
            "SELECT role, parent_message_id FROM messages WHERE id = ?",
            (message_id,),
        )
        msg = await cursor.fetchone()

        if msg:
            # 删除该消息
            await db.execute("DELETE FROM messages WHERE id = ?", (message_id,))
            # 若为助手回答，同时删除其对应的用户提问
            if msg["role"] == "assistant" and msg["parent_message_id"]:
                await db.execute(
                    "DELETE FROM messages WHERE id = ?",
                    (msg["parent_message_id"],),
                )
            await db.commit()
    finally:
        await db.close()
    return Response(status_code=204)
