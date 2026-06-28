"""长期记忆管理 - 使用 SQLite 存储跨会话记忆"""

import uuid
from datetime import datetime
from models.database import get_db
from utils.logger import logger


class LongTermMemory:
    """
    管理跨会话的长期记忆。
    使用 SQLite 存储键值对，带重要性权重。
    """

    async def store(self, key: str, value: str, importance: float = 0.5):
        """存储记忆，如果 key 已存在则更新 importance"""
        memory_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO long_term_memory (id, key, value, importance, created_at, last_accessed_at)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(key) DO UPDATE SET
                       value=excluded.value,
                       importance=excluded.importance,
                       last_accessed_at=excluded.last_accessed_at""",
                (memory_id, key, value, importance, now, now),
            )
            await db.commit()
            logger.debug(f"存储记忆: key={key}, importance={importance}")
        finally:
            await db.close()

    async def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """基于查询检索相关记忆，按重要性排序"""
        db = await get_db()
        try:
            # 简单的关键词匹配检索
            cursor = await db.execute(
                """SELECT id, key, value, importance, created_at, last_accessed_at
                   FROM long_term_memory
                   WHERE value LIKE ? OR key LIKE ?
                   ORDER BY importance DESC
                   LIMIT ?""",
                (f"%{query}%", f"%{query}%", top_k),
            )
            rows = await cursor.fetchall()

            # 更新最后访问时间
            now = datetime.now().isoformat()
            for row in rows:
                await db.execute(
                    "UPDATE long_term_memory SET last_accessed_at = ? WHERE id = ?",
                    (now, row["id"]),
                )
            await db.commit()

            return [dict(row) for row in rows]
        finally:
            await db.close()

    async def forget(self, key: str):
        """删除指定记忆"""
        db = await get_db()
        try:
            await db.execute("DELETE FROM long_term_memory WHERE key = ?", (key,))
            await db.commit()
            logger.debug(f"删除记忆: key={key}")
        finally:
            await db.close()

    async def get_all(self) -> list[dict]:
        """获取所有记忆"""
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT id, key, value, importance, created_at, last_accessed_at "
                "FROM long_term_memory ORDER BY importance DESC"
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await db.close()

    async def consolidate(self):
        """记忆整理：合并相似记忆，删除低重要性记忆"""
        db = await get_db()
        try:
            # 删除重要性低于 0.1 的记忆
            await db.execute("DELETE FROM long_term_memory WHERE importance < 0.1")
            await db.commit()
            logger.info("记忆整理完成")
        finally:
            await db.close()
