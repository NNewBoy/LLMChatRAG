"""文档分块模块"""

import re
from config import settings
from utils.logger import logger


class DocumentChunker:
    """
    文档分块器
    - 按段落、句子优先切分
    - 支持重叠分块
    """

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.rag_chunk_size
        self.chunk_overlap = chunk_overlap or settings.rag_chunk_overlap

    def chunk(self, text: str, document_id: str = "", filename: str = "") -> list[dict]:
        """
        将长文档切分为小块
        返回: [{"text": "块内容", "index": 0, "metadata": {...}}, ...]
        """
        if not text.strip():
            return []

        # 按段落切分
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks = []
        current_chunk = ""
        chunk_index = 0

        for para in paragraphs:
            # 如果当前段落本身超过 chunk_size，按句子切分
            if len(para) > self.chunk_size:
                if current_chunk:
                    chunks.append(self._make_chunk(current_chunk, chunk_index, document_id, filename))
                    chunk_index += 1
                    current_chunk = ""

                sentences = re.split(r'(?<=[。！？.!?])\s*', para)
                for sent in sentences:
                    if not sent.strip():
                        continue
                    if len(current_chunk) + len(sent) <= self.chunk_size:
                        current_chunk += sent
                    else:
                        if current_chunk:
                            chunks.append(self._make_chunk(current_chunk, chunk_index, document_id, filename))
                            chunk_index += 1
                            # 保留重叠
                            overlap = current_chunk[-self.chunk_overlap:] if self.chunk_overlap > 0 else ""
                            current_chunk = overlap + sent
                        else:
                            # 单个句子就超过 chunk_size，强制切分
                            for i in range(0, len(sent), self.chunk_size):
                                piece = sent[i:i + self.chunk_size]
                                chunks.append(self._make_chunk(piece, chunk_index, document_id, filename))
                                chunk_index += 1
                            current_chunk = ""
            else:
                if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                    current_chunk = current_chunk + "\n\n" + para if current_chunk else para
                else:
                    if current_chunk:
                        chunks.append(self._make_chunk(current_chunk, chunk_index, document_id, filename))
                        chunk_index += 1
                        overlap = current_chunk[-self.chunk_overlap:] if self.chunk_overlap > 0 else ""
                        current_chunk = overlap + para if overlap else para
                    else:
                        current_chunk = para

        if current_chunk:
            chunks.append(self._make_chunk(current_chunk, chunk_index, document_id, filename))

        logger.info(f"文档分块完成: {len(chunks)} 个块")
        return chunks

    def _make_chunk(self, text: str, index: int, document_id: str, filename: str) -> dict:
        return {
            "text": text.strip(),
            "index": index,
            "metadata": {
                "document_id": document_id,
                "filename": filename,
                "chunk_index": index,
            }
        }
