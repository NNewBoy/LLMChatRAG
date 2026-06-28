"""文档管理路由 /api/documents/* 和 错题集路由 /api/bad-cases/*"""

import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import Response
from typing import Optional
from schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    DocumentStatusResponse,
    BadCaseResponse,
    BadCaseListResponse,
    BadCaseUpdateRequest,
)
from models.database import get_db
from services.document_service import document_service
from utils.logger import logger

router = APIRouter(tags=["documents"])


# ========================================
# 文档管理接口
# ========================================

@router.post("/api/documents/upload", response_model=dict)
async def upload_document(file: UploadFile = File(...)):
    """上传文档"""
    logger.info(f"上传文档: {file.filename}")

    doc_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    file_size = 0

    # 保存文件
    file_path = await document_service.save_upload(file, doc_id)

    # 获取文件大小
    import os
    file_size = os.path.getsize(file_path)

    # 获取文件类型
    file_type = document_service.parser.get_file_type(file.filename)

    # 写入数据库
    db = await get_db()
    try:
        await db.execute(
            "INSERT INTO documents (id, filename, file_type, file_size, status, created_at) "
            "VALUES (?, ?, ?, ?, 'uploading', ?)",
            (doc_id, file.filename, file_type, file_size, now),
        )
        await db.commit()
    finally:
        await db.close()

    # 异步处理文档
    await document_service.process_document(doc_id, file_path, file.filename)

    return {
        "document": DocumentResponse(
            id=doc_id,
            filename=file.filename,
            file_type=file_type,
            file_size=file_size,
            status="uploading",
            chunk_count=0,
            error_message=None,
            created_at=now,
        ).model_dump()
    }


@router.get("/api/documents", response_model=DocumentListResponse)
async def list_documents():
    """获取所有文档列表"""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM documents ORDER BY created_at DESC")
        rows = await cursor.fetchall()
        documents = [DocumentResponse(**dict(r)) for r in rows]
        return DocumentListResponse(documents=documents)
    finally:
        await db.close()


@router.get("/api/documents/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str):
    """获取文档处理状态"""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, status, chunk_count, error_message FROM documents WHERE id = ?",
            (document_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return DocumentStatusResponse(
                document={"id": document_id, "status": "not_found", "progress": "文档不存在"}
            )

        status_map = {
            "uploading": "正在上传...",
            "parsing": "正在解析文档...",
            "chunking": "正在分块处理...",
            "embedding": "正在向量化...",
            "completed": "处理完成",
            "failed": f"处理失败: {row['error_message'] or '未知错误'}",
        }
        return DocumentStatusResponse(
            document={
                "id": row["id"],
                "status": row["status"],
                "progress": status_map.get(row["status"], row["status"]),
                "chunk_count": row["chunk_count"],
            }
        )
    finally:
        await db.close()


@router.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    """删除文档及其向量数据"""
    logger.info(f"删除文档: {document_id}")

    # 删除向量数据
    document_service.delete_document_vectors(document_id)

    # 删除数据库记录
    db = await get_db()
    try:
        await db.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        await db.commit()
    finally:
        await db.close()

    return Response(status_code=204)


# ========================================
# 错题集接口
# ========================================

@router.get("/api/bad-cases", response_model=BadCaseListResponse)
async def list_bad_cases(use_as_example: Optional[int] = Query(None)):
    """获取错题集列表"""
    db = await get_db()
    try:
        if use_as_example is not None:
            cursor = await db.execute(
                "SELECT * FROM bad_cases WHERE use_as_example = ? ORDER BY created_at DESC",
                (use_as_example,),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM bad_cases ORDER BY created_at DESC"
            )
        rows = await cursor.fetchall()
        bad_cases = [BadCaseResponse(**dict(r)) for r in rows]
        return BadCaseListResponse(bad_cases=bad_cases)
    finally:
        await db.close()


@router.put("/api/bad-cases/{bad_case_id}", response_model=dict)
async def update_bad_case(bad_case_id: str, req: BadCaseUpdateRequest):
    """更新错题答案和范例标记"""
    now = datetime.now().isoformat()
    db = await get_db()
    try:
        await db.execute(
            "UPDATE bad_cases SET correct_answer = ?, use_as_example = ?, updated_at = ? "
            "WHERE id = ?",
            (req.correct_answer, 1 if req.use_as_example else 0, now, bad_case_id),
        )
        await db.commit()
    finally:
        await db.close()

    return {
        "bad_case": {
            "id": bad_case_id,
            "correct_answer": req.correct_answer,
            "use_as_example": req.use_as_example,
            "updated_at": now,
        }
    }


@router.delete("/api/bad-cases/{bad_case_id}")
async def delete_bad_case(bad_case_id: str):
    """删除错题"""
    db = await get_db()
    try:
        await db.execute("DELETE FROM bad_cases WHERE id = ?", (bad_case_id,))
        await db.commit()
    finally:
        await db.close()
    return Response(status_code=204)
