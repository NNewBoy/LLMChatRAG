"""会话表模型"""

import uuid
from utils.timezone import now_iso


async def create_conversation(db, mode: str, title: str = "") -> dict:
    conv_id = str(uuid.uuid4())
    ts = now_iso()
    await db.execute(
        "INSERT INTO conversations (id, title, mode, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (conv_id, title, mode, ts, ts),
    )
    await db.commit()
    return {"id": conv_id, "title": title, "mode": mode, "created_at": ts, "updated_at": ts}


async def get_conversations(db, mode: str = None) -> list:
    if mode:
        cursor = await db.execute(
            "SELECT * FROM conversations WHERE mode = ? ORDER BY updated_at DESC", (mode,)
        )
    else:
        cursor = await db.execute("SELECT * FROM conversations ORDER BY updated_at DESC")
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_conversation(db, conv_id: str) -> dict | None:
    cursor = await db.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def delete_conversation(db, conv_id: str):
    await db.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    await db.commit()


async def update_conversation_title(db, conv_id: str, title: str):
    ts = now_iso()
    await db.execute(
        "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?", (title, ts, conv_id)
    )
    await db.commit()


async def touch_conversation(db, conv_id: str):
    """更新会话的 updated_at 时间"""
    ts = now_iso()
    await db.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (ts, conv_id))
    await db.commit()
