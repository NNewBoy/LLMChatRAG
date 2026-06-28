"""FastAPI 入口，启动服务"""

import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 确保项目根目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from models.database import init_db
from routes import chat, rag, document, model
from utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动前
    logger.info("正在初始化应用...")
    settings.ensure_dirs()
    await init_db()
    logger.info(f"数据库初始化完成: {settings.sqlite_db_path}")
    logger.info(f"服务启动: http://{settings.host}:{settings.port}")
    yield
    # 关闭时
    logger.info("应用关闭")


app = FastAPI(
    title="LLMChatRAG",
    description="同时支持普通聊天 Agent 和 RAG 的在线网站",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为前端域名
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
