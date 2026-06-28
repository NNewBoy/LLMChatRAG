"""检索模块 - 使用 LlamaIndex 向量检索 + BM25 混合检索"""

import math
import re
from collections import Counter
from rag.vector_store import FAISSVectorStore
from rag.embedder import Embedder
from config import settings
from utils.logger import logger


class BM25:
    """BM25 关键词检索实现"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_freqs = []
        self.idf = {}
        self.avgdl = 0
        self.doc_len = []
        self.n_docs = 0

    def _tokenize(self, text: str) -> list[str]:
        """简单分词：中文按字，英文按词"""
        words = re.findall(r'[a-zA-Z]+', text.lower())
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        return words + chinese_chars

    def fit(self, documents: list[str]):
        """构建 BM25 索引"""
        self.n_docs = len(documents)
        self.doc_freqs = []
        self.doc_len = []
        df = Counter()

        for doc in documents:
            tokens = self._tokenize(doc)
            self.doc_len.append(len(tokens))
            freq = Counter(tokens)
            self.doc_freqs.append(freq)
            for word in freq.keys():
                df[word] += 1

        self.avgdl = sum(self.doc_len) / self.n_docs if self.n_docs > 0 else 0

        for word, freq in df.items():
            self.idf[word] = math.log((self.n_docs - freq + 0.5) / (freq + 0.5) + 1)

    def search(self, query: str, top_k: int = 10) -> list[tuple[int, float]]:
        """检索最相关的文档，返回 [(doc_index, score), ...]"""
        query_tokens = self._tokenize(query)
        scores = []

        for i in range(self.n_docs):
            score = 0.0
            doc_freq = self.doc_freqs[i]
            dl = self.doc_len[i]
            for word in query_tokens:
                if word in self.idf and word in doc_freq:
                    idf = self.idf[word]
                    tf = doc_freq[word]
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                    score += idf * numerator / denominator
            scores.append((i, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class HybridRetriever:
    """
    混合检索: LlamaIndex 向量检索 + BM25 关键词检索

    由前端参数 enable_hybrid_search 控制是否启用混合检索。
    环境变量 HYBRID_ALPHA / HYBRID_BETA 控制权重比。

    混合公式: score = alpha * vector_score + beta * bm25_score
    """

    def __init__(self):
        self.vector_store = FAISSVectorStore()
        self.embedder = Embedder()
        self.bm25 = BM25()
        self.alpha = settings.hybrid_alpha
        self.beta = settings.hybrid_beta
        self._bm25_fitted = False

    def fit_bm25(self, chunks: list[dict]):
        """用文档块构建 BM25 索引"""
        texts = [c["text"] for c in chunks]
        self.bm25.fit(texts)
        self._bm25_fitted = True
        logger.info(f"BM25 索引构建完成, 文档数: {len(texts)}")

    async def retrieve(
        self,
        query: str,
        top_k: int = None,
        enable_hybrid: bool = False,
        embedding_model: str = None,
    ) -> list[dict]:
        """
        检索相关文档块
        enable_hybrid=False: 仅向量检索 (使用 LlamaIndex FaissVectorStore)
        enable_hybrid=True: 混合检索 (向量 + BM25)
        """
        top_k = top_k or settings.rag_top_k
        logger.info(f"检索查询: '{query}', top_k={top_k}, hybrid={enable_hybrid}")

        if enable_hybrid and self._bm25_fitted:
            return await self._hybrid_search(query, top_k, embedding_model)
        else:
            return await self._vector_search(query, top_k, embedding_model)

    async def _vector_search(self, query: str, top_k: int, model: str = None) -> list[dict]:
        """LlamaIndex 向量检索"""
        query_vector = await self.embedder.embed_query(query, model)
        if not query_vector:
            logger.warning("查询向量化结果为空")
            return []
        results = self.vector_store.search(query_vector, top_k=top_k)
        logger.info(f"向量检索返回 {len(results)} 条结果")
        return results

    async def _hybrid_search(self, query: str, top_k: int, model: str = None) -> list[dict]:
        """混合检索: 向量 + BM25 加权融合"""
        # 向量检索
        query_vector = await self.embedder.embed_query(query, model)
        vector_results = self.vector_store.search(query_vector, top_k=top_k * 2) if query_vector else []

        # BM25 检索
        bm25_results = self.bm25.search(query, top_k=top_k * 2)

        # 归一化分数并融合
        max_vec_score = max((r["score"] for r in vector_results), default=1.0)
        max_bm25_score = max((s for _, s in bm25_results), default=1.0)

        # 构建分数映射 (以文本前100字符为 key 去重)
        vec_scores = {}
        for r in vector_results:
            key = r.get("text", "")[:100]
            vec_scores[key] = r["score"] / max_vec_score if max_vec_score > 0 else 0

        bm25_scores = {}
        for idx, s in bm25_results:
            if 0 <= idx < len(self.vector_store.metadata):
                meta = self.vector_store.metadata[idx]
                key = meta.get("text", "")[:100]
                bm25_scores[key] = s / max_bm25_score if max_bm25_score > 0 else 0

        # 合并所有 key
        all_keys = set(vec_scores.keys()) | set(bm25_scores.keys())

        # 计算混合分数
        hybrid_results = []
        for key in all_keys:
            vec_score = vec_scores.get(key, 0.0)
            bm25_score = bm25_scores.get(key, 0.0)
            hybrid_score = self.alpha * vec_score + self.beta * bm25_score

            # 从 metadata 中查找对应记录
            for meta in self.vector_store.metadata:
                if meta.get("text", "")[:100] == key:
                    hybrid_results.append({**meta, "score": hybrid_score})
                    break

        hybrid_results.sort(key=lambda x: x["score"], reverse=True)
        results = hybrid_results[:top_k]
        logger.info(f"混合检索返回 {len(results)} 条结果")
        return results
