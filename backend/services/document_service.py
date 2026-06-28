"""文档管理业务逻辑"""

import uuid
import asyncio
from pathlib import Path
from models.database import get_db
from rag.parser import DocumentParser
from rag.pipeline import RAGPipeline
from config import settings
from utils.logger import logger


class DocumentService:
    """文档管理服务"""

    def __init__(self):
        self.parser = DocumentParser()
        self.upload_dir = Path("./data/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self._pipeline = None  # 延迟初始化

    async def _get_pipeline(self):
        """延迟获取 RAG pipeline"""
        if self._pipeline is None:
            self._pipeline = RAGPipeline()
        return self._pipeline

    async def save_upload(self, file, doc_id: str) -> str:
        """保存上传文件到磁盘，返回文件路径"""
        file_type = self.parser.get_file_type(file.filename)
        ext = Path(file.filename).suffix
        file_path = self.upload_dir / f"{doc_id}{ext}"

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        logger.info(f"文件已保存: {file_path}")
        return str(file_path)

    async def process_document(self, doc_id: str, file_path: str, filename: str):
        """异步处理文档: 解析 → 分块 → 向量化 → 存储"""
        asyncio.create_task(self._process_document(doc_id, file_path, filename))

    def delete_document_vectors(self, doc_id: str):
        """删除文档在 FAISS 中的向量数据"""
        try:
            pipeline = RAGPipeline()
            pipeline.remove_document(doc_id)
            logger.info(f"已删除文档向量: {doc_id}")
        except Exception as e:
            logger.warning(f"删除向量数据失败: {e}")

    async def upload_document(self, file_path: str, filename: str, file_size: int) -> dict:
        """上传文档并开始异步索引"""
        doc_id = str(uuid.uuid4())
        file_type = self.parser.get_file_type(filename)

        if file_type is None:
            raise ValueError(f"不支持的文件类型: {filename}")

        # 保存到数据库
        db = await get_db()
        try:
            await db.execute(
                "INSERT INTO documents (id, filename, file_type, file_size, status) "
                "VALUES (?, ?, ?, ?, 'uploading')",
                (doc_id, filename, file_type, file_size),
            )
            await db.commit()
        finally:
            await db.close()

        logger.info(f"文档上传: {filename} (id={doc_id})")

        # 异步处理文档索引
        asyncio.create_task(self._process_document(doc_id, file_path, filename))

        return {
            "id": doc_id,
            "filename": filename,
            "file_type": file_type,
            "file_size": file_size,
            "status": "uploading",
            "chunk_count": 0,
            "error_message": None,
            "created_at": "",
        }

    async def _process_document(self, doc_id: str, file_path: str, filename: str):
        """异步处理文档: 解析 → 分块 → 向量化 → 存储"""
        statuses = ["parsing", "chunking", "embedding", "completed"]
        db = None

        try:
            for status in statuses[:-1]:
                logger.info(f"文档处理状态变更: {filename} => {status}")
                db = await get_db()
                await db.execute(
                    "UPDATE documents SET status = ? WHERE id = ?",
                    (status, doc_id),
                )
                await db.commit()
                await db.close()
                db = None

                if status == "parsing":
                    # 执行解析 + 分块 + 向量化
                    pipeline = await self._get_pipeline()
                    chunk_count = await pipeline.index_document(file_path, filename, doc_id)

                    db = await get_db()
                    await db.execute(
                        "UPDATE documents SET status = 'completed', chunk_count = ? WHERE id = ?",
                        (chunk_count, doc_id),
                    )
                    await db.commit()
                    await db.close()
                    db = None
                    logger.info(f"文档处理完成: {filename}, 分块数: {chunk_count}")
                    return

        except Exception as e:
            logger.error(f"文档处理失败: {filename}, 错误: {e}")
            if db is None:
                db = await get_db()
            await db.execute(
                "UPDATE documents SET status = 'failed', error_message = ? WHERE id = ?",
                (str(e)[:500], doc_id),
            )
            await db.commit()
            await db.close()

    async def list_documents(self) -> list[dict]:
        """获取所有文档列表"""
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT * FROM documents ORDER BY created_at DESC"
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await db.close()

    async def get_document_status(self, doc_id: str) -> dict:
        """获取文档处理状态"""
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT id, status, chunk_count, error_message FROM documents WHERE id = ?",
                (doc_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return None

            status = row["status"]
            progress_map = {
                "uploading": "正在上传...",
                "parsing": "正在解析文档...",
                "chunking": "正在分块处理...",
                "embedding": "正在向量化...",
                "completed": "处理完成",
                "failed": f"处理失败: {row['error_message'] or '未知错误'}",
            }
            return {
                "id": row["id"],
                "status": status,
                "progress": progress_map.get(status, ""),
                "chunk_count": row["chunk_count"],
            }
        finally:
            await db.close()

    async def delete_document(self, doc_id: str) -> bool:
        """删除文档及其向量数据"""
        db = await get_db()
        try:
            # 查找文档
            cursor = await db.execute(
                "SELECT filename FROM documents WHERE id = ?", (doc_id,)
            )
            row = await cursor.fetchone()
            if not row:
                return False

            # 从 FAISS 删除向量
            try:
                pipeline = await self._get_pipeline()
                pipeline.remove_document(doc_id)
            except Exception as e:
                logger.warning(f"删除向量数据失败: {e}")

            # 从数据库删除
            await db.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            await db.commit()
            logger.info(f"文档已删除: {doc_id}")
            return True
        finally:
            await db.close()


document_service = DocumentService()
