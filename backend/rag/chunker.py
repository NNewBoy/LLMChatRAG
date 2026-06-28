"""文档分块模块 - 使用 LlamaIndex SentenceSplitter"""

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode
from config import settings
from utils.logger import logger


class DocumentChunker:
    """
    文档分块器，基于 LlamaIndex SentenceSplitter
    - 按句子优先切分，支持重叠
    - 保留来源元数据以便回溯
    """

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.rag_chunk_size
        self.chunk_overlap = chunk_overlap or settings.rag_chunk_overlap
        self._splitter = SentenceSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

    def chunk(self, text: str, document_id: str = "", filename: str = "") -> list[dict]:
        """
        将长文档切分为小块
        返回: [{"text": "块内容", "index": 0, "metadata": {...}}, ...]
        """
        if not text.strip():
            return []

        # 使用 LlamaIndex SentenceSplitter 切分
        nodes = self._splitter.split_text(text)

        chunks = []
        for i, node_text in enumerate(nodes):
            chunks.append({
                "text": node_text.strip(),
                "index": i,
                "metadata": {
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_index": i,
                }
            })

        logger.info(f"文档分块完成 (LlamaIndex SentenceSplitter): {len(chunks)} 个块")
        return chunks

    def chunk_to_nodes(self, text: str, document_id: str = "", filename: str = "") -> list[TextNode]:
        """
        将文本切分为 LlamaIndex TextNode 列表
        用于直接传入 LlamaIndex 索引
        """
        if not text.strip():
            return []

        nodes = self._splitter.split_text(text)
        text_nodes = []
        for i, node_text in enumerate(nodes):
            text_nodes.append(TextNode(
                text=node_text.strip(),
                metadata={
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_index": i,
                }
            ))
        logger.info(f"文档分块为 TextNode: {len(text_nodes)} 个节点")
        return text_nodes
