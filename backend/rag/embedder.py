"""向量化模块 - 使用 Embedding 模型将文本转换为向量"""

import httpx
from config import settings
from utils.logger import logger


class Embedder:
    """
    使用硅基流动 (SiliconFlow) Embedding API 进行向量化
    参考文档: https://api-docs.siliconflow.cn/docs/api/embeddings-post
    支持通过前端参数动态切换 Embedding 模型。
    """

    def __init__(self):
        self.api_key = settings.embedding_api_key
        self.base_url = settings.embedding_api_base_url
        self.default_model = settings.embedding_model

    async def embed(self, texts: list[str], model: str = None) -> list[list[float]]:
        """将文本列表转换为向量列表，model 参数可覆盖默认模型"""
        model = model or self.default_model
        if not texts:
            return []

        logger.info(f"向量化 {len(texts)} 条文本, 模型: {model}")

        # 分批处理，每批最多 64 条
        all_embeddings = []
        batch_size = 64
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = await self._call_api(batch, model)
            all_embeddings.extend(embeddings)

        logger.info(f"向量化完成, 共 {len(all_embeddings)} 个向量")
        return all_embeddings

    async def embed_query(self, query: str, model: str = None) -> list[float]:
        """将查询文本转换为向量"""
        result = await self.embed([query], model)
        return result[0] if result else []

    async def _call_api(self, texts: list[str], model: str) -> list[list[float]]:
        """调用 Embedding API"""
        url = self.base_url
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "input": texts,
            "encoding_format": "float",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        # 按 index 排序确保顺序正确
        embeddings_data = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in embeddings_data]
