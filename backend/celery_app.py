"""Celery 实例配置

用途：将耗时较长的文档索引（解析 → 分块 → 向量化 → 入库）迁移到后台 Worker 执行，
避免 Gunicorn 多进程下 asyncio.create_task 任务被抢占或随请求结束而丢失。

本地开发：
    celery -A celery_app worker --loglevel=info --concurrency=2
Docker / K8s：
    celery -A celery_app worker --loglevel=info --queues=chatrag_queue --concurrency=1
"""

import os
import sys
from pathlib import Path
from celery import Celery

# 确保项目根目录在 Python 路径中（与 main.py 保持一致）
# Celery Worker 启动时需要，否则 tasks.py 内部 import models 等包会失败
sys.path.insert(0, str(Path(__file__).parent))

from config import settings

# 队列名：API 与 Worker 共用，可通过环境变量覆盖
CELERY_QUEUE = os.getenv("CELERY_QUEUE", settings.celery_queue)

celery_app = Celery(
    "chatrag",
    broker=settings.celery_broker_url,
    backend=settings.celery_backend_url,
    include=["tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
    task_acks_late=True,
    broker_connection_retry_on_startup=True,
    # 默认路由到本服务队列，便于多项目共用 Redis 时隔离
    task_routes={
        "tasks.*": {"queue": CELERY_QUEUE},
    },
)


@celery_app.task(name="health.check")
def health_check():
    """简单心跳任务，用于验证 Celery 与 Redis 连通性。"""
    return "ok"