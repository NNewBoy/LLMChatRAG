"""意图识别模块 - 判断用户问题是普通聊天还是需要 RAG 检索"""

import json
from utils.logger import logger


class IntentRouter:
    """
    判断用户输入意图：
    - "chat": 普通聊天，直接由 LLM 回答
    - "rag": 需要检索知识库，调用 RAG 工具

    当 enable_intent_recognition=false 时，跳过意图识别，
    所有问题直接按普通聊天处理，不加载 RAG 工具。
    """

    INTENT_PROMPT = """请判断用户问题的意图类型：

- chat: 普通闲聊、编程问题、常识问答、数学计算等不依赖特定文档的问题
- rag: 需要查询特定文档/知识库才能回答的问题（如"文档中提到了什么"、"根据上传的资料"等）

对话历史:
{history}

用户问题: {query}

请返回 JSON 格式: {{"intent": "chat" 或 "rag", "confidence": 0.0到1.0, "reason": "分类理由"}}
只返回 JSON，不要其他内容。"""

    async def classify(self, query: str, llm, conversation_history: list = None) -> dict:
        """
        通过 LLM 判断意图
        返回: {"intent": "chat" | "rag", "confidence": float, "reason": str}
        """
        history_text = ""
        if conversation_history:
            recent = conversation_history[-5:]  # 最近 5 条消息
            history_text = "\n".join(
                f"{m.get('role', 'user')}: {m.get('content', '')[:200]}"
                for m in recent
            )

        prompt = self.INTENT_PROMPT.format(history=history_text, query=query)

        try:
            response = await llm.ainvoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)

            # 尝试解析 JSON
            # 移除可能的 markdown 代码块标记
            content = content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1])

            result = json.loads(content)
            intent = result.get("intent", "chat")
            confidence = float(result.get("confidence", 0.5))
            reason = result.get("reason", "")

            logger.info(f"意图识别结果: intent={intent}, confidence={confidence}, reason={reason}")
            return {"intent": intent, "confidence": confidence, "reason": reason}

        except Exception as e:
            logger.warning(f"意图识别失败，默认为 chat: {e}")
            return {"intent": "chat", "confidence": 0.5, "reason": "意图识别失败，默认普通对话"}
