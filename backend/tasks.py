"""Celery 异步任务

将耗时的 RAG 文档索引迁移到后台 Worker：
- index_document(doc_id, file_path, filename)  解析 → 分块 → 向量化 → 入库，同步更新 documents 表状态
- clean_expired_uploads(max_age_days)  清理上传目录中超过保留期的孤立文件
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path

from celery_app import celery_app
from config import settings
from utils.logger import logger


def _run_async(coro):
    """在 Celery 同步 Worker 中执行异步函数。"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="tasks.index_document", bind=True)
def index_document(self, doc_id: str, file_path: str, filename: str):
    """后台执行文档索引：解析 → 分块 → 向量化 → 存储，同步更新 documents 表状态。

    :return: dict，含 doc_id 与 chunk_count
    """
    from models.database import get_db
    from rag.pipeline import RAGPipeline

    async def _run():
        db = None
        try:
            # 状态：parsing → completed
            logger.info(f"[Celery] 文档处理状态变更: {filename} => parsing")
            db = await get_db()
            await db.execute(
                "UPDATE documents SET status = ? WHERE id = ?",
                ("parsing", doc_id),
            )
            await db.commit()
            await db.close()
            db = None

            pipeline = RAGPipeline()
            chunk_count = await pipeline.index_document(file_path, filename, doc_id)

            db = await get_db()
            await db.execute(
                "UPDATE documents SET status = 'completed', chunk_count = ? WHERE id = ?",
                (chunk_count, doc_id),
            )
            await db.commit()
            await db.close()
            db = None
            logger.info(f"[Celery] 文档处理完成: {filename}, 分块数: {chunk_count}")
            return {"doc_id": doc_id, "chunk_count": chunk_count}

        except Exception as e:
            logger.error(f"[Celery] 文档处理失败: {filename}, 错误: {e}")
            if db is None:
                db = await get_db()
            await db.execute(
                "UPDATE documents SET status = 'failed', error_message = ? WHERE id = ?",
                (str(e)[:500], doc_id),
            )
            await db.commit()
            await db.close()
            raise

    return _run_async(_run())


@celery_app.task(name="maintenance.clean_expired_uploads", ignore_result=True)
def clean_expired_uploads(max_age_days: int = 30):
    """清理上传目录中超过 max_age_days 的孤立临时文件，释放磁盘空间。"""
    upload_dir = Path(__file__).resolve().parent / "data" / "uploads"
    if not upload_dir.exists():
        return {"deleted": 0}

    threshold = datetime.now().timestamp() - max_age_days * 86400
    count = 0
    for f in upload_dir.iterdir():
        if f.is_file() and f.stat().st_mtime < threshold:
            f.unlink(missing_ok=True)
            count += 1
    logger.info(f"[Celery] 清理过期上传文件: {count} 个")
    return {"deleted": count}