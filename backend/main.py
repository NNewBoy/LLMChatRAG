"""FastAPI 入口

本地开发：uvicorn main:app --reload --host 0.0.0.0 --port 8000
生产启动：gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 120
"""

import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 确保项目根目录在 Python 路径中（Celery Worker / Gunicorn 启动时需要）
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from models.database import init_db
from routes import chat, rag, document, model
from utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("正在初始化应用...")
    settings.ensure_dirs()
    await init_db()
    logger.info(f"数据库初始化完成: {settings.sqlite_db_path}")
    logger.info(f"服务启动: http://{settings.host}:{settings.port}")
    yield
    logger.info("应用关闭")


app = FastAPI(
    title="LLMChatRAG",
    description="同时支持普通聊天 Agent 和 RAG 的在线网站",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS 配置：支持从环境变量读取多个来源（逗号分隔），默认放宽便于本地调试
_cors = os.environ.get("CORS_ORIGINS", "*")
_cors_origins = [o.strip() for o in _cors.split(",") if o.strip()] if _cors != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(model.router)
app.include_router(chat.router)
app.include_router(rag.router)
app.include_router(document.router)


@app.get("/")
async def root():
    return {"name": "LLMChatRAG", "version": "2.0.0", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
