"""重排序模块 - 使用 LLM 对检索结果精排"""

import json
from langchain_core.messages import HumanMessage, SystemMessage
from utils.logger import logger


class Reranker:
    """使用 LLM 对检索结果进行重排序"""

    def __init__(self, llm=None):
        self.llm = llm

    async def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_n: int = None,
        enable_reranking: bool = False,
    ) -> list[dict]:
        """
        使用 LLM 对候选文档进行相关性评分，返回 Top-N
        enable_reranking=False: 直接截取前 top_n 条
        enable_reranking=True: 使用 LLM 重排序
        """
        from config import settings
        top_n = top_n or settings.rag_top_n

        if not enable_reranking or not self.llm:
            logger.info(f"重排序未启用，直接返回前 {top_n} 条")
            return candidates[:top_n]

        if not candidates:
            return []

        logger.info(f"开始 LLM 重排序, 候选数: {len(candidates)}, 目标数: {top_n}")

        # 构造 Prompt
        docs_text = ""
        for i, chunk in enumerate(candidates):
            text = chunk["text"][:500]  # 截断避免 token 过长
            docs_text += f"[{i}] {text}\n\n"

        prompt = f"""请对以下文档片段与用户查询的相关性进行评分。

用户查询: {query}

文档片段:
{docs_text}

请返回 JSON 数组，每个元素包含 index (文档序号) 和 score (相关性分数 0-10)。
只返回 JSON，不要其他文字。
格式: [{{"index": 0, "score": 8.5}}, {{"index": 1, "score": 6.0}}]"""

        try:
            messages = [
                SystemMessage(content="你是一个文档相关性评估专家。"),
                HumanMessage(content=prompt),
            ]
            response = await self.llm.ainvoke(messages)
            scores = self._parse_scores(response.content)

            # 按分数排序
            scored_candidates = []
            for item in scores:
                idx = item["index"]
                if 0 <= idx < len(candidates):
                    scored_candidates.append({**candidates[idx], "rerank_score": item["score"]})

            scored_candidates.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
            results = scored_candidates[:top_n]
            logger.info(f"LLM 重排序完成, 返回 {len(results)} 条")
            return results
        except Exception as e:
            logger.error(f"LLM 重排序失败: {e}, 回退到原始排序")
            return candidates[:top_n]

    def _parse_scores(self, content: str) -> list[dict]:
        """解析 LLM 返回的评分 JSON"""
        try:
            # 尝试提取 JSON 数组
            text = content.strip()
            # 移除可能的 markdown 代码块标记
            if text.startswith("```"):
                lines = text.split("\n")
                text = "\n".join(lines[1:-1]) if lines[-1].startswith("```") else "\n".join(lines[1:])
            return json.loads(text)
        except (json.JSONDecodeError, IndexError):
            logger.warning(f"解析重排序评分失败: {content[:200]}")
            return []
