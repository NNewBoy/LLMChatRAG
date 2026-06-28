"""文档表数据访问层"""

import uuid
from datetime import datetime
from typing import Optional


async def create_document(db, filename: str, file_type: str, file_size: int) -> dict:
    """创建文档记录"""
    doc_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    await db.execute(
        """INSERT INTO documents (id, filename, file_type, file_size, status, chunk_count, error_message, created_at)
           VALUES (?, ?, ?, ?, 'uploading', 0, NULL, ?)""",
        (doc_id, filename, file_type, file_size, now),
    )
    await db.commit()
    return {
        "id": doc_id,
        "filename": filename,
        "file_type": file_type,
        "file_size": file_size,
        "status": "uploading",
        "chunk_count": 0,
        "error_message": None,
        "created_at": now,
    }


async def get_document(db, doc_id: str) -> Optional[dict]:
    """获取单个文档"""
    cursor = await db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def list_documents(db) -> list:
    """获取所有文档列表"""
    cursor = await db.execute("SELECT * FROM documents ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def update_status(db, doc_id: str, status: str,
                        chunk_count: Optional[int] = None,
                        error_message: Optional[str] = None):
    """更新文档状态"""
    if chunk_count is not None:
        await db.execute(
            "UPDATE documents SET status = ?, chunk_count = ?, error_message = ? WHERE id = ?",
            (status, chunk_count, error_message, doc_id),
        )
    else:
        await db.execute(
            "UPDATE documents SET status = ?, error_message = ? WHERE id = ?",
            (status, error_message, doc_id),
        )
    await db.commit()


async def delete_document(db, doc_id: str):
    """删除文档记录"""
    await db.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    await db.commit()
