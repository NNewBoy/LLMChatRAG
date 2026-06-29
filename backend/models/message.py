"""消息表数据访问层"""

import uuid
import json
from typing import Optional
import aiosqlite
from utils.timezone import now_iso


async def create_message(
    db: aiosqlite.Connection,
    conversation_id: str,
    role: str,
    content: str = "",
    thinking: Optional[str] = None,
    tool_calls: Optional[str] = None,
    parent_message_id: Optional[str] = None,
) -> dict:
    """创建消息"""
    msg_id = str(uuid.uuid4())
    now = now_iso()
    await db.execute(
        """INSERT INTO messages (id, conversation_id, role, content, thinking, tool_calls, parent_message_id, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (msg_id, conversation_id, role, content, thinking, tool_calls, parent_message_id, now),
    )
    await db.commit()
    return {
        "id": msg_id,
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "thinking": json.loads(thinking) if thinking else None,
        "tool_calls": json.loads(tool_calls) if tool_calls else None,
        "is_correct": None,
        "parent_message_id": parent_message_id,
        "created_at": now,
    }


async def get_messages_by_conversation(
    db: aiosqlite.Connection, conversation_id: str
) -> list[dict]:
    """获取会话所有消息，按创建时间排序"""
    cursor = await db.execute(
        """SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC""",
        (conversation_id,),
    )
    rows = await cursor.fetchall()
    result = []
    for row in rows:
        result.append({
            "id": row["id"],
            "conversation_id": row["conversation_id"],
            "role": row["role"],
            "content": row["content"],
            "thinking": json.loads(row["thinking"]) if row["thinking"] else None,
            "tool_calls": json.loads(row["tool_calls"]) if row["tool_calls"] else None,
            "is_correct": row["is_correct"],
            "parent_message_id": row["parent_message_id"],
            "created_at": row["created_at"],
        })
    return result


async def get_message_by_id(
    db: aiosqlite.Connection, message_id: str
) -> Optional[dict]:
    """获取单条消息"""
    cursor = await db.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
    row = await cursor.fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "conversation_id": row["conversation_id"],
        "role": row["role"],
        "content": row["content"],
        "thinking": json.loads(row["thinking"]) if row["thinking"] else None,
        "tool_calls": json.loads(row["tool_calls"]) if row["tool_calls"] else None,
        "is_correct": row["is_correct"],
        "parent_message_id": row["parent_message_id"],
        "created_at": row["created_at"],
    }


async def update_message_content(
    db: aiosqlite.Connection,
    message_id: str,
    content: str,
    thinking: Optional[str] = None,
    tool_calls: Optional[str] = None,
):
    """更新消息内容"""
    await db.execute(
        """UPDATE messages SET content = ?, thinking = ?, tool_calls = ? WHERE id = ?""",
        (content, thinking, tool_calls, message_id),
    )
    await db.commit()


async def update_message_feedback(
    db: aiosqlite.Connection, message_id: str, is_correct: bool
):
    """更新消息评价"""
    await db.execute(
        "UPDATE messages SET is_correct = ? WHERE id = ?",
        (1 if is_correct else 0, message_id),
    )
    await db.commit()


async def delete_message(db: aiosqlite.Connection, message_id: str):
    """删除单条消息"""
    await db.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    await db.commit()


async def delete_message_and_after(
    db: aiosqlite.Connection, conversation_id: str, message_id: str
):
    """删除指定消息及其之后的所有消息（基于 created_at）"""
    cursor = await db.execute(
        "SELECT created_at FROM messages WHERE id = ?", (message_id,)
    )
    row = await cursor.fetchone()
    if not row:
        return
    created_at = row["created_at"]
    await db.execute(
        """DELETE FROM messages WHERE conversation_id = ? AND created_at >= ?""",
        (conversation_id, created_at),
    )
    await db.commit()
