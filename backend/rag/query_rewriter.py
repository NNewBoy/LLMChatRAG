"""Query 改写模块 - 使用 LLM 改写或扩展用户问题"""

import json
from langchain_core.messages import HumanMessage, SystemMessage
from utils.logger import logger


class QueryRewriter:
    """使用 LLM 改写用户查询，提高检索召回率"""

    def __init__(self, llm=None):
        self.llm = llm

    SYSTEM_PROMPT = """你是一个查询改写助手。你的任务是改写用户的问题，使其更适合文档检索。
请遵循以下规则：
1. 扩展缩写和代词，使问题更加明确
2. 如果问题是口语化的，改写为更正式的检索查询
3. 如果问题包含多个子问题，拆分为多个查询
4. 保留原始问题的核心意图
5. 只返回改写后的查询文本，不要添加额外说明

如果原始问题已经很清晰，直接返回原问题。"""

    async def rewrite(self, query: str, llm=None) -> str:
        """
        使用 LLM 改写查询
        返回改写后的查询字符串
        """
        use_llm = llm or self.llm
        if not use_llm:
            logger.warning("未提供 LLM，跳过 Query 改写")
            return query

        logger.info(f"Query 改写: 原始查询='{query}'")

        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=f"请改写以下查询以用于文档检索:\n\n{query}"),
        ]

        try:
            response = await use_llm.ainvoke(messages)
            rewritten = response.content.strip()
            logger.info(f"Query 改写完成: 改写后='{rewritten}'")
            return rewritten
        except Exception as e:
            logger.error(f"Query 改写失败: {e}, 使用原始查询")
            return query
