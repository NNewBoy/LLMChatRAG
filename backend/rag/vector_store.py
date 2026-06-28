"""FAISS 向量存储管理 - 使用 LlamaIndex FaissVectorStore"""

import json
from pathlib import Path
from llama_index.vector_stores.faiss import FaissVectorStore
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.schema import TextNode
from config import settings
from utils.logger import logger

try:
    import faiss
except ImportError:
    faiss = None
    logger.warning("faiss 未安装，向量存储功能不可用")


class FAISSVectorStore:
    """
    基于 LlamaIndex FaissVectorStore 的向量存储管理
    - 支持文档的增删查
    - 持久化到磁盘
    - 兼容原有接口 (metadata 列表, search, add, remove)
    """

    def __init__(self):
        self.index_path = Path(settings.faiss_db_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        self.dimension = 0
        self.metadata: list[dict] = []  # 文档元数据映射
        self._llama_store: FaissVectorStore | None = None
        self._storage_context: StorageContext | None = None
        self._load()

    def _load(self):
        """从磁盘加载已有的 LlamaIndex FAISS 索引"""
        if faiss is None:
            return

        index_file = self.index_path / "faiss.index"
        meta_file = self.index_path / "metadata.json"

        if index_file.exists():
            try:
                # 加载 FAISS 索引
                faiss_index = faiss.read_index(str(index_file))
                self.dimension = faiss_index.d
                self._llama_store = FaissVectorStore(faiss_index=faiss_index)
                self._storage_context = StorageContext.from_defaults(
                    vector_store=self._llama_store
                )
                logger.info(f"加载 LlamaIndex FAISS 索引, 维度: {self.dimension}")
            except Exception as e:
                logger.error(f"加载 LlamaIndex FAISS 索引失败: {e}")
                self._init_empty_store()

        # 加载元数据
        if meta_file.exists():
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                logger.info(f"加载元数据: {len(self.metadata)} 条记录")
            except Exception as e:
                logger.error(f"加载元数据失败: {e}")
                self.metadata = []

    def _init_empty_store(self):
        """初始化空存储"""
        if faiss is None:
            return
        # 使用默认维度 1024 (BGE 模型)，会在第一次 add 时重建
        self._llama_store = None
        self._storage_context = None

    def _save(self):
        """持久化 FAISS 索引到磁盘"""
        if faiss is None or self._llama_store is None:
            return

        index_file = self.index_path / "faiss.index"
        try:
            faiss_index = self._llama_store._faiss_index
            faiss.write_index(faiss_index, str(index_file))
            logger.info(f"保存 FAISS 索引: {len(self.metadata)} 条记录")
        except Exception as e:
            logger.error(f"保存 FAISS 索引失败: {e}")

        # 保存元数据
        meta_file = self.index_path / "metadata.json"
        try:
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存元数据失败: {e}")

    def add(self, vectors: list, chunks: list[dict], document_id: str = None):
        """添加向量及对应元数据到索引"""
        if faiss is None or not vectors:
            return

        import numpy as np
        vectors_np = np.array(vectors, dtype=np.float32)
        self.dimension = vectors_np.shape[1]

        # 如果索引不存在，创建新索引
        if self._llama_store is None:
            faiss_index = faiss.IndexFlatIP(self.dimension)
            self._llama_store = FaissVectorStore(faiss_index=faiss_index)
            self._storage_context = StorageContext.from_defaults(
                vector_store=self._llama_store
            )
            logger.info(f"创建新 LlamaIndex FAISS 索引, 维度: {self.dimension}")

        # 构建 TextNode 列表
        nodes = []
        for i, (vec, chunk) in enumerate(zip(vectors_np, chunks)):
            meta = {
                "text": chunk["text"],
                "document_id": document_id or chunk.get("document_id", ""),
                "chunk_index": chunk.get("index", 0),
                "filename": chunk.get("filename", ""),
            }
            node = TextNode(
                text=chunk["text"],
                embedding=vec.tolist(),
                metadata={
                    "document_id": meta["document_id"],
                    "filename": meta["filename"],
                    "chunk_index": meta["chunk_index"],
                }
            )
            nodes.append(node)
            self.metadata.append(meta)

        # 添加到 LlamaIndex 存储
        self._llama_store.add(nodes)
        # 验证向量是否真正写入
        if hasattr(self._llama_store, '_faiss_index') and self._llama_store._faiss_index:
            ntotal = self._llama_store._faiss_index.ntotal
            logger.info(f"添加 {len(nodes)} 个向量到 LlamaIndex FAISS 索引, 当前索引总量: {ntotal}")
        else:
            logger.warning("无法验证 FAISS 索引总量")
        self._save()

    def search(self, query_vector: list, top_k: int = 10) -> list[dict]:
        """向量相似度检索，返回 Top-K 结果"""
        if faiss is None or self._llama_store is None or not self.metadata:
            logger.warning(f"search 跳过: faiss={faiss is not None}, store={self._llama_store is not None}, metadata_count={len(self.metadata)}")
            return []

        # 验证 FAISS 索引状态
        if hasattr(self._llama_store, '_faiss_index') and self._llama_store._faiss_index:
            ntotal = self._llama_store._faiss_index.ntotal
            logger.info(f"search 前 FAISS 索引总量: {ntotal}, metadata: {len(self.metadata)}")
            if ntotal == 0:
                logger.error("FAISS 索引为空，无法检索")
                return []

        from llama_index.core.vector_stores.types import VectorStoreQuery
        import numpy as np

        query_vec = np.array(query_vector, dtype=np.float32)
        # 归一化 (用于余弦相似度)
        faiss.normalize_L2(query_vec.reshape(1, -1))

        query = VectorStoreQuery(
            query_embedding=query_vec.tolist(),
            similarity_top_k=min(top_k, len(self.metadata)),
        )
        result = self._llama_store.query(query)

        logger.info(f"LlamaIndex query 返回: nodes={result.nodes is not None}, "
                     f"similarities={result.similarities is not None}, "
                     f"ids={result.ids is not None}")

        results = []
        # LlamaIndex FaissVectorStore 只存储向量，不存储节点文本
        # result.nodes 可能为 None，需要用 result.ids 或 similarities 索引到 metadata
        similarities = result.similarities or []
        ids = result.ids or []

        # ids 是 FAISS 返回的索引，对应 metadata 中的位置
        for i, score in enumerate(similarities):
            if i < len(ids):
                idx = int(ids[i])
            else:
                idx = i
            if 0 <= idx < len(self.metadata):
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

        # 过滤保留的元数据
        keep_indices = [
            i for i, m in enumerate(self.metadata)
            if m.get("document_id") != document_id
        ]

        if len(keep_indices) == len(self.metadata):
            return  # 没有需要删除的

        # LlamaIndex FaissVectorStore 不支持精确删除单条，需要重建
        # 保存保留的向量和元数据
        keep_metadata = [self.metadata[i] for i in keep_indices]

        if not keep_metadata:
            # 全部删除
            self._llama_store = None
            self._storage_context = None
            self.metadata = []
            self._save()
            return

        # 获取所有向量
        import numpy as np
        if self._llama_store and self._llama_store._faiss_index:
            faiss_index = self._llama_store._faiss_index
            all_vectors = faiss.rev_swig_ptr(
                faiss_index.get_xb(), faiss_index.ntotal * self.dimension
            )
            all_vectors = np.array(all_vectors, dtype=np.float32).reshape(-1, self.dimension)
            keep_vectors = all_vectors[keep_indices]

            # 重建索引
            new_faiss_index = faiss.IndexFlatIP(self.dimension)
            new_faiss_index.add(keep_vectors)
            self._llama_store = FaissVectorStore(faiss_index=new_faiss_index)
            self._storage_context = StorageContext.from_defaults(
                vector_store=self._llama_store
            )

        self.metadata = keep_metadata
        self._save()
        logger.info(f"删除文档 {document_id} 的向量, 剩余 {len(self.metadata)} 条")

    def get_stats(self) -> dict:
        """获取索引统计信息"""
        return {
            "total_vectors": len(self.metadata),
            "dimension": self.dimension,
            "has_index": self._llama_store is not None,
        }
