"""RAG 完整流水线编排"""

import json
from datetime import datetime
from typing import AsyncGenerator
from rag.parser import DocumentParser
from rag.chunker import DocumentChunker
from rag.embedder import Embedder
from rag.vector_store import FAISSVectorStore
from rag.query_rewriter import QueryRewriter
from rag.retriever import HybridRetriever
from rag.reranker import Reranker
from rag.generator import Generator
from config import settings
from utils.logger import logger
from utils.sse import sse_event


class RAGPipeline:
    """RAG 完整流水线，编排解析→分块→向量化→检索→重排→生成"""

    def __init__(self, llm=None):
        self.parser = DocumentParser()
        self.chunker = DocumentChunker()
        self.embedder = Embedder()
        self.vector_store = FAISSVectorStore()
        self.query_rewriter = QueryRewriter(llm)
        self.retriever = HybridRetriever()
        self.reranker = Reranker(llm)
        self.generator = Generator(llm)

        # 索引已在 FAISSVectorStore.__init__ 中自动加载
        if self.vector_store.metadata:
            self.retriever.fit_bm25(self.vector_store.metadata)

    async def index_document(self, file_path: str, filename: str, document_id: str) -> int:
        """
        文档索引流程: 解析 → 分块 → 向量化 → 存储
        返回分块数量
        """
        logger.info(f"开始索引文档: {filename} (id: {document_id})")

        # 1. 解析文档
        file_type = self.parser.get_file_type(filename)
        text = self.parser.parse(file_path, file_type)

        # 2. 文档分块
        chunks = self.chunker.chunk(text)
        for chunk in chunks:
            chunk["document_id"] = document_id
            chunk["filename"] = filename

        # 3. 向量化
        texts = [c["text"] for c in chunks]
        vectors = await self.embedder.embed(texts)

        # 4. 存入 FAISS
        self.vector_store.add(vectors, chunks, document_id)

        # 5. 更新 BM25 索引
        self.retriever.fit_bm25(self.vector_store.metadata)

        logger.info(f"文档索引完成: {filename}, 分块数: {len(chunks)}")
        return len(chunks)

    def remove_document(self, document_id: str):
        """删除文档的所有向量数据"""
        self.vector_store.remove(document_id)
        self.retriever.fit_bm25(self.vector_store.metadata)
        logger.info(f"已删除文档向量数据: {document_id}")

    async def run_stream(
        self,
        query: str,
        embedding_model: str = None,
        enable_query_rewriting: bool = None,
        enable_hybrid_search: bool = None,
        enable_reranking: bool = None,
        bad_case_examples: list[dict] = None,
    ) -> AsyncGenerator[str, None]:
        """
        RAG 对话流水线 (流式输出 SSE 事件)
        返回 SSE 事件字符串的异步生成器
        """
        # 使用默认值
        if enable_query_rewriting is None:
            enable_query_rewriting = settings.enable_query_rewriting
        if enable_hybrid_search is None:
            enable_hybrid_search = settings.enable_hybrid_search
        if enable_reranking is None:
            enable_reranking = settings.enable_reranking

        logger.info(
            f"RAG 流水线启动: query='{query}', "
            f"query_rewriting={enable_query_rewriting}, "
            f"hybrid={enable_hybrid_search}, reranking={enable_reranking}"
        )

        # 1. Query 改写 (可选)
        search_query = query
        if enable_query_rewriting:
            yield sse_event("thinking", {"content": "正在改写查询以提高检索召回率..."})
            try:
                search_query = await self.query_rewriter.rewrite(query)
                yield sse_event("thinking", {"content": f"改写后的查询: {search_query}"})
            except Exception as e:
                logger.warning(f"Query 改写失败，使用原始查询: {e}")
                search_query = query

        # 2. 检索
        yield sse_event("thinking", {"content": "正在检索相关文档..."})
        yield sse_event("tool_call", {
            "tool_name": "rag_search",
            "tool_input": {"query": search_query, "hybrid": enable_hybrid_search},
            "timestamp": datetime.now().isoformat(),
        })

        results = await self.retriever.retrieve(
            search_query,
            top_k=settings.rag_top_k,
            enable_hybrid=enable_hybrid_search,
            embedding_model=embedding_model,
        )

        tool_output = f"找到 {len(results)} 条相关文档"
        if results:
            sources = [r.get("filename", "未知") for r in results[:3]]
            tool_output += f"，来源: {', '.join(sources)}"

        yield sse_event("tool_result", {
            "tool_name": "rag_search",
            "tool_output": tool_output,
            "timestamp": datetime.now().isoformat(),
        })

        if not results:
            yield sse_event("token", {"content": "未找到相关文档。请先上传文档后再进行提问。"})
            yield sse_event("done", {"full_content": "未找到相关文档。请先上传文档后再进行提问。"})
            return

        # 3. 重排序 (可选)
        if enable_reranking:
            yield sse_event("thinking", {"content": "正在对检索结果进行重排序..."})
            try:
                results = await self.reranker.rerank(
                    search_query, results,
                    top_n=settings.rag_top_n,
                    enable_reranking=True,
                )
            except Exception as e:
                logger.warning(f"重排序失败，使用原始排序: {e}")
                results = results[:settings.rag_top_n]
        else:
            results = results[:settings.rag_top_n]

        yield sse_event("thinking", {"content": f"已选出 {len(results)} 条最相关文档，正在生成回答..."})

        # 4. 构建 Prompt
        prompt = self.generator.build_prompt(query, results, bad_case_examples or [])

        # 5. 答案生成 (流式)
        async for token in self.generator.generate_stream(prompt):
            yield sse_event("token", {"content": token})

        # 6. 附带引用来源
        sources = []
        for r in results:
            sources.append({
                "filename": r.get("filename", ""),
                "text": r.get("text", "")[:200],
                "score": r.get("score", 0),
            })
        yield sse_event("tool_result", {
            "tool_name": "rag_sources",
            "tool_output": json.dumps(sources, ensure_ascii=False),
            "timestamp": datetime.now().isoformat(),
        })

        logger.info("RAG 流水线完成")

    async def search_only(self, query: str, top_k: int = 5) -> list[dict]:
        """仅执行检索，不生成答案 (供 Agent 工具调用)"""
        results = await self.retriever.retrieve(query, top_k=top_k)
        return results
