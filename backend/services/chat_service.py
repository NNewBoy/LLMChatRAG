"""普通对话业务逻辑"""

import uuid
import json
from datetime import datetime
from typing import AsyncGenerator
from models.database import get_db
from agent.agent_factory import AgentFactory
from agent.intent_router import IntentRouter
from utils.logger import logger
from utils.sse import sse_event


class ChatService:
    """普通对话服务，处理 Agent 对话流程"""

    def __init__(self):
        self.agent_factory = AgentFactory()
        self.intent_router = IntentRouter()
        # 存储活跃的生成任务，用于停止
        self._active_generations: dict[str, bool] = {}

    async def get_conversations(self, mode: str = "chat") -> list[dict]:
        """获取历史会话列表"""
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT * FROM conversations WHERE mode = ? ORDER BY updated_at DESC",
                (mode,),
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await db.close()

    async def create_conversation(self, mode: str, title: str = "") -> dict:
        """创建新会话"""
        conv_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        db = await get_db()
        try:
            await db.execute(
                "INSERT INTO conversations (id, title, mode, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (conv_id, title, mode, now, now),
            )
            await db.commit()
            return {"id": conv_id, "title": title, "mode": mode, "created_at": now, "updated_at": now}
        finally:
            await db.close()

    async def delete_conversation(self, conversation_id: str):
        """删除会话及其所有消息"""
        db = await get_db()
        try:
            await db.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            await db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            await db.commit()
        finally:
            await db.close()

    async def get_messages(self, conversation_id: str) -> list[dict]:
        """获取会话消息历史"""
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
                (conversation_id,),
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await db.close()

    async def save_message(self, conversation_id: str, role: str, content: str,
                           thinking: str = None, tool_calls: str = None,
                           parent_message_id: str = None) -> str:
        """保存消息到数据库"""
        msg_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        db = await get_db()
        try:
            await db.execute(
                """INSERT INTO messages (id, conversation_id, role, content, thinking, tool_calls, parent_message_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (msg_id, conversation_id, role, content, thinking, tool_calls, parent_message_id, now),
            )
            # 更新会话的 updated_at
            await db.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conversation_id),
            )
            # 如果是第一条用户消息，更新会话标题
            if role == "user":
                cursor = await db.execute(
                    "SELECT COUNT(*) as cnt FROM messages WHERE conversation_id = ? AND role = 'user'",
                    (conversation_id,),
                )
                row = await cursor.fetchone()
                if row["cnt"] == 1:
                    title = content[:50] + ("..." if len(content) > 50 else "")
                    await db.execute(
                        "UPDATE conversations SET title = ? WHERE id = ?",
                        (title, conversation_id),
                    )
            await db.commit()
            return msg_id
        finally:
            await db.close()

    async def delete_message(self, conversation_id: str, message_id: str):
        """删除指定消息"""
        db = await get_db()
        try:
            await db.execute("DELETE FROM messages WHERE id = ?", (message_id,))
            await db.commit()
        finally:
            await db.close()

    async def delete_message_and_after(self, conversation_id: str, message_id: str):
        """删除指定消息及其之后的所有消息（用于重新生成）"""
        db = await get_db()
        try:
            cursor = await db.execute(
                "SELECT created_at FROM messages WHERE id = ?", (message_id,)
            )
            row = await cursor.fetchone()
            if row:
                await db.execute(
                    "DELETE FROM messages WHERE conversation_id = ? AND created_at >= ?",
                    (conversation_id, row["created_at"]),
                )
                await db.commit()
        finally:
            await db.close()

    async def get_message_history(self, conversation_id: str, parent_message_id: str = None, exclude_msg_id: str = None) -> list[dict]:
        """获取对话历史（用于构建上下文）"""
        db = await get_db()
        try:
            if parent_message_id:
                # 追问模式：获取父消息之前的所有消息
                cursor = await db.execute(
                    "SELECT created_at FROM messages WHERE id = ?", (parent_message_id,)
                )
                row = await cursor.fetchone()
                if row:
                    cursor = await db.execute(
                        "SELECT * FROM messages WHERE conversation_id = ? AND created_at < ? ORDER BY created_at ASC",
                        (conversation_id, row["created_at"]),
                    )
                else:
                    cursor = await db.execute(
                        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
                        (conversation_id,),
                    )
            else:
                cursor = await db.execute(
                    "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
                    (conversation_id,),
                )
            rows = await cursor.fetchall()
            messages = [dict(row) for row in rows]
            # 排除指定消息（如当前用户消息，避免重复）
            if exclude_msg_id:
                messages = [m for m in messages if m["id"] != exclude_msg_id]
            return messages
        finally:
            await db.close()

    def request_stop(self, message_id: str):
        """请求停止生成"""
        self._active_generations[message_id] = False
        logger.info(f"请求停止生成: {message_id}")

    def is_stopped(self, message_id: str) -> bool:
        """检查是否被请求停止"""
        return not self._active_generations.get(message_id, True)

    async def chat_stream(
        self,
        conversation_id: str,
        content: str,
        model: str,
        image: str = None,
        parent_message_id: str = None,
        enable_intent_recognition: bool = True,
    ) -> AsyncGenerator[str, None]:
        """普通对话流式生成"""
        # 保存用户消息
        user_msg_id = await self.save_message(
            conversation_id, "user", content, parent_message_id=parent_message_id
        )

        # 创建 assistant 消息占位 ID
        assistant_msg_id = str(uuid.uuid4())
        self._active_generations[assistant_msg_id] = True

        # 立即发送 message_id 给前端，用于停止操作
        yield sse_event("init", {"message_id": assistant_msg_id})

        thinking_parts = []
        tool_call_parts = []
        full_content = ""

        try:
            # 获取对话历史（排除当前用户消息，避免重复）
            history = await self.get_message_history(conversation_id, parent_message_id, exclude_msg_id=user_msg_id)
            logger.info(f"Chat 对话历史: {len(history)} 条消息, conversation={conversation_id}")

            # 创建 LLM 实例
            llm = await AgentFactory.get_llm(model)
            logger.info(f"LLM 实例创建: model={model}")

            # 意图识别（如果启用）
            if enable_intent_recognition:
                logger.info("开始意图识别...")
                yield sse_event("thinking", {"content": "正在分析问题意图..."})
                intent_result = await self.intent_router.classify(content, llm, history)
                logger.info(f"意图识别完成: intent={intent_result['intent']}, confidence={intent_result['confidence']}")
                yield sse_event("intent", intent_result)

                if intent_result["intent"] == "rag":
                    # 调用 RAG 工具
                    yield sse_event("thinking", {"content": "检测到需要查询知识库，正在调用 RAG 工具..."})
                    tool_call_parts.append({
                        "tool_name": "rag_search",
                        "tool_input": {"query": content},
                    })
                    yield sse_event("tool_call", {
                        "tool_name": "rag_search",
                        "tool_input": {"query": content},
                        "timestamp": datetime.now().isoformat(),
                    })

                    # 执行 RAG 检索
                    from rag.pipeline import RAGPipeline
                    rag = RAGPipeline(llm)
                    results = await rag.search_only(content)

                    if results:
                        rag_context = "\n\n".join(
                            f"[{i+1}] (来源: {r.get('filename', '')})\n{r.get('text', '')}"
                            for i, r in enumerate(results)
                        )
                        tool_output = f"找到 {len(results)} 条相关文档"
                        tool_call_parts.append({"tool_name": "rag_search", "tool_output": tool_output})
                        yield sse_event("tool_result", {
                            "tool_name": "rag_search",
                            "tool_output": tool_output,
                            "timestamp": datetime.now().isoformat(),
                        })

                        # 构建 RAG 增强的 prompt
                        from rag.generator import Generator
                        gen = Generator(llm)
                        prompt = gen.build_prompt(content, results, [])
                        messages = [{"role": "system", "content": prompt}]
                        logger.info(f"Chat RAG 路径: 检索到 {len(results)} 条文档, 已构建 RAG prompt")
                    else:
                        yield sse_event("tool_result", {
                            "tool_name": "rag_search",
                            "tool_output": "未找到相关文档",
                            "timestamp": datetime.now().isoformat(),
                        })
                        messages = [{"role": "system", "content": "你是一个智能助手。"}]
                else:
                    messages = [{"role": "system", "content": "你是一个智能助手，请友好地回答用户的问题。"}]
            else:
                messages = [{"role": "system", "content": "你是一个智能助手，请友好地回答用户的问题。"}]

            # 添加历史消息
            for msg in history[-10:]:  # 最近 10 条
                if msg["role"] in ("user", "assistant"):
                    messages.append({"role": msg["role"], "content": msg["content"]})

            # 添加当前用户消息
            if image:
                # 多模态: 文本 + 图片合并为一条消息
                image_url = image if image.startswith("data:") else f"data:image/jpeg;base64,{image}"
                messages.append({"role": "user", "content": [
                    {"type": "text", "text": content},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ]})
            else:
                messages.append({"role": "user", "content": content})

            # 流式生成
            from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
            lc_messages = []
            for m in messages:
                if m["role"] == "system":
                    lc_messages.append(SystemMessage(content=m["content"]))
                elif m["role"] == "user":
                    lc_messages.append(HumanMessage(content=m["content"]))
                elif m["role"] == "assistant":
                    lc_messages.append(AIMessage(content=m["content"]))

            # 打印最终发送给 LLM 的 prompt
            logger.info(f"Chat 最终 Prompt ({len(lc_messages)} 条消息):")
            for i, m in enumerate(lc_messages):
                content_preview = m.content[:500] if isinstance(m.content, str) else str(m.content)[:500]
                logger.info(f"  [{i}] {m.__class__.__name__}: {content_preview}{'...' if len(str(m.content)) > 500 else ''}")

            logger.info("开始 LLM 流式生成...")
            async for chunk in llm.astream(lc_messages):
                if self.is_stopped(assistant_msg_id):
                    yield sse_event("thinking", {"content": "生成已停止"})
                    break
                token = chunk.content if hasattr(chunk, "content") else str(chunk)
                if token:
                    full_content += token
                    yield sse_event("token", {"content": token, "message_id": assistant_msg_id})

            # 保存 assistant 消息
            thinking_json = json.dumps(thinking_parts, ensure_ascii=False) if thinking_parts else None
            tool_calls_json = json.dumps(tool_call_parts, ensure_ascii=False) if tool_call_parts else None
            saved_msg_id = await self.save_message(
                conversation_id, "assistant", full_content,
                thinking=thinking_json, tool_calls=tool_calls_json,
                parent_message_id=user_msg_id,
            )

            yield sse_event("done", {
                "message_id": saved_msg_id,
                "full_content": full_content,
                "conversation_id": conversation_id,
            })

        except Exception as e:
            logger.error(f"对话生成失败: {e}")
            yield sse_event("error", {
                "code": "GENERATION_ERROR",
                "message": f"生成失败: {e}",
                "message_id": assistant_msg_id,
            })
        finally:
            self._active_generations.pop(assistant_msg_id, None)

    async def regenerate_stream(
        self, conversation_id: str, message_id: str, model: str
    ) -> AsyncGenerator[str, None]:
        """重新生成回答"""
        # 获取被重新生成的消息
        db = await get_db()
        try:
            cursor = await db.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
            msg = await cursor.fetchone()
        finally:
            await db.close()

        if not msg:
            yield sse_event("error", {"code": "NOT_FOUND", "message": "消息不存在"})
            return

        # 删除该消息及其之后的所有消息
        await self.delete_message_and_after(conversation_id, message_id)

        # 获取父消息 ID，用于确定上下文
        parent_id = dict(msg).get("parent_message_id")

        # 获取原始用户消息内容
        if parent_id:
            db = await get_db()
            try:
                cursor = await db.execute("SELECT * FROM messages WHERE id = ?", (parent_id,))
                parent_msg = await cursor.fetchone()
                if parent_msg:
                    content = dict(parent_msg)["content"]
                else:
                    yield sse_event("error", {"code": "NOT_FOUND", "message": "父消息不存在"})
                    return
            finally:
                await db.close()
        else:
            # 找到最近一条用户消息
            content = dict(msg).get("content", "")

        # 重新生成
        async for event in self.chat_stream(
            conversation_id, content, model,
            parent_message_id=parent_id,
            enable_intent_recognition=True,
        ):
            yield event


chat_service = ChatService()
