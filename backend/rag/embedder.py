"""向量化模块 - 支持 LlamaIndex OpenAIEmbedding 或硅基流动原生 API

通过环境变量 EMBEDDING_PROVIDER 切换:
- "llama_index" (默认): 使用 LlamaIndex OpenAIEmbedding (兼容 OpenAI 接口)
- "siliconflow": 使用硅基流动原生 API (httpx 直接调用)
  接口文档: https://api-docs.siliconflow.cn/docs/api/embeddings-post
"""

import httpx
from config import settings
from utils.logger import logger


class SiliconFlowEmbedder:
    """
    硅基流动原生 Embedding API 客户端
    接口文档: https://api-docs.siliconflow.cn/docs/api/embeddings-post

    请求: POST {base_url}/embeddings
    请求体: {"model": "...", "input": ["text1", "text2"], "encoding_format": "float"}
    响应: {"data": [{"embedding": [...], "index": 0}, ...], "model": "...", "usage": {...}}
    """

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        """同步批量获取文本向量"""
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": texts,
            "encoding_format": "float",
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        # 按 index 排序确保顺序正确
        embeddings_data = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in embeddings_data]

    def _get_query_embedding(self, query: str) -> list[float]:
        """同步获取查询向量"""
        result = self._get_text_embeddings([query])
        return result[0] if result else []


class Embedder:
    """
    向量化模块，支持两种后端:
    1. LlamaIndex OpenAIEmbedding (通过 OpenAI 兼容接口)
    2. 硅基流动原生 API (httpx 直接调用)

    通过环境变量 EMBEDDING_PROVIDER 切换:
    - "llama_index": 使用 LlamaIndex OpenAIEmbedding
    - "siliconflow": 使用硅基流动原生 API
    """

    def __init__(self):
        self.api_key = settings.embedding_api_key
        self.base_url = settings.embedding_api_base_url
        self.default_model = settings.embedding_model
        # 通过配置决定使用哪种 Embedding 实现
        self.provider = getattr(settings, "embedding_provider", "llama_index")

    def _create_embedding(self, model: str = None):
        """创建 Embedding 实例，根据 provider 配置返回不同实现"""
        use_model = model or self.default_model

        if self.provider == "siliconflow":
            return SiliconFlowEmbedder(
                api_key=self.api_key,
                base_url=self.base_url,
                model=use_model,
            )

        # 默认: LlamaIndex OpenAIEmbedding (兼容 OpenAI 接口的硅基流动)
        from llama_index.embeddings.openai import OpenAIEmbedding
        return OpenAIEmbedding(
            model=use_model,
            api_key=self.api_key,
            api_base_url=self.base_url,
        )

    async def embed(self, texts: list[str], model: str = None) -> list[list[float]]:
        """将文本列表转换为向量列表，model 参数可覆盖默认模型"""
        if not texts:
            return []

        logger.info(
            f"向量化 {len(texts)} 条文本, 模型: {model or self.default_model}, "
            f"provider: {self.provider}"
        )
        embed_model = self._create_embedding(model)

        all_embeddings = []
        batch_size = 64
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = embed_model._get_text_embeddings(batch)
            all_embeddings.extend(embeddings)

        logger.info(f"向量化完成, 共 {len(all_embeddings)} 个向量")
        return all_embeddings

    async def embed_query(self, query: str, model: str = None) -> list[float]:
        """将查询文本转换为向量"""
        embed_model = self._create_embedding(model)
        return embed_model._get_query_embedding(query)
