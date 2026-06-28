"""错题表数据访问层"""

import uuid
from datetime import datetime, timezone
from typing import Optional


async def create_bad_case(db, message_id: str, question: str, wrong_answer: str,
                          correct_answer: str = "", use_as_example: int = 0) -> dict:
    """创建错题记录"""
    bad_case_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        """INSERT INTO bad_cases (id, message_id, question, wrong_answer, correct_answer, use_as_example, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (bad_case_id, message_id, question, wrong_answer, correct_answer, use_as_example, now, now)
    )
    await db.commit()
    return {"id": bad_case_id, "message_id": message_id, "question": question,
            "wrong_answer": wrong_answer, "correct_answer": correct_answer,
            "use_as_example": bool(use_as_example), "created_at": now}


async def get_bad_cases(db, use_as_example: Optional[int] = None) -> list:
    """获取错题列表"""
    if use_as_example is not None:
        cursor = await db.execute(
            "SELECT * FROM bad_cases WHERE use_as_example = ? ORDER BY created_at DESC",
            (use_as_example,)
        )
    else:
        cursor = await db.execute("SELECT * FROM bad_cases ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def update_bad_case(db, bad_case_id: str, correct_answer: str,
                          use_as_example: int) -> Optional[dict]:
    """更新错题"""
    now = datetime.now(timezone.utc).isoformat()
    cursor = await db.execute(
        """UPDATE bad_cases SET correct_answer = ?, use_as_example = ?, updated_at = ?
           WHERE id = ?""",
        (correct_answer, use_as_example, now, bad_case_id)
    )
    await db.commit()
    if cursor.rowcount == 0:
        return None
    cursor = await db.execute("SELECT * FROM bad_cases WHERE id = ?", (bad_case_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def delete_bad_case(db, bad_case_id: str) -> bool:
    """删除错题"""
    cursor = await db.execute("DELETE FROM bad_cases WHERE id = ?", (bad_case_id,))
    await db.commit()
    return cursor.rowcount > 0


async def get_example_bad_cases(db) -> list:
    """获取标记为范例的错题，用于 RAG Prompt 构建"""
    cursor = await db.execute(
        "SELECT * FROM bad_cases WHERE use_as_example = 1 ORDER BY created_at DESC"
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]
