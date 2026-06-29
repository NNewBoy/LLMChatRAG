# LLMChatRAG

> 同时支持普通聊天 Agent 和 RAG（检索增强生成）的在线网站

## 功能特性

- **普通对话模式**：Agent 自动识别意图，普通问题直接回答，涉及知识库的问题自动调用 RAG 工具
- **RAG 对话模式**：直接进入 RAG 流程，基于上传文档进行问答，支持实时调整检索策略
- **多技能 Agent**：通过 SKILL.md 扩展 Agent 能力，DeepAgents 自主决策调用
- **MCP 联网搜索**：通过 MCP 协议集成 bing-cn-mcp，Agent 自主决定是否调用联网搜索和网页抓取工具
- **长期记忆**：SQLite 持久化对话历史，跨会话上下文关联
- **流式对话**：SSE 推送，前端实时展示思考过程与工具调用，支持中途停止
- **图片理解**：支持上传图片，多模态模型理解
- **会话管理**：新建/重命名/删除会话，URL 直达特定会话 (`/chat/{id}`、`/rag/{id}`)
- **混合检索**：向量检索 + BM25 关键词检索，加权融合
- **重排序**：LLM 对检索结果精排，提升答案质量
- **Bad Case 管理**：前端标记错误答案，构建错题集，支持范例回传
- **文档管理**：上传/删除文档，自动解析入库，状态追踪，重复上传检测，支持拖拽上传
- **统一配置**：Chat 和 RAG 页面均通过 header 设置弹窗统一管理模型与检索参数
- **响应式设计**：兼容 PC 端与移动端，自适应布局
- **UI 设计**：Glassmorphism + Dark Mode 风格，玻璃态质感，统一深色主题

## 技术栈

### 前端
- Vue 3 + Vite + Element Plus + Pinia + Vue Router + Axios
- marked / highlight.js (Markdown 渲染与代码高亮)

### 后端
- Python 3.11+ + FastAPI + SQLite (aiosqlite) + FAISS
- DeepAgents (Agent 框架) + LlamaIndex (RAG 框架)
- LangChain (init_chat_model) + langchain-mcp-adapters (MCP 工具) + Pydantic + uvicorn

## 项目结构

```
LLMChatRAG/
├── backend/                # 后端
│   ├── main.py             # FastAPI 入口
│   ├── config.py           # 环境变量配置
│   ├── models/             # 数据库模型 (SQLite)
│   ├── routes/             # API 路由 (chat/rag/document/model)
│   ├── agent/              # Agent 模块 (DeepAgents)
│   ├── rag/                # RAG 模块 (LlamaIndex)
│   ├── services/           # 业务逻辑层
│   ├── schemas/            # 请求/响应模型
│   ├── utils/              # 工具 (SSE/Logger)
│   ├── data/               # 数据存储 (SQLite/FAISS/上传文件)
│   ├── requirements.txt
│   └── .env.example
├── frontend/               # 前端
│   ├── src/
│   │   ├── views/          # 页面 (ChatView/RAGView/DocumentView)
│   │   ├── components/     # 组件 (chat/rag/document/common)
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── api/            # API 封装 (含 SSE)
│   │   ├── router/         # 路由
│   │   └── assets/         # 样式
│   ├── vite.config.js
│   └── package.json
└── README.md
```

## 快速开始

