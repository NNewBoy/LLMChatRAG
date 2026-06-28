"""RAG 对话业务逻辑"""

import uuid
import json
from datetime import datetime
from typing import AsyncGenerator
import aiosqlite
from models.database import get_db
from agent.agent_factory import AgentFactory
from rag.pipeline import RAGPipeline
from utils.logger import logger
from utils.sse import sse_event


class RAGService:
    """RAG 对话服务"""

    def __init__(self):
        self.factory = AgentFactory()
        self.pipeline = None  # 延迟初始化
        self._bad_cases_cache = None
        self._active_generations: dict[str, bool] = {}  # 停止标志

    def request_stop(self, message_id: str):
        """请求停止生成"""
        self._active_generations[message_id] = False
        logger.info(f"请求停止 RAG 生成: {message_id}")

    def is_stopped(self, message_id: str) -> bool:
        """检查是否被请求停止"""
        return not self._active_generations.get(message_id, True)

    async def _ensure_pipeline(self, llm):
        """延迟初始化 RAG pipeline"""
        if self.pipeline is None:
            self.pipeline = RAGPipeline(llm=llm)
        return self.pipeline

    async def _load_bad_case_examples(self) -> list[dict]:
        """加载标记为范例的错题"""
        if self._bad_cases_cache is not None:
            return self._bad_cases_cache

        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT question, wrong_answer, correct_answer FROM bad_cases "
                "WHERE use_as_example = 1 ORDER BY created_at DESC LIMIT 10"
            )
            rows = await cursor.fetchall()
            self._bad_cases_cache = [dict(row) for row in rows]
            return self._bad_cases_cache
        finally:
            await db.close()

    async def send_message_stream(
        self,
        conversation_id: str,
        content: str,
        model: str,
        parent_message_id: str = None,
        embedding_model: str = None,
        enable_query_rewriting: bool = True,
        enable_hybrid_search: bool = False,
        enable_reranking: bool = False,
    ) -> AsyncGenerator[str, None]:
        """发送 RAG 消息，流式返回 (无需意图识别，直接 RAG 流程)"""
        logger.info(f"RAG 消息: conversation={conversation_id}, model={model}")

        # 保存用户消息
        user_msg_id = str(uuid.uuid4())
        db = await get_db()
        try:
            await db.execute(
                "INSERT INTO messages (id, conversation_id, role, content, parent_message_id) "
                "VALUES (?, ?, 'user', ?, ?)",
                (user_msg_id, conversation_id, content, parent_message_id),
            )
            await db.execute(
                "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
                (conversation_id,),
            )
            await db.commit()
        finally:
            await db.close()

        # 创建 LLM 实例
        llm = await AgentFactory.get_llm(model)

        # 确保 pipeline 初始化
        pipeline = await self._ensure_pipeline(llm)

        # 加载错题范例
        bad_case_examples = await self._load_bad_case_examples()

        # 创建助手消息占位
        assistant_msg_id = str(uuid.uuid4())
        self._active_generations[assistant_msg_id] = True
        # 立即发送 message_id 给前端，用于停止操作
        yield sse_event("init", {"message_id": assistant_msg_id})
        full_content = ""
        thinking_parts = []
        tool_call_parts = []

        # 运行 RAG 流水线
        try:
            async for event in pipeline.run_stream(
                query=content,
                embedding_model=embedding_model,
                enable_query_rewriting=enable_query_rewriting,
                enable_hybrid_search=enable_hybrid_search,
                enable_reranking=enable_reranking,
                bad_case_examples=bad_case_examples,
            ):
                # 检查是否被请求停止
                if self.is_stopped(assistant_msg_id):
                    yield sse_event("thinking", {"content": "生成已停止"})
                    break

                # 解析 SSE 事件，收集内容
                if "token" in event:
                    try:
                        data = json.loads(event.split("data: ", 1)[1].strip())
                        full_content += data.get("content", "")
                    except Exception:
                        pass
                elif "thinking" in event:
                    try:
                        data = json.loads(event.split("data: ", 1)[1].strip())
                        thinking_parts.append(data.get("content", ""))
                    except Exception:
                        pass
                elif "tool_call" in event or "tool_result" in event:
                    tool_call_parts.append(event)

                yield event

            # 保存助手消息
            thinking_json = json.dumps(thinking_parts, ensure_ascii=False) if thinking_parts else None
            tool_calls_json = json.dumps(tool_call_parts, ensure_ascii=False) if tool_call_parts else None

            db = await get_db()
            try:
                await db.execute(
                    "INSERT INTO messages (id, conversation_id, role, content, thinking, tool_calls, parent_message_id) "
                    "VALUES (?, ?, 'assistant', ?, ?, ?, ?)",
                    (assistant_msg_id, conversation_id, full_content, thinking_json, tool_calls_json, user_msg_id),
                )
                await db.execute(
                    "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
                    (conversation_id,),
                )
                await db.commit()
            finally:
                await db.close()

            # 发送 done 事件
            yield sse_event("done", {
                "message_id": assistant_msg_id,
                "full_content": full_content,
                "conversation_id": conversation_id,
            })

        except Exception as e:
            logger.error(f"RAG 生成失败: {e}")
            yield sse_event("error", {
                "code": "RAG_GENERATION_ERROR",
                "message": str(e),
                "message_id": assistant_msg_id,
            })
        finally:
            self._active_generations.pop(assistant_msg_id, None)

    async def submit_feedback(self, conversation_id: str, message_id: str, is_correct: bool):
        """标记答案正确/错误，错误时自动创建错题记录"""
        db = await get_db()
        try:
            # 更新消息的 is_correct 字段
            await db.execute(
                "UPDATE messages SET is_correct = ? WHERE id = ?",
                (1 if is_correct else 0, message_id),
            )

            if not is_correct:
                # 查找该消息及对应的用户问题
                cursor = await db.execute(
                    "SELECT content, parent_message_id FROM messages WHERE id = ?",
                    (message_id,),
                )
                msg = await cursor.fetchone()
                if msg:
                    wrong_answer = msg["content"]
                    parent_id = msg["parent_message_id"]

                    question = ""
                    if parent_id:
                        cursor = await db.execute(
                            "SELECT content FROM messages WHERE id = ?",
                            (parent_id,),
                        )
                        parent = await cursor.fetchone()
                        if parent:
                            question = parent["content"]

                    # 检查是否已存在错题记录，避免重复创建
                    cursor = await db.execute(
                        "SELECT id FROM bad_cases WHERE message_id = ?",
                        (message_id,),
                    )
                    existing = await cursor.fetchone()
                    if existing:
                        logger.info(f"错题记录已存在: message_id={message_id}")
                    else:
                        # 创建错题记录
                        bad_case_id = str(uuid.uuid4())
                        await db.execute(
                            "INSERT INTO bad_cases (id, message_id, question, wrong_answer) "
                            "VALUES (?, ?, ?, ?)",
                            (bad_case_id, message_id, question, wrong_answer),
                        )
                        logger.info(f"创建错题记录: {bad_case_id}")
                else:
                    logger.warning(f"未找到消息: {message_id}, 无法创建错题")

            await db.commit()
        finally:
            await db.close()

        return {"status": "ok", "message_id": message_id, "is_correct": is_correct}


rag_service = RAGService()
