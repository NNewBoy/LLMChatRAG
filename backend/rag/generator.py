"""答案生成模块 - Prompt 构建 + 答案生成"""

import json
from typing import AsyncGenerator
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from utils.logger import logger


class Generator:
    """Prompt 构建 + 答案生成"""

    def __init__(self, llm=None):
        self.llm = llm

    SYSTEM_PROMPT = "你是一个专业的问答助手。请基于以下文档内容回答问题。"

    def build_prompt(
        self,
        query: str,
        context_chunks: list[dict],
        bad_case_examples: list[dict] = None,
    ) -> list:
        """
        构建消息列表，包含系统指令、错题范例、检索到的文档上下文、用户问题
        """
        messages = [SystemMessage(content=self.SYSTEM_PROMPT)]

        context_text = ""
        if bad_case_examples:
            context_text += "## 以下是以往的问答范例，请参考正确答案的风格和准确度：\n\n"
            for bc in bad_case_examples:
                context_text += f"问题: {bc.get('question', '')}\n"
                context_text += f"正确答案: {bc.get('correct_answer', '')}\n\n"

        context_text += "## 参考文档：\n\n"
        for i, chunk in enumerate(context_chunks):
            text = chunk.get("text", "")
            source = chunk.get("filename", chunk.get("metadata", {}).get("filename", "未知来源"))
            context_text += f"[{i + 1}] (来源: {source})\n{text}\n\n"

        context_text += f"## 用户问题：{query}\n\n"
        context_text += "请基于以上文档内容回答，如果文档中没有相关信息，请明确说明。请引用对应的文档编号。"

        messages.append(HumanMessage(content=context_text))

        # 打印最终 RAG Prompt
        logger.info(f"RAG 最终 Prompt 构建 ({len(messages)} 条消息):")
        logger.info(f"  System: {self.SYSTEM_PROMPT}")
        logger.info(f"  参考文档数: {len(context_chunks)}, 错题范例数: {len(bad_case_examples or [])}")
        logger.info(f"  Human (前1000字): {context_text[:1000]}{'...' if len(context_text) > 1000 else ''}")

        return messages

    async def generate_stream(self, messages: list, llm: BaseChatModel = None) -> AsyncGenerator[str, None]:
        """流式生成答案，逐 token 返回"""
        use_llm = llm or self.llm
        if not use_llm:
            raise ValueError("未提供 LLM 实例")
        logger.info("开始流式生成答案")
        try:
            async for chunk in use_llm.astream(messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"流式生成失败: {e}")
            raise

    async def generate(self, messages: list, llm: BaseChatModel = None) -> str:
        """非流式生成完整答案"""
        use_llm = llm or self.llm
        if not use_llm:
            raise ValueError("未提供 LLM 实例")
        logger.info("开始生成答案")
        try:
            response = await use_llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"生成失败: {e}")
            raise
