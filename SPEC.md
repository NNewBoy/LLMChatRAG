# LLMChatRAG 软件规格说明书 (SPEC)

> 版本: v2.0 | 日期: 2026-06-28

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术栈](#2-技术栈)
3. [系统架构](#3-系统架构)
4. [项目目录结构](#4-项目目录结构)
5. [数据库设计](#5-数据库设计)
6. [后端 API 设计](#6-后端-api-设计)
7. [SSE 流式协议规范](#7-sse-流式协议规范)
8. [Agent 模块设计](#8-agent-模块设计)
9. [RAG 模块设计](#9-rag-模块设计)
10. [前端设计](#10-前端设计)
    - 10.5 [响应式设计](#105-响应式设计)
11. [环境变量配置](#11-环境变量配置)
12. [开发与部署](#12-开发与部署)

---

## 1. 项目概述

### 1.1 软件功能

实现一个同时支持**普通聊天 Agent** 和 **RAG（检索增强生成）** 的在线网站。用户可在两种模式间切换：

- **普通对话模式**：Agent 自动识别意图，普通问题直接回答，涉及知识库的问题自动调用 RAG 工具；用户可手动关闭意图识别，此时 Agent 仅进行普通对话
- **RAG 对话模式**：直接进入 RAG 流程，基于上传文档进行问答；用户可实时调整检索策略参数

### 1.2 核心特性

| 特性 | 描述 |
|------|------|
| 多技能 Agent | 通过 SKILL.md 扩展 Agent 能力，DeepAgents 自主决策调用 |
| 长期记忆 | SQLite 持久化对话历史，跨会话上下文关联 |
| 流式对话 | SSE 推送，前端实时展示思考过程与工具调用 |
| 图片理解 | 支持上传图片，多模态模型理解 |
| 联网搜索 | Agent 可调用搜索引擎获取实时信息 |
| 意图识别 | 自动判断用户问题是否需要 RAG 检索，支持开关控制 |
| 混合检索 | 向量检索 + BM25 关键词检索，加权融合 |
| 重排序 | LLM 对检索结果精排，提升答案质量 |
| Bad Case 管理 | 前端标记错误答案，构建错题集，支持范例回传 |
| 文档管理 | 上传/删除文档，自动解析入库，状态追踪 |
| 响应式设计 | 兼容 PC 端与移动端，自适应布局 |
| 运行时配置 | RAG 模式下前端可实时切换 Embedding 模型、检索策略等参数 |

---

## 2. 技术栈

### 2.1 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | ^3.4 | 前端框架 |
| Vite | ^5 | 构建工具 |
| Element Plus | ^2.5 | UI 组件库 |
| Pinia | ^2 | 状态管理 |
| Vue Router | ^4 | 路由管理 |
| Axios | ^1 | HTTP 请求 |
| marked / highlight.js | - | Markdown 渲染与代码高亮 |

### 2.2 后端

| 技术 | 用途 |
|------|------|
| Python 3.11+ | 运行环境 |
| FastAPI | Web 框架 |
| SQLite (aiosqlite) | 关系型数据库 |
| FAISS | 向量数据库 |
| DeepAgents | Agent 框架 |
| LlamaIndex | RAG 框架 |
| LangChain | LLM 连接层 (init_chat_model) |
| Pydantic | 数据校验 |
| uvicorn | ASGI 服务器 |
| python-multipart | 文件上传 |

---

## 3. 系统架构

### 3.1 架构分层

```
┌─────────────────────────────────────────────────────────┐
│                      前端 (Vue3)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ 普通对话  │  │ RAG对话  │  │ 文档管理  │              │
│  │   页面    │  │   页面   │  │  页面    │              │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘              │
│       │             │             │                     │
│       └─────────────┼─────────────┘                     │
│                     │ HTTP/SSE                          │
└─────────────────────┼───────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────┐
│                  后端 (FastAPI)                          │
│  ┌──────────────────┴──────────────────┐                │
│  │           API 路由层                 │                │
│  │  /chat  /rag  /documents  /models   │                │
│  └──────────┬──────────────┬───────────┘                │
│             │              │                            │
│  ┌──────────┴──┐  ┌───────┴────────┐                   │
│  │ Agent 模块  │  │   RAG 模块     │                   │
│  │ (DeepAgents)│  │ (LlamaIndex)   │                   │
│  │             │  │                │                   │
│  │ ┌─────────┐ │  │ ┌────────────┐ │                   │
│  │ │意图识别  │ │  │ │ 文档解析    │ │                   │
│  │ │技能管理  │ │  │ │ 文档分块    │ │                   │
│  │ │长期记忆  │ │  │ │ 向量化      │ │                   │
│  │ │工具调用  │ │  │ │ FAISS存储   │ │                   │
│  │ │联网搜索  │ │  │ │ Query改写   │ │                   │
│  │ │图片理解  │ │  │ │ 混合检索    │ │                   │
│  │ └─────────┘ │  │ │ 重排序      │ │                   │
│  └──────┬──────┘  │ │ 答案生成    │ │                   │
│         │         │ └────────────┘ │                   │
│         │         └───────┬────────┘                   │
│         │                 │                            │
│  ┌──────┴─────────────────┴────────┐                   │
│  │          数据层                   │                   │
│  │  SQLite (会话/消息/错题/记忆)     │                   │
│  │  FAISS (向量索引)                │                   │
│  └──────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

### 3.2 请求处理流程

```
用户输入
  │
  ├─ 普通对话模式 ─→ Agent 意图识别 (可关闭)
  │                    │
  │                    ├─ 普通问题 ─→ LLM 直接回答 (SSE)
  │                    │
  │                    └─ RAG 问题 ─→ 调用 RAG 工具 ─→ 检索 ─→ LLM 生成回答 (SSE)
  │
  └─ RAG 对话模式 ─→ 直接 RAG 流程
                       │
                       ├─ Query 改写 (前端可控开关)
                       ├─ 向量检索 / 混合检索 (前端可控开关)
                       ├─ 重排序 (前端可控开关)
                       ├─ Prompt 构建
                       └─ LLM 生成回答 (SSE)
```

---

## 4. 项目目录结构

```
LLMChatRAG/
├── backend/
│   ├── main.py                    # FastAPI 入口，启动服务
│   ├── config.py                  # 环境变量配置加载
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py            # SQLite 连接管理
│   │   ├── conversation.py        # 会话表模型
│   │   ├── message.py             # 消息表模型
│   │   ├── bad_case.py            # 错题表模型
│   │   └── document.py            # 文档表模型
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py                # /api/chat/* 普通对话接口
│   │   ├── rag.py                 # /api/rag/* RAG 对话接口
│   │   ├── document.py            # /api/documents/* 文档管理接口
│   │   └── model.py               # /api/models/* 模型列表接口
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── agent_factory.py       # Agent 工厂，创建 DeepAgents 实例
│   │   ├── intent_router.py       # 意图识别：普通聊天 vs RAG
│   │   ├── skills_loader.py       # 加载 SKILL.md 文件
│   │   ├── tools.py               # Agent 工具定义 (RAG工具、联网搜索等)
│   │   ├── memory.py              # 长期记忆管理 (SQLite)
│   │   └── skills/                # SKILL.md 存放目录
│   │       ├── web_search.md      # 联网搜索技能
│   │       ├── rag_query.md       # RAG 查询技能
│   │       └── image_analysis.md  # 图片分析技能
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── parser.py              # 文档解析 (PDF/Word/HTML/TXT)
│   │   ├── chunker.py             # 文档分块
│   │   ├── embedder.py            # 向量化 (Embedding)
│   │   ├── vector_store.py        # FAISS 向量存储管理
│   │   ├── query_rewriter.py      # Query 改写
│   │   ├── retriever.py           # 检索 (向量检索 + BM25 混合)
│   │   ├── reranker.py            # 重排序
│   │   ├── generator.py           # Prompt 构建 + 答案生成
│   │   └── pipeline.py            # RAG 完整流水线编排
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chat_service.py        # 普通对话业务逻辑
│   │   ├── rag_service.py         # RAG 对话业务逻辑
│   │   └── document_service.py    # 文档管理业务逻辑
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── chat.py                # 对话请求/响应模型
│   │   ├── rag.py                 # RAG 请求/响应模型
│   │   └── document.py            # 文档请求/响应模型
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── sse.py                 # SSE 事件构建工具
│   │   └── logger.py              # Logging 配置
│   ├── data/
│   │   ├── faiss/                 # FAISS 索引文件存储
│   │   ├── sqlite/                # SQLite 数据库文件
│   │   └── uploads/               # 上传文档临时存储
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/
│   │   │   └── index.js
│   │   ├── stores/
│   │   │   ├── chat.js            # 对话状态 (Pinia)
│   │   │   ├── rag.js             # RAG 状态 (Pinia)
│   │   │   └── document.js        # 文档状态 (Pinia)
│   │   ├── api/
│   │   │   ├── client.js          # Axios 实例 + SSE 封装
│   │   │   ├── chat.js            # 聊天 API
│   │   │   ├── rag.js             # RAG API
│   │   │   └── document.js        # 文档 API
│   │   ├── views/
│   │   │   ├── ChatView.vue       # 普通对话页面
│   │   │   ├── RAGView.vue        # RAG 对话页面
│   │   │   └── DocumentView.vue   # 文档管理页面
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── ChatInput.vue          # 输入框组件
│   │   │   │   ├── ChatMessage.vue        # 单条消息展示
│   │   │   │   ├── ChatMessageList.vue    # 消息列表
│   │   │   │   ├── ChatThinking.vue       # 思考过程展示
│   │   │   │   ├── ChatToolCall.vue       # 工具调用展示
│   │   │   │   ├── ChatSidebar.vue        # 历史会话侧边栏
│   │   │   │   ├── ImageUpload.vue        # 图片上传
│   │   │   │   ├── ModelSelector.vue      # 模型选择器
│   │   │   │   └── IntentToggle.vue       # 意图识别开关
│   │   │   ├── rag/
│   │   │   │   ├── RAGChatInput.vue       # RAG 输入框
│   │   │   │   ├── RAGChatMessage.vue     # RAG 消息展示
│   │   │   │   ├── RAGChatSidebar.vue     # RAG 历史会话侧边栏
│   │   │   │   ├── FeedbackBadge.vue      # 答案正确/错误标记
│   │   │   │   ├── BadCaseEditor.vue      # 错题编辑器
│   │   │   │   └── RAGConfigPanel.vue     # RAG 运行时配置面板
│   │   │   └── document/
│   │   │       ├── DocumentUpload.vue     # 文档上传
│   │   │       ├── DocumentList.vue       # 文档列表
│   │   │       └── DocumentStatus.vue     # 文档状态标签
│   │   └── assets/
│   │       └── styles/
│   │           └── main.css
│   └── public/
└── README.md
```

---

## 5. 数据库设计

### 5.1 表结构总览

#### conversations（会话表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | UUID 主键 |
| title | TEXT | 会话标题 (自动截取首条消息) |
| mode | TEXT | 模式: "chat" / "rag" |
| created_at | TEXT | 创建时间 ISO 格式 |
| updated_at | TEXT | 最后更新时间 |

#### messages（消息表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | UUID 主键 |
| conversation_id | TEXT FK | 关联会话 |
| role | TEXT | "user" / "assistant" / "system" |
| content | TEXT | 消息内容 |
| thinking | TEXT | 思考过程 (JSON, 可空) |
| tool_calls | TEXT | 工具调用记录 (JSON, 可空) |
| is_correct | INTEGER | 是否正确 (NULL=未评价, 0=错误, 1=正确) |
| parent_message_id | TEXT | 追问来源消息 ID (可空) |
| created_at | TEXT | 创建时间 |

#### documents（文档表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | UUID 主键 |
| filename | TEXT | 原始文件名 |
| file_type | TEXT | 文件类型: pdf/word/html/txt |
| file_size | INTEGER | 文件大小 (bytes) |
| status | TEXT | 状态: "uploading" / "parsing" / "chunking" / "embedding" / "completed" / "failed" |
| chunk_count | INTEGER | 分块数量 |
| error_message | TEXT | 错误信息 (可空) |
| created_at | TEXT | 创建时间 |

#### bad_cases（错题表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | UUID 主键 |
| message_id | TEXT FK | 关联错误消息 |
| question | TEXT | 用户问题 |
| wrong_answer | TEXT | 错误答案 |
| correct_answer | TEXT | 用户编写的正确答案 |
| use_as_example | INTEGER | 是否作为范例传给 LLM (0/1) |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

#### long_term_memory（长期记忆表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | TEXT PK | UUID 主键 |
| key | TEXT | 记忆键 |
| value | TEXT | 记忆内容 |
| importance | REAL | 重要性权重 (0-1) |
| created_at | TEXT | 创建时间 |
| last_accessed_at | TEXT | 最后访问时间 |

### 5.2 建表 SQL

```sql
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '',
    mode TEXT NOT NULL CHECK(mode IN ('chat', 'rag')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL DEFAULT '',
    thinking TEXT,
    tool_calls TEXT,
    is_correct INTEGER,
    parent_message_id TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_message_id) REFERENCES messages(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'uploading',
    chunk_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS bad_cases (
    id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL,
    question TEXT NOT NULL,
    wrong_answer TEXT NOT NULL,
    correct_answer TEXT NOT NULL DEFAULT '',
    use_as_example INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS long_term_memory (
    id TEXT PRIMARY KEY,
    key TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL,
    importance REAL NOT NULL DEFAULT 0.5,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_accessed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_parent ON messages(parent_message_id);
CREATE INDEX idx_bad_cases_message ON bad_cases(message_id);
CREATE INDEX idx_documents_status ON documents(status);
```

---

## 6. 后端 API 设计

### 6.1 通用说明

- Base URL: `http://{HOST}:{PORT}/api`
- 响应格式: JSON
- 流式端点: SSE (text/event-stream)
- 所有时间字段使用 ISO 8601 格式

### 6.2 模型列表接口

#### GET /api/models

获取可用 LLM 模型列表，包含是否支持多模态的信息。

**响应:**
```json
{
  "models": [
    {
      "id": "deepseek-chat",
      "name": "DeepSeek Chat",
      "provider": "deepseek",
      "multimodal": false
    },
    {
      "id": "gpt-4o",
      "name": "GPT-4o",
      "provider": "openai",
      "multimodal": true
    }
  ]
}
```

#### GET /api/embedding-models

获取可用 Embedding 模型列表（供 RAG 模式前端选择）。

**响应:**
```json
{
  "models": [
    {
      "id": "BAAI/bge-large-zh-v1.5",
      "name": "BGE Large Chinese v1.5",
      "provider": "siliconflow",
      "dimension": 1024
    },
    {
      "id": "BAAI/bge-m3",
      "name": "BGE M3",
      "provider": "siliconflow",
      "dimension": 1024
    }
  ]
}
```

### 6.3 普通对话接口

#### GET /api/chat/conversations

获取历史会话列表。

**参数:** `?mode=chat`

**响应:**
```json
{
  "conversations": [
    {
      "id": "uuid",
      "title": "关于机器学习的讨论",
      "mode": "chat",
      "created_at": "2026-06-28T10:00:00",
      "updated_at": "2026-06-28T12:00:00"
    }
  ]
}
```

#### POST /api/chat/conversations

创建新会话。

**请求:**
```json
{
  "mode": "chat",
  "title": "新对话"
}
```

**响应:**
```json
{
  "conversation": {
    "id": "uuid",
    "title": "新对话",
    "mode": "chat",
    "created_at": "2026-06-28T10:00:00",
    "updated_at": "2026-06-28T10:00:00"
  }
}
```

#### DELETE /api/chat/conversations/{conversation_id}

删除会话及其所有消息。

**响应:** `204 No Content`

#### GET /api/chat/conversations/{conversation_id}/messages

获取会话消息历史。

**响应:**
```json
{
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "什么是机器学习？",
      "thinking": null,
      "tool_calls": null,
      "is_correct": null,
      "parent_message_id": null,
      "created_at": "2026-06-28T10:00:00"
    }
  ]
}
```

#### POST /api/chat/conversations/{conversation_id}/messages (SSE 流式)

发送消息，流式返回 Agent 回复。

**请求:**
```json
{
  "content": "什么是机器学习？",
  "model": "deepseek-chat",
  "image": null,
  "parent_message_id": null,
  "enable_intent_recognition": true
}
```

**请求 (带图片，需模型支持多模态):**
```json
{
  "content": "这张图片里有什么？",
  "model": "gpt-4o",
  "image": "base64_encoded_image_data",
  "parent_message_id": null,
  "enable_intent_recognition": true
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | 是 | 用户消息内容 |
| model | string | 是 | LLM 模型 ID |
| image | string | 否 | 图片 base64 编码数据 (仅多模态模型) |
| parent_message_id | string | 否 | 追问来源消息 ID |
| enable_intent_recognition | boolean | 是 | 是否启用意图识别。true 时加载 RAG 工具供 Agent 调用；false 时不进行意图识别且不加载 RAG 工具 |

**SSE 响应:** 参见 [第7节 SSE 流式协议规范](#7-sse-流式协议规范)

#### POST /api/chat/conversations/{conversation_id}/messages/{message_id}/stop

停止生成。

**响应:**
```json
{
  "status": "stopped",
  "message_id": "uuid"
}
```

#### POST /api/chat/conversations/{conversation_id}/messages/{message_id}/regenerate (SSE 流式)

重新生成回答。**后端会删除该消息及其之后的所有消息**，然后以该消息的父消息为上下文重新生成。

**请求:**
```json
{
  "model": "deepseek-chat"
}
```

#### DELETE /api/chat/conversations/{conversation_id}/messages/{message_id}

删除指定消息，从对话历史中移除该条消息。

**响应:** `204 No Content`

### 6.4 RAG 对话接口

#### GET /api/rag/conversations

获取 RAG 历史会话列表。

**参数:** `?mode=rag`

**响应:** 同 `/api/chat/conversations`

#### POST /api/rag/conversations

创建 RAG 新会话。

**请求:**
```json
{
  "mode": "rag",
  "title": "RAG 新对话"
}
```

**响应:** 同 `/api/chat/conversations`

#### DELETE /api/rag/conversations/{conversation_id}

删除 RAG 会话。

**响应:** `204 No Content`

#### GET /api/rag/conversations/{conversation_id}/messages

获取 RAG 会话消息历史。

**响应:** 同 `/api/chat/conversations/{id}/messages`

#### POST /api/rag/conversations/{conversation_id}/messages (SSE 流式)

发送 RAG 消息，流式返回基于检索的回复。**无需意图识别，直接进入 RAG 流程。**

**请求:**
```json
{
  "content": "文档中提到了哪些关键技术？",
  "model": "deepseek-chat",
  "parent_message_id": null,
  "embedding_model": "BAAI/bge-large-zh-v1.5",
  "enable_query_rewriting": true,
  "enable_hybrid_search": false,
  "enable_reranking": false
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | string | 是 | 用户消息内容 |
| model | string | 是 | LLM 模型 ID |
| parent_message_id | string | 否 | 追问来源消息 ID |
| embedding_model | string | 是 | Embedding 模型 ID |
| enable_query_rewriting | boolean | 是 | 是否启用 Query 改写 |
| enable_hybrid_search | boolean | 是 | 是否启用混合检索 (默认仅向量检索) |
| enable_reranking | boolean | 是 | 是否启用重排序 |

**SSE 响应:** 参见 [第7节 SSE 流式协议规范](#7-sse-流式协议规范)

#### POST /api/rag/conversations/{conversation_id}/messages/{message_id}/stop

停止生成。

#### POST /api/rag/conversations/{conversation_id}/messages/{message_id}/regenerate (SSE 流式)

重新生成 RAG 回答。**后端会删除该消息及其之后的所有消息**，然后以该消息的父消息为上下文重新生成。

#### DELETE /api/rag/conversations/{conversation_id}/messages/{message_id}

删除指定消息，从 RAG 对话历史中移除该条消息。

**响应:** `204 No Content`

#### POST /api/rag/conversations/{conversation_id}/messages/{message_id}/feedback

标记答案正确/错误。

**请求:**
```json
{
  "is_correct": false
}
```

**响应:**
```json
{
  "status": "ok",
  "message_id": "uuid",
  "is_correct": false
}
```

### 6.5 文档管理接口

#### POST /api/documents/upload

上传文档。

**请求:** `multipart/form-data`
- `file`: 文件 (PDF/Word/HTML/TXT)

**响应:**
```json
{
  "document": {
    "id": "uuid",
    "filename": "技术文档.pdf",
    "file_type": "pdf",
    "file_size": 1024000,
    "status": "uploading",
    "chunk_count": 0,
    "error_message": null,
    "created_at": "2026-06-28T10:00:00"
  }
}
```

#### GET /api/documents

获取所有文档列表。

**响应:**
```json
{
  "documents": [
    {
      "id": "uuid",
      "filename": "技术文档.pdf",
      "file_type": "pdf",
      "file_size": 1024000,
      "status": "completed",
      "chunk_count": 150,
      "error_message": null,
      "created_at": "2026-06-28T10:00:00"
    }
  ]
}
```

#### GET /api/documents/{document_id}/status

获取文档处理状态（供前端轮询）。

**响应:**
```json
{
  "document": {
    "id": "uuid",
    "status": "chunking",
    "progress": "正在分块处理..."
  }
}
```

#### DELETE /api/documents/{document_id}

删除文档及其向量数据。

**响应:** `204 No Content`

### 6.6 错题集接口

#### GET /api/bad-cases

获取错题集列表。

**参数:**
- `use_as_example` (可选): 0/1 筛选是否作为范例

**响应:**
```json
{
  "bad_cases": [
    {
      "id": "uuid",
      "message_id": "uuid",
      "question": "什么是机器学习？",
      "wrong_answer": "机器学习是...",
      "correct_answer": "机器学习是人工智能的一个分支...",
      "use_as_example": true,
      "created_at": "2026-06-28T10:00:00"
    }
  ]
}
```

#### PUT /api/bad-cases/{bad_case_id}

更新错题答案和范例标记。

**请求:**
```json
{
  "correct_answer": "正确的答案内容...",
  "use_as_example": true
}
```

**响应:**
```json
{
  "bad_case": {
    "id": "uuid",
    "correct_answer": "正确的答案内容...",
    "use_as_example": true,
    "updated_at": "2026-06-28T12:00:00"
  }
}
```

#### DELETE /api/bad-cases/{bad_case_id}

删除错题。

**响应:** `204 No Content`

---

## 7. SSE 流式协议规范

### 7.1 事件类型

| 事件类型 | 说明 | 触发时机 |
|----------|------|----------|
| `thinking` | Agent 思考过程 | 推理阶段 |
| `tool_call` | 工具调用开始 | 开始调用工具时 |
| `tool_result` | 工具调用结果 | 工具执行完毕 |
| `intent` | 意图识别结果 | 识别完成时 |
| `token` | 文本增量 Token | 逐字生成 |
| `done` | 生成完成 | 全部完成 |
| `error` | 错误信息 | 发生异常 |

### 7.2 事件格式

```
event: thinking
data: {"content": "用户问的是关于机器学习的基础概念，我需要从定义出发来解释...", "timestamp": "2026-06-28T10:00:00"}

event: intent
data: {"intent": "rag", "confidence": 0.95, "reason": "用户问题涉及知识库中的文档内容"}

event: tool_call
data: {"tool_name": "rag_search", "tool_input": {"query": "什么是机器学习"}, "timestamp": "2026-06-28T10:00:01"}

event: tool_result
data: {"tool_name": "rag_search", "tool_output": "找到 3 条相关文档...", "timestamp": "2026-06-28T10:00:02"}

event: token
data: {"content": "机器", "message_id": "uuid", "timestamp": "2026-06-28T10:00:03"}

event: token
data: {"content": "学习", "message_id": "uuid", "timestamp": "2026-06-28T10:00:03"}

event: done
data: {"message_id": "uuid", "full_content": "机器学习是...", "conversation_id": "uuid"}

event: error
data: {"code": "GENERATION_ERROR", "message": "生成失败：API 调用超时", "message_id": "uuid"}
```

### 7.3 前端 SSE 消费示例

```javascript
// api/client.js
async function streamChat(url, body, callbacks) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop();

    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEvent = line.slice(7);
      } else if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (callbacks[currentEvent]) {
          callbacks[currentEvent](data);
        }
      }
    }
  }
}
```

---

## 8. Agent 模块设计

### 8.1 Agent 创建流程

```
┌──────────────────────────────────────────────────────────┐
│                    AgentFactory                          │
│                                                          │
│  1. 加载环境变量配置 (LLM Model, API Key, Base URL)      │
│  2. 通过 LangChain init_chat_model 创建 LLM 实例         │
│  3. 加载 SKILL.md 技能文件                               │
│  4. 注册工具 (rag_search, web_search, image_analysis)    │
│  5. 加载长期记忆 (SQLite)                                │
│  6. 创建 DeepAgents Agent 实例                           │
│  7. 注入意图识别中间件 (根据 enable_intent_recognition)   │
│                                                          │
│  输出: DeepAgents Agent 实例                             │
└──────────────────────────────────────────────────────────┘
```

### 8.2 意图识别 (IntentRouter)

```python
# 伪代码
class IntentRouter:
    """
    判断用户输入意图：
    - "chat": 普通聊天，直接由 LLM 回答
    - "rag": 需要检索知识库，调用 RAG 工具

    注意：当 enable_intent_recognition=false 时，跳过意图识别，
    所有问题直接按普通聊天处理，不加载 RAG 工具。
    """

    def classify(self, query: str, conversation_history: list) -> dict:
        """
        通过 LLM 判断意图，返回:
        {
            "intent": "chat" | "rag",
            "confidence": 0.0 ~ 1.0,
            "reason": "分类理由"
        }
        """
        prompt = f"""
        判断用户问题的意图类型：
        - chat: 普通闲聊、编程问题、常识问答等
        - rag: 需要查询特定文档/知识库才能回答的问题

        对话历史: {conversation_history}
        用户问题: {query}

        返回 JSON: {{"intent": "...", "confidence": 0.0, "reason": "..."}}
        """
        # 调用 LLM 判断
```

### 8.3 技能系统 (SKILL.md)

每个 SKILL.md 文件定义一种技能，DeepAgents 框架自动读取并决定何时使用。

**SKILL.md 文件格式示例 (rag_query.md):**

```markdown
# RAG 查询技能

## 描述
当用户问题需要查询知识库文档时使用此技能。

## 触发条件
- 用户明确询问文档相关内容
- 意图识别为 "rag"
- 用户提及特定文档名称

## 工具
- rag_search: 在知识库中检索相关文档

## 使用方式
调用 rag_search 工具，传入改写后的查询语句。
```

**SKILL.md 文件格式示例 (web_search.md):**

```markdown
# 联网搜索技能

## 描述
当用户问题需要实时信息、最新新闻、或 LLM 训练数据中不包含的内容时使用。

## 触发条件
- 用户询问实时信息
- 用户要求搜索最新资料
- LLM 无法确定答案且需要外部信息

## 工具
- web_search: 使用搜索引擎查询

## 使用方式
调用 web_search 工具，传入搜索关键词。
```

### 8.4 工具定义

```python
# 伪代码 - tools.py

# 1. RAG 检索工具
def rag_search(query: str, top_k: int = 5) -> str:
    """在知识库中检索相关文档"""
    # 调用 RAG pipeline 的检索部分
    return formatted_results

# 2. 联网搜索工具
def web_search(query: str, num_results: int = 5) -> str:
    """搜索互联网获取实时信息"""
    # 调用搜索引擎 API
    return formatted_results

# 3. 图片分析工具 (多模态模型内置支持)
# 无需额外定义，DeepAgents 通过多模态 LLM 直接处理图片输入
```

### 8.5 长期记忆 (LongTermMemory)

```python
# 伪代码 - memory.py
class LongTermMemory:
    """
    管理跨会话的长期记忆。
    使用 SQLite 存储键值对，带重要性权重。
    """

    def store(self, key: str, value: str, importance: float = 0.5):
        """存储记忆，如果 key 已存在则更新 importance"""

    def retrieve(self, query: str, top_k: int = 5) -> list:
        """基于查询检索相关记忆，按重要性排序"""

    def forget(self, key: str):
        """删除指定记忆"""

    def consolidate(self):
        """记忆整理：合并相似记忆，删除低重要性记忆"""
```

---

## 9. RAG 模块设计

### 9.1 RAG 流水线 (Pipeline)

```
┌─────────────────────────────────────────────────────────────────┐
│                      RAG Pipeline                               │
│                                                                 │
│  输入: 用户查询 (query) + 运行时配置参数                          │
│                                                                 │
│  ┌─────────────┐                                                │
│  │ 1. Query改写 │ (可选，由前端参数 enable_query_rewriting 控制)  │
│  │   使用 LLM   │ 将模糊问题改写为精确查询                          │
│  └──────┬──────┘                                                │
│         │ rewritten_query                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────┐                    │
│  │ 2. 检索 (Retrieval)                      │                    │
│  │                                          │                    │
│  │  ┌──────────────┐  ┌──────────────┐      │                    │
│  │  │ 向量检索      │  │ BM25 关键词   │      │                    │
│  │  │ (Embedding)  │  │ 检索          │      │                    │
│  │  └──────┬───────┘  └──────┬───────┘      │                    │
│  │         │                 │               │                    │
│  │         └────────┬────────┘               │                    │
│  │                  │                        │                    │
│  │                  ▼                        │                    │
│  │  ┌──────────────────────────┐             │                    │
│  │  │ 混合加权 (α * 向量 +       │             │                    │
│  │  │         β * BM25)         │             │                    │
│  │  │ 默认: α=1.0, β=0.0       │             │                    │
│  │  │ (仅向量检索)              │             │                    │
│  │  └──────────┬───────────────┘             │                    │
│  └─────────────┼─────────────────────────────┘                    │
│                │ Top-K 结果                                      │
│                ▼                                                 │
│  ┌─────────────┐                                                │
│  │ 3. 重排序    │ (可选，由前端参数 enable_reranking 控制)        │
│  │   使用 LLM   │ 对 Top-K 精排，选 Top-N                        │
│  └──────┬──────┘                                                │
│         │ Top-N 结果                                             │
│         ▼                                                       │
│  ┌─────────────┐                                                │
│  │ 4. Prompt构建│ 拼接文档块 + 错题范例 + 用户问题                 │
│  └──────┬──────┘                                                │
│         │ 完整 Prompt                                            │
│         ▼                                                       │
│  ┌─────────────┐                                                │
│  │ 5. 答案生成  │ LLM 基于 Prompt 生成最终答案 (SSE 流式)         │
│  └─────────────┘                                                │
│                                                                 │
│  输出: 流式答案 + 引用来源                                        │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 文档解析 (Parser)

```python
# 伪代码 - parser.py
class DocumentParser:
    """
    支持格式:
    - PDF: 使用 PyMuPDF / pdfplumber
    - Word: 使用 python-docx
    - HTML: 使用 BeautifulSoup4
    - TXT: 直接读取
    """

    def parse(self, file_path: str, file_type: str) -> str:
        """解析文档为纯文本字符串"""
        if file_type == "pdf":
            return self._parse_pdf(file_path)
        elif file_type == "word":
            return self._parse_docx(file_path)
        elif file_type == "html":
            return self._parse_html(file_path)
        elif file_type == "txt":
            return self._parse_txt(file_path)
```

### 9.3 文档分块 (Chunker)

```python
# 伪代码 - chunker.py
class DocumentChunker:
    """
    分块策略:
    - chunk_size: 512 tokens (默认，可配置)
    - chunk_overlap: 50 tokens (默认，可配置)
    - 分隔符: 优先按段落(\n\n)，其次按句子(。！？)，最后按字符
    """

    def chunk(self, text: str) -> list[dict]:
        """
        返回: [{"text": "块内容", "index": 0, "metadata": {...}}, ...]
        """
```

### 9.4 向量化 (Embedder)

```python
# 伪代码 - embedder.py
class Embedder:
    """
    使用硅基流动 (SiliconFlow) Embedding API 进行向量化
    参考文档: https://api-docs.siliconflow.cn/docs/api/embeddings-post

    支持通过前端参数动态切换 Embedding 模型。
    """

    def __init__(self):
        self.model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")
        self.api_key = os.getenv("EMBEDDING_API_KEY")
        self.base_url = os.getenv("EMBEDDING_API_BASE_URL",
                                   "https://api.siliconflow.cn/v1")

    def embed(self, texts: list[str], model: str = None) -> list[list[float]]:
        """将文本列表转换为向量列表，model 参数可覆盖默认模型"""
        # POST {base_url}/embeddings
        # 返回 embedding 向量列表

    def embed_query(self, query: str, model: str = None) -> list[float]:
        """将查询文本转换为向量"""
```

### 9.5 向量存储 (VectorStore)

```python
# 伪代码 - vector_store.py
class FAISSVectorStore:
    """
    FAISS 向量存储管理
    """

    def __init__(self):
        self.index_path = os.getenv("FAISS_DB_PATH", "./data/faiss/")
        self.index = None  # FAISS Index
        self.metadata = {}  # 文档元数据映射

    def add(self, vectors: list, chunks: list[dict]):
        """添加向量及对应元数据到索引"""

    def search(self, query_vector: list, top_k: int = 10) -> list[dict]:
        """向量相似度检索，返回 Top-K 结果"""

    def remove(self, document_id: str):
        """删除指定文档的所有向量"""

    def save(self):
        """持久化索引到磁盘"""

    def load(self):
        """从磁盘加载索引"""
```

### 9.6 混合检索 (Retriever)

```python
# 伪代码 - retriever.py
class HybridRetriever:
    """
    混合检索: 向量检索 + BM25 关键词检索

    由前端参数 enable_hybrid_search 控制是否启用混合检索。
    环境变量 HYBRID_ALPHA / HYBRID_BETA 控制权重比。

    混合公式: score = alpha * vector_score + beta * bm25_score
    """

    def __init__(self):
        self.alpha = float(os.getenv("HYBRID_ALPHA", "0.7"))
        self.beta = float(os.getenv("HYBRID_BETA", "0.3"))

    def retrieve(self, query: str, top_k: int = 10,
                 enable_hybrid: bool = False) -> list[dict]:
        if enable_hybrid:
            return self._hybrid_search(query, top_k)
        else:
            return self._vector_search(query, top_k)
```

### 9.7 重排序 (Reranker)

```python
# 伪代码 - reranker.py
class Reranker:
    """
    使用 LLM 对检索结果进行重排序。
    由前端参数 enable_reranking 控制是否启用。
    """

    def rerank(self, query: str, candidates: list[dict], top_n: int = 5,
               enable_reranking: bool = False) -> list[dict]:
        """
        使用 LLM 对候选文档进行相关性评分，返回 Top-N
        """
        if not enable_reranking:
            return candidates[:top_n]
        # 构造 Prompt，让 LLM 对每个候选文档打分
        # 按分数排序返回 Top-N
```

### 9.8 答案生成 (Generator)

```python
# 伪代码 - generator.py
class Generator:
    """
    Prompt 构建 + 答案生成
    """

    def build_prompt(self, query: str, context_chunks: list[dict],
                     bad_case_examples: list[dict]) -> str:
        """
        构建包含以下部分的 Prompt:
        1. 系统指令
        2. 错题范例 (用户标记为 use_as_example 的 bad cases)
        3. 检索到的文档上下文
        4. 用户问题
        """
        prompt = "你是一个专业的问答助手。请基于以下文档内容回答问题。\n\n"

        if bad_case_examples:
            prompt += "## 注意：以下是以往的错误答案范例，请避免类似错误：\n"
            for bc in bad_case_examples:
                prompt += f"问题: {bc['question']}\n"
                prompt += f"错误答案: {bc['wrong_answer']}\n"
                prompt += f"正确答案: {bc['correct_answer']}\n\n"

        prompt += "## 参考文档：\n"
        for i, chunk in enumerate(context_chunks):
            prompt += f"[{i+1}] {chunk['text']}\n\n"

        prompt += f"## 用户问题：{query}\n\n"
        prompt += "请基于以上文档内容回答，如果文档中没有相关信息，请明确说明。"

        return prompt

    async def generate_stream(self, prompt: str, llm) -> AsyncGenerator:
        """流式生成答案"""
        async for token in llm.astream(prompt):
            yield token
```

---

## 10. 前端设计

### 10.1 路由设计

| 路径 | 组件 | 说明 |
|------|------|------|
| `/` | 重定向到 `/chat` | - |
| `/chat` | ChatView | 普通对话模式 |
| `/chat/:conversationId` | ChatView | 指定会话的普通对话 |
| `/rag` | RAGView | RAG 对话模式 |
| `/rag/:conversationId` | RAGView | 指定会话的 RAG 对话 |
| `/documents` | DocumentView | 文档管理页面 |

### 10.2 组件树

```
App.vue
├── AppLayout.vue
│   ├── AppHeader.vue                    # 顶部导航栏
│   │   ├── Logo
│   │   ├── NavigationTabs (普通对话 | RAG对话 | 文档管理)
│   │   └── ModelSelector.vue           # LLM 模型选择器
│   │
│   └── <router-view>
│       │
│       ├── ChatView.vue                # 普通对话页面
│       │   ├── ChatSidebar.vue         # 左侧历史会话列表
│       │   │   ├── NewChatButton
│       │   │   └── ConversationList
│       │   │       └── ConversationItem (可删除)
│       │   └── ChatMain.vue            # 右侧对话区域
│       │       ├── ChatMessageList.vue
│       │       │   └── ChatMessage.vue
│       │       │       ├── MessageBubble (用户/助手)
│       │       │       ├── ChatThinking.vue (思考过程可折叠)
│       │       │       ├── ChatToolCall.vue (工具调用展示)
│       │       │       └── MessageActions (停止/删除/重新生成/追问)
│       │       └── ChatInput.vue
│       │           ├── ImageUpload.vue (多模态模型时可用)
│       │           ├── IntentToggle.vue (意图识别开关)
│       │           ├── TextInput
│       │           └── SendButton
│       │
│       ├── RAGView.vue                 # RAG 对话页面
│       │   ├── RAGChatSidebar.vue      # 左侧历史会话列表
│       │   │   ├── NewChatButton
│       │   │   └── ConversationList
│       │   └── RAGChatMain.vue         # 右侧对话区域
│       │       ├── RAGConfigPanel.vue  # RAG 运行时配置面板
│       │       │   ├── EmbeddingModelSelector  (Embedding 模型选择)
│       │       │   ├── QueryRewritingToggle    (Query 改写开关)
│       │       │   ├── HybridSearchToggle      (混合检索开关)
│       │       │   └── RerankingToggle         (重排序开关)
│       │       ├── RAGChatMessageList.vue
│       │       │   └── RAGChatMessage.vue
│       │       │       ├── MessageBubble
│       │       │       ├── ChatThinking.vue
│       │       │       ├── ChatToolCall.vue
│       │       │       ├── FeedbackBadge.vue (正确/错误标记)
│       │       │       └── MessageActions
│       │       └── RAGChatInput.vue
│       │           ├── TextInput
│       │           └── SendButton
│       │
│       └── DocumentView.vue            # 文档管理页面
│           ├── BadCaseEditor.vue       # 错题编辑器 (可切换显示)
│           │   ├── BadCaseList
│           │   └── BadCaseEditForm
│           └── DocumentPanel.vue
│               ├── DocumentUpload.vue
│               └── DocumentList.vue
│                   └── DocumentItem.vue
│                       ├── DocumentStatus.vue
│                       └── DeleteButton
```

### 10.3 状态管理 (Pinia Stores)

#### chatStore

```javascript
// stores/chat.js
{
  state: {
    conversations: [],          // 历史会话列表
    currentConversationId: null,
    messages: [],               // 当前会话消息
    isStreaming: false,         // 是否正在流式接收
    selectedModel: 'deepseek-chat',
    availableModels: [],        // 可用模型列表 (含 multimodal 字段)
    enableIntentRecognition: true,  // 意图识别开关
  },
  actions: {
    fetchModels(),              // 获取可用 LLM 模型列表
    fetchConversations(),
    createConversation(title),
    deleteConversation(id),
    fetchMessages(conversationId),
    sendMessage(content, image, parentMessageId),
    stopGeneration(),
    deleteMessage(messageId),
    regenerateMessage(messageId),
    setSelectedModel(modelId),
    setEnableIntentRecognition(enabled),
  }
}
```

#### ragStore

```javascript
// stores/rag.js
{
  state: {
    conversations: [],
    currentConversationId: null,
    messages: [],
    isStreaming: false,
    selectedModel: 'deepseek-chat',
    // RAG 运行时配置
    selectedEmbeddingModel: 'BAAI/bge-large-zh-v1.5',
    availableEmbeddingModels: [],       // 可用 Embedding 模型列表
    enableQueryRewriting: true,
    enableHybridSearch: false,          // 默认仅向量检索
    enableReranking: false,
  },
  actions: {
    fetchEmbeddingModels(),             // 获取可用 Embedding 模型列表
    fetchConversations(),
    createConversation(title),
    deleteConversation(id),
    fetchMessages(conversationId),
    sendMessage(content, parentMessageId),
    stopGeneration(),
    deleteMessage(messageId),
    regenerateMessage(messageId),
    submitFeedback(messageId, isCorrect),
    setSelectedModel(modelId),
    setSelectedEmbeddingModel(modelId),
    setEnableQueryRewriting(enabled),
    setEnableHybridSearch(enabled),
    setEnableReranking(enabled),
  }
}
```

#### documentStore

```javascript
// stores/document.js
{
  state: {
    documents: [],              // 文档列表
    badCases: [],               // 错题列表
  },
  actions: {
    uploadDocument(file),
    fetchDocuments(),
    deleteDocument(id),
    fetchBadCases(),
    updateBadCase(id, correctAnswer, useAsExample),
    deleteBadCase(id),
  }
}
```

### 10.4 页面交互流程

#### 普通对话流程

```
1. 用户进入页面 → 加载历史会话列表 + 可用模型列表
2. 选择模型 (ModelSelector)，模型列表显示是否支持多模态
3. 切换意图识别开关 (IntentToggle)：
   - 开启：Agent 加载 RAG 工具，自动识别意图
   - 关闭：Agent 不加载 RAG 工具，全部按普通对话处理
4. 选择或创建会话 → 加载历史消息
5. 用户输入问题 (多模态模型时可选上传图片)
6. 点击发送 → POST /api/chat/.../messages (SSE)
   ├── 前端展示思考过程 (thinking 事件)
   ├── 前端展示意图识别结果 (intent 事件，仅意图识别开启时)
   ├── 前端展示工具调用 (tool_call → tool_result 事件)
   └── 前端逐字展示回复 (token 事件)
7. 对话编辑操作:
   ├── 点击"停止"按钮 → 中断流式生成，保留已生成内容
   ├── 点击"删除"按钮 → 从对话历史中移除该条消息 (DELETE /api/chat/.../messages/{id})
   ├── 点击"重新生成" → 删除该消息及之后所有消息，以该消息之前的内容为上下文重新生成
   └── 点击某条助手消息 → 以该消息为基础追问 (parent_message_id 关联)
```

#### RAG 对话流程

```
1. 用户进入页面 → 加载历史 RAG 会话列表 + 可用 Embedding 模型列表
2. 配置 RAG 参数 (RAGConfigPanel)：
   ├── 选择 Embedding 模型
   ├── 切换 Query 改写开关
   ├── 切换混合检索开关 (默认关闭)
   └── 切换重排序开关 (默认关闭)
3. 选择或创建会话 → 加载历史消息
4. 用户输入问题
5. 点击发送 → POST /api/rag/.../messages (SSE，携带 RAG 运行时参数)
   ├── 前端展示 Query 改写过程 (thinking 事件)
   ├── 前端展示检索结果 (tool_call/tool_result 事件)
   ├── 前端展示重排序过程 (thinking 事件)
   └── 前端逐字展示回复 (token 事件)
6. 用户可标记答案正确/错误 (FeedbackBadge)
7. 错误答案自动进入错题集
```

#### 文档上传流程

```
1. 用户选择文件 → 前端校验格式和大小
2. 点击上传 → POST /api/documents/upload
3. 后端异步处理:
   ├── 解析文档 → 分块 → 向量化 → 存入 FAISS
   └── 状态更新: uploading → parsing → chunking → embedding → completed
4. 前端轮询获取状态更新 (GET /api/documents/{id}/status)
5. 完成后在列表中显示为"已完成"状态
```

### 10.5 响应式设计

UI 需兼容 PC 端与移动端，采用 Element Plus 的响应式栅格系统实现自适应布局。

#### 断点策略

| 断点 | 宽度 | 布局 |
|------|------|------|
| 移动端 | < 768px | 侧边栏隐藏，通过汉堡菜单展开；对话区全宽 |
| 平板端 | 768px ~ 1024px | 侧边栏可折叠，对话区自适应 |
| PC 端 | >= 1024px | 左侧侧边栏 + 右侧对话区，标准双栏布局 |

#### 移动端适配要点

- **侧边栏**：默认隐藏，通过顶部导航栏的汉堡图标（hamburger menu）触发抽屉式（Drawer）展开
- **消息气泡**：最大宽度调整为 90%，确保在小屏幕上可读
- **输入框**：固定在底部，发送按钮和图片上传按钮并排
- **文档管理**：表格改为卡片列表展示，操作按钮收纳进下拉菜单
- **错题编辑器**：使用全屏 Dialog 而非侧边面板
- **导航栏**：Tab 切换使用可横向滚动的标签栏，避免换行
- **RAG 配置面板**：移动端折叠为可展开的配置抽屉，避免占用过多对话区空间
- **意图识别开关**：移动端收纳进输入框上方的工具栏

---

## 11. 环境变量配置

### 11.1 完整环境变量列表

```bash
# ========================================
# 服务器配置
# ========================================
HOST=0.0.0.0                          # 服务器监听地址
PORT=8000                             # 服务器监听端口

# ========================================
# LLM 模型配置 (Agent 和 RAG 共用)
# ========================================
LLM_MODEL=deepseek-chat               # LLM 模型名称 (默认)
LLM_API_KEY=sk-xxxxxxxxxxxxxxxx       # LLM API Key
LLM_API_BASE_URL=https://api.deepseek.com/v1  # LLM API Base URL

# ========================================
# SQLite 数据库路径
# ========================================
SQLITE_DB_PATH=./data/sqlite/chatrag.db  # SQLite 主数据库文件路径
BAD_CASE_DB_PATH=./data/sqlite/bad_cases.db  # 错题集数据库路径 (可选，默认合并到主库 SQLITE_DB_PATH)

# ========================================
# Embedding 模型配置 (RAG 向量化)
# ========================================
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5  # Embedding 模型名称 (默认)
EMBEDDING_API_KEY=sk-xxxxxxxx           # Embedding API Key
EMBEDDING_API_BASE_URL=https://api.siliconflow.cn/v1  # Embedding API Base URL

# ========================================
# RAG 数据库路径
# ========================================
FAISS_DB_PATH=./data/faiss/           # FAISS 向量数据库存储路径

# ========================================
# RAG 功能开关 (默认值，前端可运行时覆盖)
# ========================================
ENABLE_QUERY_REWRITING=true           # 是否启用 Query 改写
ENABLE_HYBRID_SEARCH=false            # 是否启用混合检索 (默认仅向量检索)
ENABLE_RERANKING=false                # 是否启用重排序

# ========================================
# 混合检索参数 (ENABLE_HYBRID_SEARCH=true 时生效)
# ========================================
HYBRID_ALPHA=0.7                      # 向量检索权重 (0-1)
HYBRID_BETA=0.3                       # BM25 关键词检索权重 (0-1)

# ========================================
# RAG 检索参数
# ========================================
RAG_TOP_K=10                          # 检索返回 Top-K 数量
RAG_TOP_N=5                           # 重排序后返回 Top-N 数量
RAG_CHUNK_SIZE=512                    # 文档分块大小 (tokens)
RAG_CHUNK_OVERLAP=50                  # 文档分块重叠大小 (tokens)

# ========================================
# 联网搜索配置
# ========================================
SEARCH_API_KEY=xxxxxxxx               # 搜索引擎 API Key (可选)
SEARCH_API_URL=https://api.example.com/search  # 搜索引擎 API URL (可选)

# ========================================
# 日志配置
# ========================================
LOG_LEVEL=INFO                        # 日志级别: DEBUG/INFO/WARNING/ERROR
LOG_FILE=./logs/app.log               # 日志文件路径
```

### 11.2 配置加载 (config.py)

```python
# config.py - 配置加载模块
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 服务器
    host: str = "0.0.0.0"
    port: int = 8000

    # LLM
    llm_model: str = "deepseek-chat"
    llm_api_key: str = ""
    llm_api_base_url: str = "https://api.deepseek.com/v1"

    # SQLite
    sqlite_db_path: str = "./data/sqlite/chatrag.db"
    bad_case_db_path: str = ""   # 为空则使用 sqlite_db_path

    # Embedding
    embedding_model: str = "BAAI/bge-large-zh-v1.5"
    embedding_api_key: str = ""
    embedding_api_base_url: str = "https://api.siliconflow.cn/v1"

    # FAISS
    faiss_db_path: str = "./data/faiss/"

    # RAG 开关 (默认值，前端可运行时覆盖)
    enable_query_rewriting: bool = True
    enable_hybrid_search: bool = False
    enable_reranking: bool = False

    # 混合检索
    hybrid_alpha: float = 0.7
    hybrid_beta: float = 0.3

    # RAG 参数
    rag_top_k: int = 10
    rag_top_n: int = 5
    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 50

    # 日志
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

---

## 12. 开发与部署

### 12.1 后端启动

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填入 API Key 等配置
python main.py
# 服务启动在 http://localhost:8000
# API 文档: http://localhost:8000/docs
```

### 12.2 前端启动

```bash
cd frontend
npm install
npm run dev
# 开发服务器启动在 http://localhost:5173
# 代理配置将 /api 请求转发至 http://localhost:8000
```

### 12.3 Vite 代理配置

```javascript
// vite.config.js
export default {
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
}
```

### 12.4 后端依赖 (requirements.txt)

```
fastapi==0.111.0
uvicorn[standard]==0.30.0
python-multipart==0.0.9
aiosqlite==0.20.0
pydantic==2.7.0
pydantic-settings==2.3.0
langchain==0.2.0
langchain-core==0.2.0
deepagents==0.1.0
llama-index==0.10.0
llama-index-vector-stores-faiss==0.1.0
faiss-cpu==1.8.0
pymupdf==1.24.0           # PDF 解析
python-docx==1.1.0         # Word 解析
beautifulsoup4==4.12.0     # HTML 解析
lxml==5.2.0
httpx==0.27.0
aiofiles==23.2.0
```

### 12.5 前端依赖 (package.json 核心)

```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.3.0",
    "pinia": "^2.1.0",
    "element-plus": "^2.5.0",
    "axios": "^1.7.0",
    "marked": "^12.0.0",
    "highlight.js": "^11.9.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "vite": "^5.2.0"
  }
}
```

---

## 附录 A: 安全注意事项

1. **API Key 安全**: 所有 API Key 仅通过环境变量注入，不写入代码或前端
2. **文件上传安全**: 校验文件类型白名单、大小限制 (建议 50MB)、病毒扫描
3. **SQL 注入防护**: 使用参数化查询，ORM 框架天然防护
4. **CORS 配置**: 仅允许前端域名跨域访问
5. **输入校验**: 所有 API 输入使用 Pydantic 严格校验
6. **日志脱敏**: 日志中不记录 API Key 等敏感信息
7. **速率限制**: 建议对对话接口添加速率限制 (如 60次/分钟/IP)

## 附录 B: 参考文档

- DeepAgents 框架: https://docs.langchain.com/oss/python/deepagents/overview
- 硅基流动 Embedding API: https://api-docs.siliconflow.cn/docs/api/embeddings-post
- LangChain init_chat_model: https://python.langchain.com/docs/how_to/chat_models_universal_init/
- LlamaIndex: https://docs.llamaindex.ai/
- FAISS: https://github.com/facebookresearch/faiss
- FastAPI: https://fastapi.tiangolo.com/
- Element Plus: https://element-plus.org/