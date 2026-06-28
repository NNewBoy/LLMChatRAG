"""FAISS 向量存储管理"""

import json
import numpy as np
from pathlib import Path
from config import settings
from utils.logger import logger

try:
    import faiss
except ImportError:
    faiss = None
    logger.warning("faiss 未安装，向量存储功能不可用")


class FAISSVectorStore:
    """FAISS 向量存储管理"""

    def __init__(self):
        self.index_path = Path(settings.faiss_db_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        self.index = None
        self.dimension = 0
        self.metadata: list[dict] = []  # 文档元数据映射
        self._load()

    def _load(self):
        """从磁盘加载索引"""
        if faiss is None:
            return

        index_file = self.index_path / "faiss.index"
        meta_file = self.index_path / "metadata.json"

        if index_file.exists() and meta_file.exists():
            try:
                self.index = faiss.read_index(str(index_file))
                with open(meta_file, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                self.dimension = self.index.d
                logger.info(f"加载 FAISS 索引: {len(self.metadata)} 条记录, 维度: {self.dimension}")
            except Exception as e:
                logger.error(f"加载 FAISS 索引失败: {e}")
                self.index = None
                self.metadata = []

    def _save(self):
        """持久化索引到磁盘"""
        if faiss is None or self.index is None:
            return

        index_file = self.index_path / "faiss.index"
        meta_file = self.index_path / "metadata.json"

        faiss.write_index(self.index, str(index_file))
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        logger.info(f"保存 FAISS 索引: {len(self.metadata)} 条记录")

    def add(self, vectors: list, chunks: list[dict], document_id: str = None):
        """添加向量及对应元数据到索引"""
        if faiss is None or not vectors:
            return

        vectors = np.array(vectors, dtype=np.float32)

        # 如果索引不存在，创建新索引
        if self.index is None:
            self.dimension = vectors.shape[1]
            self.index = faiss.IndexFlatIP(self.dimension)  # 内积相似度 (需归一化)
            logger.info(f"创建新 FAISS 索引, 维度: {self.dimension}")

        if vectors.shape[1] != self.dimension:
            raise ValueError(f"向量维度不匹配: 期望 {self.dimension}, 实际 {vectors.shape[1]}")

        # 归一化向量 (用于余弦相似度)
        faiss.normalize_L2(vectors)
        self.index.add(vectors)

        # 添加元数据
        for chunk in chunks:
            meta = {
                "text": chunk["text"],
                "document_id": document_id or chunk.get("document_id", ""),
                "chunk_index": chunk.get("index", 0),
                "filename": chunk.get("filename", ""),
            }
            self.metadata.append(meta)

        self._save()
        logger.info(f"添加 {len(vectors)} 个向量到 FAISS 索引")

    def search(self, query_vector: list, top_k: int = 10) -> list[dict]:
        """向量相似度检索，返回 Top-K 结果"""
        if faiss is None or self.index is None or not self.metadata:
            return []

        query_vector = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(query_vector)

        k = min(top_k, len(self.metadata))
        scores, indices = self.index.search(query_vector, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            meta = self.metadata[idx]
            results.append({
                "text": meta["text"],
                "document_id": meta.get("document_id", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "filename": meta.get("filename", ""),
                "score": float(score),
            })
        return results

    def remove(self, document_id: str):
        """删除指定文档的所有向量 (重建索引)"""
        if not self.metadata:
            return

        # 过滤掉指定文档的元数据
        keep_indices = [
            i for i, m in enumerate(self.metadata)
            if m.get("document_id") != document_id
        ]

        if len(keep_indices) == len(self.metadata):
            return  # 没有需要删除的

        if len(keep_indices) == 0:
            # 全部删除
            self.index = None
            self.metadata = []
            self._save()
            return

        # 重建索引
        if faiss is not None and self.index is not None:
            # 获取所有向量
            all_vectors = faiss.rev_swig_ptr(
                self.index.get_xb(), self.index.ntotal * self.dimension
            )
            all_vectors = np.array(all_vectors, dtype=np.float32).reshape(-1, self.dimension)

            # 保留的向量
            keep_vectors = all_vectors[keep_indices]
            keep_metadata = [self.metadata[i] for i in keep_indices]

            # 重建索引
            self.index = faiss.IndexFlatIP(self.dimension)
            self.index.add(keep_vectors)
            self.metadata = keep_metadata
            self._save()
            logger.info(f"删除文档 {document_id} 的向量, 剩余 {len(self.metadata)} 条")

    def get_stats(self) -> dict:
        """获取索引统计信息"""
        return {
            "total_vectors": len(self.metadata),
            "dimension": self.dimension,
            "has_index": self.index is not None,
        }
