"""Agent 工具定义 - RAG 工具"""

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
