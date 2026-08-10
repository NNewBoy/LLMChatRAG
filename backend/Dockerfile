FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# faiss-cpu / pymupdf / lxml 需要编译工具链与系统库
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libopenblas-dev libomp-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖清单安装（利用 Docker 层缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目源码
COPY . .

# 数据目录（SQLite / FAISS / 上传文件 / 日志），由 volume 持久化
RUN mkdir -p data/sqlite data/faiss data/uploads logs

EXPOSE 8000

# Gunicorn 管理 2 个 Uvicorn Worker，实现多进程并发
# 对话接口使用 SSE，--timeout 设大避免长连接被中断
CMD ["gunicorn", "main:app", \
     "--workers", "2", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]