### 1. 后端启动

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入 API Key 等配置
python main.py
# 服务启动在 http://localhost:8000
# API 文档: http://localhost:8000/docs
```

### 2. 前端启动

```bash
cd frontend
npm install
npm run dev
# 开发服务器启动在 http://localhost:5173
```

### 3. 使用说明

1. **普通对话**：访问 `/chat`，点击 header 右侧设置图标选择模型、开关意图识别，输入问题即可对话。开启意图识别后，Agent 会自动判断是否需要查询知识库。
2. **RAG 对话**：访问 `/rag`，先上传文档（在文档管理页面），然后在 RAG 对话页面基于文档提问。点击 header 右侧设置图标可调整 LLM 模型、Embedding 模型、Query 改写、混合检索、重排序等参数。
3. **文档管理**：访问 `/documents`，上传 PDF/Word/HTML/TXT 文档，系统自动解析、分块、向量化并存入 FAISS。支持重复上传检测和删除时同步清理向量数据与上传文件。
4. **错题集**：在 RAG 对话中标记错误答案，在文档管理页面的错题集 Tab 中编辑正确答案，可设为范例供 LLM 参考。

## 环境变量配置

关键环境变量（详见 `.env.example`）：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_MODEL` | LLM 模型名称 | deepseek-chat |
| `LLM_API_KEY` | LLM API Key | - |
| `LLM_API_BASE_URL` | LLM API Base URL | https://api.deepseek.com/v1 |
| `EMBEDDING_MODEL` | Embedding 模型 | BAAI/bge-large-zh-v1.5 |
| `EMBEDDING_API_KEY` | Embedding API Key | - |
| `EMBEDDING_API_BASE_URL` | Embedding API Base URL | https://api.siliconflow.cn/v1 |
| `EMBEDDING_PROVIDER` | Embedding 提供方式 (llama_index/siliconflow) | siliconflow |
| `SQLITE_DB_PATH` | SQLite 数据库路径 | ./data/sqlite/chatrag.db |
| `FAISS_DB_PATH` | FAISS 向量数据库路径 | ./data/faiss/ |
| `ENABLE_QUERY_REWRITING` | 启用 Query 改写 | true |
| `ENABLE_HYBRID_SEARCH` | 启用混合检索 | false |
| `ENABLE_RERANKING` | 启用重排序 | false |
| `RAG_TOP_K` | 检索候选数 | 10 |
| `RAG_TOP_N` | 最终保留数 | 5 |
| `RAG_CHUNK_SIZE` | 分块大小 | 512 |
| `RAG_CHUNK_OVERLAP` | 分块重叠 | 50 |

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/models` | 获取 LLM 模型列表 |
| GET | `/api/embedding-models` | 获取 Embedding 模型列表 |
| GET/POST/DELETE | `/api/chat/conversations` | 普通对话会话管理 |
| POST | `/api/chat/conversations/{id}/messages` | 发送消息 (SSE 流式) |
| POST | `/api/chat/conversations/{id}/messages/{mid}/stop` | 停止生成 |
| POST | `/api/chat/conversations/{id}/messages/{mid}/regenerate` | 重新生成 |
| DELETE | `/api/chat/conversations/{id}/messages/{mid}` | 删除消息 (含对应提问) |
| GET/POST/DELETE | `/api/rag/conversations` | RAG 对话会话管理 |
| PUT | `/api/rag/conversations/{id}` | 重命名 RAG 会话 |
| POST | `/api/rag/conversations/{id}/messages` | RAG 消息 (SSE 流式) |
| POST | `/api/rag/conversations/{id}/messages/{mid}/stop` | 停止生成 |
| POST | `/api/rag/conversations/{id}/messages/{mid}/regenerate` | 重新生成 |
| DELETE | `/api/rag/conversations/{id}/messages/{mid}` | 删除消息 (含对应提问) |
| POST | `/api/rag/conversations/{id}/messages/{mid}/feedback` | 标记答案正确/错误 |
| POST | `/api/documents/upload` | 上传文档 (重复检测) |
| GET | `/api/documents` | 文档列表 |
| DELETE | `/api/documents/{id}` | 删除文档 (向量+文件+数据库) |
| GET/PUT/DELETE | `/api/bad-cases` | 错题集管理 |

## 参考文档

- [DeepAgents 框架](https://docs.langchain.com/oss/python/deepagents/overview)
- [LangChain MCP Adapters](https://docs.langchain.com/oss/python/langchain/mcp)
- [bing-cn-mcp](https://www.modelscope.cn/mcp/servers/@tavily-ai/tavily-mcp)
- [硅基流动 Embedding API](https://api-docs.siliconflow.cn/docs/api/embeddings-post)
- [LangChain init_chat_model](https://python.langchain.com/docs/how_to/chat_models_universal_init/)
- [LlamaIndex](https://docs.llamaindex.ai/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Element Plus](https://element-plus.org/)
