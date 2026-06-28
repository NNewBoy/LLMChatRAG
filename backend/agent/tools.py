"""Agent 工具定义 - RAG 工具、联网搜索等"""

import httpx
from config import settings
from utils.logger import logger


def create_rag_tool(rag_pipeline):
    """
    创建 RAG 检索工具
    Agent 调用此工具检索知识库文档
    """
    async def rag_search(query: str, top_k: int = 5) -> str:
        """在知识库中检索相关文档。

        Args:
            query: 搜索查询语句
            top_k: 返回结果数量

        Returns:
            检索到的文档内容，格式化后的文本
        """
        logger.info(f"Agent 调用 RAG 工具: query='{query}', top_k={top_k}")
        try:
            results = await rag_pipeline.search_only(query, top_k=top_k)
            if not results:
                return "未找到相关文档。"

            formatted = []
            for i, r in enumerate(results):
                text = r.get("text", "")
                filename = r.get("filename", "未知来源")
                formatted.append(f"[{i+1}] (来源: {filename})\n{text}")

            result_text = "\n\n".join(formatted)
            logger.info(f"RAG 工具返回 {len(results)} 条结果")
            return result_text
        except Exception as e:
            logger.error(f"RAG 检索失败: {e}")
            return f"检索失败: {e}"

    return rag_search


def create_web_search_tool():
    """
    创建联网搜索工具
    使用配置的搜索引擎 API 获取实时信息
    """
    async def web_search(query: str, num_results: int = 5) -> str:
        """搜索互联网获取实时信息。

        Args:
            query: 搜索关键词
            num_results: 返回结果数量

        Returns:
            搜索结果摘要
        """
        logger.info(f"Agent 调用联网搜索: query='{query}'")

        if not settings.search_api_url or not settings.search_api_key:
            return "联网搜索功能未配置，请设置 SEARCH_API_URL 和 SEARCH_API_KEY。"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    settings.search_api_url,
                    params={"q": query, "num": num_results, "api_key": settings.search_api_key},
                )
                response.raise_for_status()
                data = response.json()

            results = data.get("results", [])
            if not results:
                return "未找到相关搜索结果。"

            formatted = []
            for i, r in enumerate(results[:num_results]):
                title = r.get("title", "")
                snippet = r.get("snippet", "")
                url = r.get("url", "")
                formatted.append(f"[{i+1}] {title}\n{snippet}\n链接: {url}")

            return "\n\n".join(formatted)
        except Exception as e:
            logger.error(f"联网搜索失败: {e}")
            return f"搜索失败: {e}"

    return web_search
