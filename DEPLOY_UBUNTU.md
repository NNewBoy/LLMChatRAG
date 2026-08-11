# LLMChatRAG Ubuntu 部署指南

本文档介绍如何将 LLMChatRAG 部署到 Ubuntu 服务器上。

## 目录

- [环境要求](#环境要求)
- [1. 系统准备](#1-系统准备)
- [2. 安装 Python 环境](#2-安装-python-环境)
- [3. 安装 Node.js 环境](#3-安装-nodejs-环境)
- [4. 部署后端服务](#4-部署后端服务)
- [5. 构建前端](#5-构建前端)
- [6. 配置 Nginx](#6-配置-nginx)
- [7. 配置 Systemd 服务](#7-配置-systemd-服务)
- [8. 防火墙配置](#8-防火墙配置)
- [9. SSL/HTTPS 配置（可选）](#9-sslhttps-配置可选)
- [10. 常用运维命令](#10-常用运维命令)
- [11. Docker Compose 部署](#11-docker-compose-部署)
- [12. Jenkins CI/CD + K8s 部署](#12-jenkins-cicd--k8s-部署)
- [故障排查](#故障排查)

---

## 环境要求

| 组件 | 版本要求 |
|------|---------|
| Ubuntu | 20.04 LTS 或更高版本 |
| Python | 3.11+（推荐 3.12） |
| Node.js | 18+（构建前端需要，生产环境可不装） |
| Redis | 7+（Celery 异步任务依赖） |
| Nginx | 1.18+ |
| LLM API Key | DeepSeek / OpenAI 兼容模型 |
| Embedding API Key | 硅基流动或其他 OpenAI 兼容 Embedding 服务 |

> **说明**: 本项目使用 DeepAgents + LlamaIndex，后端默认端口 `8003`（可通过 `.env` 的 `PORT` 修改），前端部署在 `/llmchatrag/` 子路径。微服务架构采用 Uvicorn + Gunicorn（多进程并发）+ Celery + Redis（异步任务队列），支持 Docker 容器化与 Jenkins CI/CD。

---

## 1. 系统准备

### 更新系统

```bash
sudo apt update && sudo apt upgrade -y
```

### 安装基础依赖

```bash
sudo apt install -y curl wget git build-essential
```

### 安装 Redis（Celery 异步任务依赖）

```bash
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
# 验证：redis-cli ping → PONG
```

### 创建项目目录

```bash
sudo mkdir -p /var/LLMChatRAG
sudo chown $USER:$USER /var/LLMChatRAG
```

### 克隆项目

```bash
cd /var/LLMChatRAG
git clone <你的仓库地址> .
# 或者使用 scp/rsync 从本地上传
# scp -r ./LLMChatRAG user@server:/var/LLMChatRAG/
```

---

## 2. 安装 Python 环境

### 安装 Python 3.11

```bash
# 添加 Python 3.11 PPA
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# 安装 Python 3.11 及相关工具
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
```

### 验证安装

```bash
python3.11 --version
# 应输出: Python 3.11.x
```

### 创建虚拟环境

```bash
cd /var/LLMChatRAG/backend

# 创建虚拟环境
python3.11 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip
```

### 安装后端依赖

```bash
pip install -r requirements.txt
```

> **说明**: `faiss-cpu` 在某些架构上可能需要从源码编译，若安装失败可尝试 `pip install faiss-cpu==1.9.0.post1 --no-cache-dir` 或先安装 `libopenblas-dev`：
> ```bash
> sudo apt install -y libopenblas-dev libomp-dev
> ```

---

## 3. 安装 Node.js 环境

### 使用 NodeSource 安装 Node.js 18

```bash
# 添加 NodeSource 仓库
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -

# 安装 Node.js
sudo apt install -y nodejs

# 验证安装
node --version  # 应输出: v18.x.x
npm --version   # 应输出: 9.x.x 或更高
```

### 安装前端依赖

```bash
cd /var/LLMChatRAG/frontend

# 安装依赖
npm install
```

---

## 4. 部署后端服务

### 配置环境变量

```bash
cd /var/LLMChatRAG/backend

# 从模板创建 .env 文件
cp .env.example .env

# 编辑 .env 文件，填入 API Key 等配置
nano .env
```

> **必填项**: `LLM_API_KEY` 和 `EMBEDDING_API_KEY` 必须配置为实际值，否则 Agent 对话与 RAG 功能无法使用。

### .env 主要配置项

| 变量 | 说明 | 示例值 |
|------|------|--------|
| `HOST` | 服务监听地址 | `0.0.0.0` |
| `PORT` | 服务监听端口 | `8003` |
| `LLM_MODEL` | LLM 模型名称 | `deepseek-chat` |
| `LLM_API_KEY` | LLM API 密钥 | `sk-xxxx` |
| `LLM_API_BASE_URL` | LLM API Base URL | `https://api.deepseek.com/v1` |
| `EMBEDDING_MODEL` | Embedding 模型 | `BAAI/bge-large-zh-v1.5` |
| `EMBEDDING_API_KEY` | Embedding API 密钥 | `sk-xxxx` |
| `EMBEDDING_API_BASE_URL` | Embedding API Base URL | `https://api.siliconflow.cn/v1` |
| `EMBEDDING_PROVIDER` | Embedding 提供方式 (llama_index/siliconflow) | `siliconflow` |
| `SQLITE_DB_PATH` | SQLite 数据库路径 | `./data/sqlite/chatrag.db` |
| `BAD_CASE_DB_PATH` | 错题集数据库路径（为空则使用主库） | （留空） |
| `FAISS_DB_PATH` | FAISS 向量数据库路径 | `./data/faiss/` |
| `ENABLE_QUERY_REWRITING` | 启用 Query 改写 | `true` |
| `ENABLE_HYBRID_SEARCH` | 启用混合检索 | `false` |
| `ENABLE_RERANKING` | 启用重排序 | `false` |
| `SEARCH_API_KEY` | 联网搜索 API Key（可选） | （留空） |
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `LOG_FILE` | 日志文件路径 | `./logs/app.log` |

> **端口说明**: 若修改 `PORT`，需同步更新 `frontend/vite.config.js` 中的代理 `target` 以及本文档第 6 节的 Nginx `proxy_pass` 配置。

### 创建数据目录

后端启动时会自动创建以下目录，也可手动创建：

```bash
mkdir -p /var/LLMChatRAG/backend/data/sqlite
mkdir -p /var/LLMChatRAG/backend/data/faiss
mkdir -p /var/LLMChatRAG/backend/data/uploads
mkdir -p /var/LLMChatRAG/backend/logs
```

### 测试后端启动

```bash
cd /var/LLMChatRAG/backend
source venv/bin/activate

# 测试运行
uvicorn main:app --host 127.0.0.1 --port 8003

# 如果看到类似以下输出表示成功:
# INFO:     正在初始化应用...
# INFO:     数据库初始化完成: ./data/sqlite/chatrag.db
# INFO:     服务启动: http://0.0.0.0:8003
# INFO:     Uvicorn running on http://127.0.0.1:8003

# 按 Ctrl+C 停止测试
```

### 验证健康检查

```bash
curl http://127.0.0.1:8003/health
# 应返回: {"status":"ok"}
```

---

## 5. 构建前端

### 前端路径配置说明

前端已配置为部署到 `/llmchatrag/` 子路径：

- `vite.config.js` 中 `base: '/llmchatrag/'`
- `src/router/index.js` 中 `createWebHistory(import.meta.env.BASE_URL)`
- `src/api/client.js` 中 axios `baseURL` 与 SSE `fetch` 均使用 `${import.meta.env.BASE_URL}api`
- 开发环境通过 Vite 代理 `/llmchatrag/api` 到后端（`rewrite` 去除前缀）

### 构建生产版本

```bash
cd /var/LLMChatRAG/frontend
npm run build
```

构建完成后，静态文件将生成在 `frontend/dist/` 目录。

### 复制静态文件到 Nginx 目录

```bash
sudo mkdir -p /var/www/llmchatrag
sudo rm -rf /var/www/llmchatrag/*
sudo cp -r /var/LLMChatRAG/frontend/dist/* /var/www/llmchatrag/
sudo chown -R www-data:www-data /var/www/llmchatrag
```

---

## 6. 配置 Nginx

### 安装 Nginx

```bash
sudo apt install -y nginx
```

### 创建站点配置

```bash
sudo nano /etc/nginx/sites-available/LLMChatRAG
```

### Nginx 配置内容

```nginx
# 静态文件目录结构:
# /var/www/llmchatrag/
# ├── index.html
# └── assets/
#     ├── index-xxx.js
#     └── index-xxx.css

# LLMChatRAG 前端 - 路径: /llmchatrag
location /llmchatrag {
    root /var/www;
    index index.html;
    try_files $uri $uri/ /llmchatrag/index.html;
}

# API 代理（含 SSE 流式支持，关键配置）
# 前端请求 /llmchatrag/api/xxx，proxy_pass 末尾带斜杠会替换 location 匹配部分，
# 即 /llmchatrag/api/models -> http://127.0.0.1:8003/api/models
location /llmchatrag/api/ {
    # 文档上传大小限制（RAG 文档可能较大，按需调整）
    client_max_body_size 10M;

    proxy_pass http://127.0.0.1:8003/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # ====== SSE 流式输出支持 ======
    # 注意: 不要在此设置 proxy_buffering off，否则该路径下所有 API 请求
    # （会话列表、模型列表等普通 GET）都会禁用缓冲，影响页面加载速度。
    # SSE 流式输出由后端响应头 X-Accel-Buffering: no 自动控制，
    # Nginx 会针对该单个响应禁用缓冲，无需 location 级别全局禁用。
    proxy_http_version 1.1;
    proxy_set_header Connection "";   # 清除 Connection 头以启用 HTTP/1.1 keep-alive
    chunked_transfer_encoding on;     # 启用分块传输
    proxy_read_timeout 300s;          # SSE 长连接读超时（对话可能持续较久）
    proxy_send_timeout 300s;
}

# 前端静态资源缓存
location ~* /llmchatrag/.*\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    root /var/www;
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

> **重要**: 本项目对话接口使用 SSE 流式输出，必须设置 `proxy_buffering off`，否则前端无法实时显示思考过程与生成内容，会出现"长时间等待后一次性输出全部内容"的现象。

> **注意**: 以上 location 配置应添加到 Nginx 的 `server {}` 块中。如果服务器上只有一个站点，可以直接替换默认配置；如果已有其他站点，将 location 块添加到现有 server 配置中。

### 完整 Nginx 配置示例（独立站点）

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名或 IP

    # 文档上传大小限制（RAG 文档可能较大，按需调整）
    client_max_body_size 10M;

    # LLMChatRAG 前端
    location /llmchatrag {
        root /var/www;
        index index.html;
        try_files $uri $uri/ /llmchatrag/index.html;
    }

    # API 代理（含 SSE 流式支持）
    # 前端请求 /llmchatrag/api/xxx -> 后端 /api/xxx
    location /llmchatrag/api/ {
        proxy_pass http://127.0.0.1:8003/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 流式输出支持
        # 不设 proxy_buffering off，普通 API 请求保持默认缓冲快速返回；
        # SSE 响应由后端 X-Accel-Buffering: no 头自动禁用缓冲
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        chunked_transfer_encoding on;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    # 前端静态资源缓存
    location ~* /llmchatrag/.*\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        root /var/www;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 部署静态文件

```bash
# 创建目录
sudo mkdir -p /var/www/llmchatrag

# 复制构建产物
sudo cp -r /var/LLMChatRAG/frontend/dist/* /var/www/llmchatrag/

# 设置权限
sudo chown -R www-data:www-data /var/www/llmchatrag

# 验证文件结构
ls -la /var/www/llmchatrag/
# 应该看到: index.html  assets/
```

### 启用站点

```bash
# 创建符号链接
sudo ln -s /etc/nginx/sites-available/LLMChatRAG /etc/nginx/sites-enabled/

# 删除默认站点（可选）
sudo rm /etc/nginx/sites-enabled/default

# 测试配置
sudo nginx -t

# 重载 Nginx
sudo systemctl reload nginx
```

---

## 7. 配置 Systemd 服务

### 创建后端服务文件

```bash
sudo nano /etc/systemd/system/LLMChatRAG.service
```

### 服务配置内容

```ini
[Unit]
Description=LLMChatRAG Backend
After=network.target redis-server.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/var/LLMChatRAG/backend
Environment="PATH=/var/LLMChatRAG/backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/var/LLMChatRAG/backend/.env
ExecStart=/var/LLMChatRAG/backend/venv/bin/gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 127.0.0.1:8003 --timeout 120 --access-logfile - --error-logfile -
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

> **注意**:
> - `--port 8003` 必须与 `.env` 中的 `PORT` 及 Nginx `proxy_pass` 保持一致。
> - 使用 Gunicorn 管理 2 个 Uvicorn Worker 实现多进程并发，生产环境不建议使用 `--reload`。
> - 后端依赖 Redis，systemd 已配置 `After=redis-server.service` 确保启动顺序。

### 设置目录权限

```bash
# 确保项目目录可访问
sudo chmod -R 755 /var/LLMChatRAG

# 确保数据目录可写（SQLite、FAISS、上传文件、日志）
sudo chmod -R 777 /var/LLMChatRAG/backend/data
sudo chmod -R 777 /var/LLMChatRAG/backend/logs
```

### 启动服务

```bash
# 重载 systemd 配置
sudo systemctl daemon-reload

# 启动后端 API 与 Celery Worker
sudo systemctl start LLMChatRAG LLMChatRAG-celery

# 设置开机自启
sudo systemctl enable LLMChatRAG LLMChatRAG-celery

# 查看服务状态
sudo systemctl status LLMChatRAG
sudo systemctl status LLMChatRAG-celery
```

### Celery Worker 服务（异步文档索引）

```bash
sudo nano /etc/systemd/system/LLMChatRAG-celery.service
```

```ini
[Unit]
Description=LLMChatRAG Celery Worker
After=network.target redis-server.service LLMChatRAG.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/var/LLMChatRAG/backend
Environment="PATH=/var/LLMChatRAG/backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/var/LLMChatRAG/backend/.env
ExecStart=/var/LLMChatRAG/backend/venv/bin/celery -A celery_app worker --loglevel=info --concurrency=1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

> **说明**: Celery Worker 负责后台执行文档索引任务（解析 → 分块 → 向量化 → 入库），避免 Gunicorn 多进程下 asyncio.create_task 任务被抢占。未启动 Worker 时，后端会回退到 asyncio.create_task，但稳定性不如 Celery。

---

## 8. 防火墙配置

### 使用 UFW 配置防火墙

```bash
# 启用防火墙
sudo ufw enable

# 允许 SSH
sudo ufw allow ssh

# 允许 HTTP
sudo ufw allow 80/tcp

# 允许 HTTPS（如果需要）
sudo ufw allow 443/tcp

# 查看防火墙状态
sudo ufw status
```

> **注意**: 后端运行在 `127.0.0.1:8003`，仅本机可访问，无需开放 8003 端口。外部请求通过 Nginx 80/443 端口转发。

---

## 9. SSL/HTTPS 配置（可选）

### 使用 Let's Encrypt 免费证书

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期测试
sudo certbot renew --dry-run
```

Certbot 会自动修改 Nginx 配置，添加 HTTPS 支持。

---

## 10. 常用运维命令

### 服务管理

```bash
# 启动后端服务
sudo systemctl start LLMChatRAG

# 停止后端服务
sudo systemctl stop LLMChatRAG

# 重启后端服务
sudo systemctl restart LLMChatRAG

# 查看服务状态
sudo systemctl status LLMChatRAG

# 查看服务日志
sudo journalctl -u LLMChatRAG -f

# 查看最近 100 行日志
sudo journalctl -u LLMChatRAG -n 100
```

### Nginx 管理

```bash
# 测试配置
sudo nginx -t

# 重载配置
sudo systemctl reload nginx

# 重启 Nginx
sudo systemctl restart nginx

# 查看 Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 更新项目

```bash
cd /var/LLMChatRAG

# 拉取最新代码
git pull origin main

# 更新后端依赖
cd backend
source venv/bin/activate
pip install -r requirements.txt

# 重新构建前端
cd ../frontend
npm install
npm run build

# 清空旧文件
sudo rm -rf /var/www/llmchatrag/*

# 复制新的静态文件
sudo cp -r dist/* /var/www/llmchatrag/
sudo chown -R www-data:www-data /var/www/llmchatrag

# 重启后端服务
sudo systemctl restart LLMChatRAG
```

### 数据备份

```bash
# 备份 SQLite 数据库
cp /var/LLMChatRAG/backend/data/sqlite/chatrag.db /var/LLMChatRAG/backend/data/sqlite/chatrag.db.backup.$(date +%Y%m%d)

# 备份 FAISS 向量数据
cp -r /var/LLMChatRAG/backend/data/faiss /var/LLMChatRAG/backend/data/faiss.backup.$(date +%Y%m%d)

# 定时备份（添加到 crontab）
# 每天凌晨 3 点备份数据库与向量库
0 3 * * * cp /var/LLMChatRAG/backend/data/sqlite/chatrag.db /var/LLMChatRAG/backend/data/sqlite/chatrag.db.$(date +\%Y\%m\%d).db
0 3 * * * cp -r /var/LLMChatRAG/backend/data/faiss /var/LLMChatRAG/backend/data/faiss.$(date +\%Y\%m\%d)
```

---

## 11. Docker Compose 部署

> 一键启动 backend + celery-worker + redis + nginx 四个服务，最简部署方式。

### 11.1 准备环境变量

```bash
cd /var/LLMChatRAG
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入 LLM_API_KEY / EMBEDDING_API_KEY
# Docker 模式必须设置 REDIS_HOST=redis
nano backend/.env
```

### 11.2 一键启动

```bash
# 构建 backend / frontend 镜像并启动所有服务
docker compose up -d --build

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f backend
docker compose logs -f celery-worker
```

### 11.3 服务架构

```
用户请求 :80
    │
    └─ Nginx 容器（前端静态 + 反向代理）
            ├── /llmchatrag/          → 静态文件 /var/www/llmchatrag
            └── /llmchatrag/api/      → backend:8000
                                          ├── Gunicorn + 2 Uvicorn Worker
                                          └── Celery Worker 容器（异步文档索引）
                                                  └── Redis :6379
```

### 11.4 数据持久化

| 卷 | 用途 |
|------|------|
| `db-data` | SQLite 数据库 |
| `faiss-data` | FAISS 向量索引 |
| `uploads` | 上传文档 |
| `logs` | 后端日志 |
| `redis-data` | Redis 数据 |

### 11.5 更新与维护

```bash
# 拉取最新代码后重新构建
cd /var/LLMChatRAG
git pull origin main
docker compose up -d --build

# 停止所有服务
docker compose down

# 停止并清除数据卷（谨慎操作）
docker compose down -v
```

### 11.6 宿主机 Nginx 做 SSL 终止（需要 HTTPS 时）

前端容器端口改为内部映射 `127.0.0.1:8080:80`，宿主机 Nginx 反代到容器：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

---

## 12. Jenkins CI/CD + K8s 部署

> 完整配置流程详见 `docs/JENKINS-DOCKER-GUIDE.md`。本节列出关键步骤。

### 12.1 安装 Jenkins

```bash
# 安装 JDK 17
sudo apt install -y openjdk-17-jre-headless

# 安装 Jenkins LTS
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee /usr/share/keyrings/jenkins-keyring.asc > /dev/null
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt update
sudo apt install -y jenkins

sudo systemctl enable jenkins
sudo systemctl start jenkins
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

安装必要插件：`Manage Jenkins → Plugins` → 安装 **Docker**、**Git**、**Pipeline**、**Config File Provider**。

### 12.2 安装 Docker 与 kubectl（Jenkins 服务器）

```bash
# Docker（构建镜像需要）
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins

# kubectl（部署 K8s 需要）
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

### 12.3 配置阿里云 ACR 镜像仓库

1. 登录阿里云控制台 → 容器镜像服务 ACR → 个人版
2. 创建命名空间 `llmproject` 与镜像仓库 `backend_chatrag`、`frontend_chatrag`
3. 记录镜像仓库地址，例如 `crpi-v27gqzero2fjya51.cn-guangzhou.personal.cr.aliyuncs.com`

> **注意**：本项目的 ACR 命名空间为 `llmproject`，镜像名为 `backend_chatrag` / `frontend_chatrag`，与 LLMBLOG（命名空间 `llmblog`）独立，便于多项目共用一个 ACR 账号。

### 12.4 配置 Jenkins 凭据

进入 `Manage Jenkins → Credentials → System → Global credentials`：

| 凭据 ID | 类型 | 说明 |
|---------|------|------|
| `github-cred` | Username with password | GitHub 用户名 / Token（需 repo 权限） |
| `aliyun-acr` | Username with password | 阿里云 ACR 账号 / 密码 |
| `k8s-kubeconfig` | Secret File | 上传 K8s Master 的 kubeconfig 文件 |
| `opencode-api-key` | Secret Text | DeepSeek LLM API Key |
| `siliconflow-api-key` | Secret Text | 硅基流动 Embedding API Key |

### 12.5 创建流水线项目

1. Jenkins 首页 → `New Item` → 选「流水线」→ 命名 `LLMChatRAG-CICD`
2. `Pipeline` → `Definition` → `Pipeline script from SCM`：
   - Repository URL：`https://github.com/<你的用户名>/LLMChatRAG.git`
   - Credentials：`github-cred`
   - Branch：`*/main`
   - Script Path：`Jenkinsfile`
3. `Build Triggers` → 勾选 `Poll SCM` → `H/5 * * * *`（每 5 分钟轮询）
4. 保存并点击「立即构建」，查看 Console Output 验证全流程

### 12.6 流水线执行流程

`Jenkinsfile` 定义了三个阶段：

```
拉取代码 → 构建并推送镜像（并行）→ 部署到 K8s 集群
```

| 阶段 | 动作 |
|------|------|
| 拉取代码 | `checkout scm` 从 GitHub main 分支拉取 |
| 构建后端镜像 | `docker build -f backend/Dockerfile backend/` → 推送 ACR |
| 构建前端镜像 | `docker build -f frontend/Dockerfile frontend/` → 推送 ACR |
| 镜像标签 | `构建号-GitCommit短哈希`（每次唯一可追溯） |
| 部署 K8s | `kubectl set image` 滚动更新 backend-chatrag/frontend-chatrag/celery-worker-chatrag |
| 等待完成 | `kubectl rollout status` 确认滚动更新成功 |

> ARM 架构机器（如 Apple M 系列）构建时必须加 `--platform linux/amd64`，Jenkinsfile 已含此参数。

### 12.7 K8s 集群资源规划与端口冲突分析

> **重要**：LLMBLOG 与 LLMChatRAG 同时部署在同一个 K8s 集群的 `app` 命名空间，部分基础资源共用，业务资源通过命名前缀隔离。

#### 共用基础资源（来自 LLMBLOG 的 `k8s/`）

| 资源 | 名称 | 说明 |
|------|------|------|
| Namespace | `app` | 两个项目共用 |
| Redis Service | `redis:6379` | 两个项目共用同一 Redis 实例 |
| ACR 拉取密钥 | `aliyun-acr-secret` | 共用 |

**Redis DB 分配**（避免键冲突）：

| 项目 | Broker DB | Backend DB |
|------|-----------|-----------|
| LLMBLOG | 0 | 1 |
| LLMChatRAG | 2 | 3 |

#### 独立业务资源（本项目 `k8s/`）

| 资源 | 类型 | 名称 | 避免冲突 |
|------|------|------|---------|
| 配置 | ConfigMap | `chatrag-config` | 与 LLMBLOG `app-config` 区分 |
| 密钥 | Secret | `chatrag-secret` | 与 LLMBLOG `app-secret` 区分 |
| 存储 | PV | `pv-chatrag-db/faiss/uploads` | hostPath 为 `/data/chatrag/*`，与 LLMBLOG `/data/llmblog/*` 区分 |
| 存储 | PVC | `chatrag-db/faiss-data/uploads` | 加 `chatrag-` 前缀 |
| 后端 | Deployment + Service | `backend-chatrag` | 与 LLMBLOG `backend` 区分 |
| 前端 | Deployment + Service | `frontend-chatrag` | 与 LLMBLOG `frontend` 区分 |
| Worker | Deployment | `celery-worker-chatrag` | 与 LLMBLOG `celery-worker` 区分 |
| 入口 | Ingress | `chatrag-ingress` | 与 LLMBLOG `app-ingress` 区分，路由 `/llmchatrag/*` 子路径 |

#### Ingress 路径规划

| 前缀路径 | 路由目标 | 说明 |
|---------|---------|------|
| `/` 和 `/api` 和 `/llmblog_uploads` | LLMBLOG `frontend` / `backend` | 由 LLMBLOG `app-ingress` 定义 |
| `/llmchatrag` | LLMChatRAG `frontend-chatrag` | **LLMChatRAG 前端子路径** |
| `/llmchatrag/api` | LLMChatRAG `backend-chatrag` | **LLMChatRAG API 子路径** |

#### 端口冲突检查

| 组件 | LLMBLOG | LLMChatRAG | 是否冲突 |
|------|---------|------------|---------|
| 后端容器端口 | 8000 | 8000 | **否**（K8s Service 网络隔离，ClusterIP + DNS 域名区分） |
| 后端 Service | `backend:8000` | `backend-chatrag:8000` | **否**（不同 Service 名） |
| 前端容器端口 | 80 | 80 | **否**（同上） |
| Redis 实例 | 容器 6379 | 共用 | **否**（共用一个 Redis Pod，通过 DB 0-1/2-3 隔离） |
| Ingress NodePort | 31080/31443 | 共用 | **否**（共用 ingress-nginx-controller） |
| 数据卷 hostPath | `/data/llmblog/*` | `/data/chatrag/*` | **否**（不同目录） |

> **结论**：所有端口通过 K8s Service 名称（ClusterIP + DNS）隔离，不存在端口冲突。

### 12.8 K8s 集群一次性配置

在 K8s Master 节点执行一次：

```bash
# 创建 ACR 拉取密钥（如 LLMBLOG 部署时已创建，跳过此步）
kubectl create secret docker-registry aliyun-acr-secret \
  --namespace=app \
  --docker-server=crpi-v27gqzero2fjya51.cn-guangzhou.personal.cr.aliyuncs.com \
  --docker-username=你的ACR用户名 \
  --docker-password=ACR访问凭证固定密码 2>/dev/null || echo "secret 已存在，跳过"

# 创建 LLMChatRAG 数据目录（与 LLMBLOG 的 /data/llmblog 独立）
sudo mkdir -p /data/chatrag/db /data/chatrag/faiss /data/chatrag/uploads
sudo chmod -R 777 /data/chatrag

# 应用 LLMChatRAG 业务资源
# 注意：namespace 与 redis 由 LLMBLOG 的 k8s/ 共用，不在此重复 apply
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/celery-worker.yaml
kubectl apply -f k8s/frontend.yaml
kubectl apply -f k8s/ingress.yaml --validate=false
```

后续每次提交代码，Jenkins 自动构建并滚动更新 Deployment，无需手动操作。

### 12.9 更新 K8s Secret（API Key 等敏感配置）

> **重要**：`k8s/secret.yaml` 含 API Key 等敏感信息，已加入 `.gitignore`，**不通过 yaml apply**（避免 Git 中的占位符覆盖集群真实值）。Jenkinsfile 已集成「更新 K8s Secret」阶段，每次构建自动从 Jenkins Credentials 注入。

#### 方式一：手动命令更新（首次部署或临时更换 Key）

在 K8s Master 节点执行：

```bash
# 用 kubectl create --dry-run 生成并应用（无需手动 base64 编码）
kubectl create secret generic chatrag-secret \
  --namespace=app \
  --from-literal=LLM_API_KEY="sk-你的真实DeepSeek密钥" \
  --from-literal=LLM_API_BASE_URL="https://api.deepseek.com/v1" \
  --from-literal=LLM_MODEL="deepseek-chat" \
  --from-literal=EMBEDDING_API_KEY="sk-你的真实硅基流动密钥" \
  --from-literal=EMBEDDING_API_BASE_URL="https://api.siliconflow.cn/v1" \
  --from-literal=EMBEDDING_MODEL="BAAI/bge-large-zh-v1.5" \
  --dry-run=client -o yaml | kubectl apply -f -

# 更新后重启 Pod 使新 Secret 生效
kubectl rollout restart deployment/backend-chatrag -n app
kubectl rollout restart deployment/celery-worker-chatrag -n app
```

#### 方式二：通过 Jenkins Credentials 自动注入（推荐，已集成到 Jenkinsfile）

Jenkinsfile 已含「更新 K8s Secret」阶段，每次构建自动执行——只需在 Jenkins 配置好凭据即可。

**前提条件**：已在 §12.4 中配置以下 Jenkins 凭据：

| 凭据 ID | 类型 | 说明 |
|---------|------|------|
| `opencode-api-key` | Secret Text | DeepSeek LLM API Key |
| `siliconflow-api-key` | Secret Text | 硅基流动 Embedding API Key |

**Jenkinsfile 执行流程**：

```
拉取代码 → 构建并推送镜像 → 更新 K8s Secret → 部署到 K8s 集群
                                        ↓
                         从 Jenkins Credentials 读取 API Key
                                        ↓
                         kubectl create secret --dry-run | kubectl apply
                                        ↓
                         后续滚动更新 Pod 自动读取最新 Secret
```

**更换 API Key 时**：只需在 Jenkins `Manage Jenkins → Credentials` 中更新凭据值，下次构建自动生效，无需手动操作 K8s。

### 12.10 K8s 宿主机 Nginx 配置

K8s 部署完成后，宿主机 Nginx 做 SSL 终止，将请求代理到 **ingress-nginx-controller 的 NodePort**，由 Ingress 根据 Host 头路由到对应 Service。

```nginx
# HTTP → HTTPS 跳转
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}

# SSL 终止 + 反代到 ingress-nginx NodePort
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:31080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

> **固定 NodePort**：
> ```bash
> kubectl patch svc ingress-nginx-controller -n ingress-nginx -p '{
>   "spec": {
>     "ports": [
>       {"name": "http", "port": 80, "nodePort": 31080, "targetPort": 80},
>       {"name": "https", "port": 443, "nodePort": 31443, "targetPort": 443}
>     ]
>   }
> }'
> ```

### 12.11 K8s 运维命令

```bash
# Pod / Service / Deployment 状态
kubectl get pods -n app -o wide
kubectl get svc -n app
kubectl get deploy -n app

# 查看日志（LLMChatRAG 业务 Pod 加 -chatrag 后缀）
kubectl logs -n app -l app=backend-chatrag --tail=50
kubectl logs -n app -l app=celery-worker-chatrag --tail=50

# 滚动更新后回滚
kubectl rollout undo deployment/backend-chatrag -n app
kubectl rollout undo deployment/frontend-chatrag -n app
kubectl rollout undo deployment/celery-worker-chatrag -n app

# 进入 Pod 调试
kubectl exec -it deploy/backend-chatrag -n app -- bash
kubectl exec -it deploy/redis -n app -- redis-cli

# 健康检查（LLMChatRAG 后端）
kubectl exec -it deploy/backend-chatrag -n app -- curl -s http://127.0.0.1:8000/health
```

---

## 故障排查

### 1. 后端服务无法启动

```bash
# 查看详细日志
sudo journalctl -u LLMChatRAG -n 50 --no-pager

# 手动测试启动
cd /var/LLMChatRAG/backend
source venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8003
```

常见原因：
- `.env` 中 `LLM_API_KEY` 或 `EMBEDDING_API_KEY` 未配置
- Python 依赖未完整安装（尤其 `faiss-cpu`）
- 端口被占用：`sudo lsof -i:8003`

### 2. 前端显示空白

```bash
# 检查静态文件是否存在
ls -la /var/www/llmchatrag/

# 检查 Nginx 配置
sudo nginx -t

# 确认访问路径为 http://your-domain.com/llmchatrag/
# 注意末尾斜杠，路由会重定向到 /llmchatrag/chat
```

### 3. API 请求 404

```bash
# 确认后端服务正在运行
curl http://127.0.0.1:8003/health
# 应返回: {"status":"ok"}

# 检查 Nginx 代理配置
sudo nginx -t

# 确认 /llmchatrag/api/ 代理配置正确，proxy_pass 末尾带斜杠
# 前端请求 /llmchatrag/api/xxx 应被代理到后端 /api/xxx
```

### 4. 对话不流式输出（内容一次性全部出现）

SSE 流式输出依赖后端响应头 `X-Accel-Buffering: no`（已在 [chat.py](file:///d:/AIProjects/LLMChatRAG/backend/routes/chat.py) / [rag.py](file:///d:/AIProjects/LLMChatRAG/backend/routes/rag.py) 的 `StreamingResponse` 中设置），Nginx 会针对该响应自动禁用缓冲。

检查要点：

```bash
# 1. 确认 Nginx 未忽略 X-Accel-Buffering 头
# 配置中不应出现: proxy_ignore_headers X-Accel-Buffering;
sudo nginx -T 2>/dev/null | grep proxy_ignore_headers

# 2. 确认 /llmchatrag/api/ 代理配置了 HTTP/1.1 与长连接
#   proxy_http_version 1.1;
#   proxy_set_header Connection "";

# 3. 确认后端 SSE 响应头包含 X-Accel-Buffering: no
curl -i -N -X POST http://127.0.0.1:8003/api/chat/conversations/<id>/messages \
  -H "Content-Type: application/json" -d '{"content":"hi","model":"xxx"}' | head -20
```

> **注意**: 不要在 `/llmchatrag/api/` location 设置 `proxy_buffering off`，否则会拖慢普通 API 请求。SSE 禁用缓冲由响应头自动完成。

### 5. 文档上传失败

#### 413 Request Entity Too Large

Nginx 默认上传限制 1MB，RAG 文档通常较大需调高：

```bash
# 检查当前 Nginx 配置中的 client_max_body_size
sudo nginx -T 2>/dev/null | grep client_max_body_size

# 在 /llmchatrag/api/ location 块或 server 块中添加（建议 10M 或更大）:
#   client_max_body_size 10M;

# 修改后重载
sudo nginx -t && sudo systemctl reload nginx
```

#### 上传目录权限问题

```bash
# 检查上传目录权限
ls -la /var/LLMChatRAG/backend/data/uploads/

# 确认目录可写
sudo chmod -R 777 /var/LLMChatRAG/backend/data
```

### 6. RAG 检索报错

```bash
# 检查 FAISS 目录是否有数据
ls -la /var/LLMChatRAG/backend/data/faiss/

# 检查 Embedding API Key 是否配置正确
cat /var/LLMChatRAG/backend/.env | grep EMBEDDING

# 查看 RAG 相关日志
sudo journalctl -u LLMChatRAG -f | grep -i rag
```

### 7. 权限问题

```bash
# 修复文件权限
sudo chown -R www-data:www-data /var/LLMChatRAG
sudo chown -R www-data:www-data /var/www/llmchatrag
sudo chmod -R 755 /var/LLMChatRAG
sudo chmod -R 777 /var/LLMChatRAG/backend/data
sudo chmod -R 777 /var/LLMChatRAG/backend/logs
```

### 8. MCP 工具加载失败（npx 找不到）

日志出现 `MCP 工具加载失败: [Errno 2] No such file or directory: 'npx'` 或 `'/usr/bin/npx'`：

```bash
# 1. 确认 Node.js 已安装并查找 npx 实际路径
which npx
ls -la /usr/local/bin/npx /usr/bin/npx 2>/dev/null

# 2. 修复方式 A（推荐）：在 .env 中配置 NPX_PATH 为绝对路径
echo "NPX_PATH=$(which npx)" >> /var/LLMChatRAG/backend/.env
# 或手动编辑: nano /var/LLMChatRAG/backend/.env  ->  NPX_PATH=/usr/local/bin/npx

# 3. 修复方式 B：确保 systemd 服务的 PATH 包含 npx 所在目录
# 编辑 /etc/systemd/system/LLMChatRAG.service:
#   Environment="PATH=/var/LLMChatRAG/backend/venv/bin:/usr/local/bin:/usr/bin:/bin"

# 4. 修改后重载并重启
sudo systemctl daemon-reload
sudo systemctl restart LLMChatRAG

# 5. 首次运行 npx 会下载 bing-cn-mcp，可能较慢，可手动预热
sudo -E npx -y bing-cn-mcp --help
```

> **说明**: 错误日志会同时打印 `npx_path` 与 `PATH`，便于诊断。若 `shutil.which("npx")` 返回 None，说明服务进程的 PATH 中确实没有 npx，请用方式 A 显式指定路径。

---

## 完整部署检查清单

- [ ] Ubuntu 系统已更新
- [ ] Python 3.11+ 已安装
- [ ] Node.js 18+ 已安装
- [ ] 项目代码已克隆/上传
- [ ] Python 虚拟环境已创建
- [ ] 后端依赖已安装（含 faiss-cpu）
- [ ] `.env` 文件已配置（含 `LLM_API_KEY`、`EMBEDDING_API_KEY`）
- [ ] 数据目录已创建且有写权限
- [ ] 后端服务可以手动启动
- [ ] 健康检查接口返回正常 (`/health`)
- [ ] 前端已构建（`npm run build`）
- [ ] 静态文件已复制到 `/var/www/llmchatrag/`
- [ ] Nginx 已配置（含 SSE 流式 `proxy_buffering off`）
- [ ] Systemd 服务已创建并启动
- [ ] 防火墙已配置
- [ ] 服务已设置开机自启
- [ ] 浏览器可以正常访问 `http://your-domain.com/llmchatrag/`
- [ ] 对话流式输出正常（思考过程实时显示）

---

如有问题，请查看项目日志或提交 Issue。

**日志位置**:
- 后端日志: `sudo journalctl -u LLMChatRAG`
- 后端应用日志: `/var/LLMChatRAG/backend/logs/app.log`
- Nginx 访问日志: `/var/log/nginx/access.log`
- Nginx 错误日志: `/var/log/nginx/error.log`
