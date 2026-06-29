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
- [故障排查](#故障排查)

---

## 环境要求

| 组件 | 版本要求 |
|------|---------|
| Ubuntu | 20.04 LTS 或更高版本 |
| Python | 3.11+ |
| Node.js | 18+ |
| Nginx | 1.18+ |
| LLM API Key | DeepSeek / OpenAI 兼容模型 |
| Embedding API Key | 硅基流动或其他 OpenAI 兼容 Embedding 服务 |

> **说明**: 本项目使用 DeepAgents + LlamaIndex，后端默认端口 `8003`（可通过 `.env` 的 `PORT` 修改），前端部署在 `/llmchatrag/` 子路径。

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
    proxy_pass http://127.0.0.1:8003/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # ====== SSE 流式输出关键配置 ======
    proxy_http_version 1.1;
    proxy_set_header Connection "";   # 清除 Connection 头以启用 HTTP/1.1 keep-alive
    proxy_buffering off;              # 禁用缓冲，保证 token 实时推送
    proxy_cache off;                  # 禁用缓存
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
    client_max_body_size 50M;

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

        # SSE 流式输出关键配置
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_cache off;
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
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/var/LLMChatRAG/backend
Environment="PATH=/var/LLMChatRAG/backend/venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/var/LLMChatRAG/backend/.env
ExecStart=/var/LLMChatRAG/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8003 --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

> **注意**:
> - `--port 8003` 必须与 `.env` 中的 `PORT` 及 Nginx `proxy_pass` 保持一致。
> - 生产环境不建议使用 `--reload`（仅开发用），Systemd 已提供自动重启。
> - 使用 root 用户运行可避免文件权限问题。如需更安全配置，请创建专用用户并设置相应目录权限。

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

# 启动服务
sudo systemctl start LLMChatRAG

# 设置开机自启
sudo systemctl enable LLMChatRAG

# 查看服务状态
sudo systemctl status LLMChatRAG
```

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

这是 Nginx 缓冲导致的 SSE 问题。检查 `/llmchatrag/api/` location 配置：

```nginx
# 必须包含以下配置
proxy_buffering off;
proxy_http_version 1.1;
proxy_set_header Connection "";
```

修改后重载：`sudo systemctl reload nginx`

### 5. 文档上传失败

```bash
# 检查上传目录权限
ls -la /var/LLMChatRAG/backend/data/uploads/

# 确认目录可写
sudo chmod -R 777 /var/LLMChatRAG/backend/data

# 检查 Nginx 上传大小限制
# 在 server 块中确认 client_max_body_size 设置足够大（默认 1M）
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
