"""Agent 工厂 - 创建 DeepAgents 实例"""

import os
from typing import Optional
from config import settings
from utils.logger import logger
from agent.skills_loader import SkillsLoader
from agent.tools import create_rag_tool
from agent.memory import LongTermMemory


class AgentFactory:
    """Agent 工厂，负责创建和配置 DeepAgents 实例"""

    _llm = None
    _rag_pipeline = None
    _mcp_tools = None

    @classmethod
    def set_rag_pipeline(cls, rag_pipeline):
        """注入 RAG pipeline 实例"""
        cls._rag_pipeline = rag_pipeline
        logger.info("RAG pipeline 已注入 AgentFactory")

    @classmethod
    async def get_mcp_tools(cls):
        """
        通过 MCP 加载 Bing 联网搜索工具
        使用 langchain-mcp-adapters 连接 bing-cn-mcp 子进程
        """
        if cls._mcp_tools is not None:
            return cls._mcp_tools

        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient

            client = MultiServerMCPClient(
                {
                    "bing-search": {
                        "transport": "stdio",
                        "command": "cmd",
                        "args": ["/c", "npx", "-y", "bing-cn-mcp"],
                    }
                }
            )
            cls._mcp_tools = await client.get_tools()
            logger.info(f"MCP 工具加载成功: {[t.name for t in cls._mcp_tools]}")
        except Exception as e:
            logger.error(f"MCP 工具加载失败: {e}")
            cls._mcp_tools = []
        return cls._mcp_tools

    @classmethod
    async def get_llm(cls, model: str = None):
        """
        通过 LangChain init_chat_model 创建 LLM 实例
        支持多模态模型
        """
        model_name = model or settings.llm_model

        # 缓存已创建的 LLM 实例 (按模型名)
        cache_key = f"_llm_{model_name}"
        if hasattr(cls, cache_key) and getattr(cls, cache_key) is not None:
            return getattr(cls, cache_key)

        try:
            from langchain.chat_models import init_chat_model

            llm = init_chat_model(
                model=model_name,
                model_provider="openai",
                api_key=settings.llm_api_key,
                base_url=settings.llm_api_base_url,
                temperature=0.7,
            )
            setattr(cls, cache_key, llm)
            logger.info(f"LLM 实例创建成功: {model_name}")
            return llm
        except Exception as e:
            logger.error(f"LLM 创建失败: {e}")
            raise

    @classmethod
    async def create_agent(cls, llm, enable_rag: bool = True):
        """
        创建 DeepAgents Agent 实例

        Args:
            llm: LangChain LLM 实例
            enable_rag: 是否加载 RAG 工具

        Returns:
            DeepAgents Agent 实例
        """
        logger.info(f"创建 Agent: enable_rag={enable_rag}")

        # 加载技能
        skills_loader = SkillsLoader()
        skills = skills_loader.load_all()

        # 准备工具列表
        tools = []

        if enable_rag and cls._rag_pipeline:
            rag_tool = create_rag_tool(cls._rag_pipeline)
            tools.append(rag_tool)
            logger.info("RAG 工具已加载")

        # 加载 MCP 工具（联网搜索等）
        mcp_tools = await cls.get_mcp_tools()
        tools.extend(mcp_tools)

        # 构建系统提示
        system_prompt = cls._build_system_prompt(skills, enable_rag)

        try:
            # 尝试使用 DeepAgents 框架创建 Agent
            from deepagents import create_deep_agent

            agent = create_deep_agent(
                model=llm,
                tools=tools,
                system_prompt=system_prompt,
            )
            logger.info("DeepAgents Agent 创建成功")
            return agent
        except ImportError:
            # DeepAgents 不可用时，回退到 LangChain Agent
            logger.warning("DeepAgents 不可用，回退到 LangChain AgentExecutor")
            return cls._create_langchain_agent(llm, tools, system_prompt)
        except Exception as e:
            logger.error(f"Agent 创建失败: {e}")
            # 回退到简单模式
            return cls._create_langchain_agent(llm, tools, system_prompt)

    @classmethod
    def _create_langchain_agent(cls, llm, tools, system_prompt):
        """回退方案：使用 LangChain create_react_agent"""
        try:
            from langchain.agents import create_react_agent, AgentExecutor
            from langchain_core.prompts import ChatPromptTemplate

            tool_names = ", ".join([getattr(t, "__name__", str(t)) for t in tools])

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ])

            if tools:
                agent = create_react_agent(llm, tools, prompt)
                agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
                logger.info("LangChain AgentExecutor 创建成功")
                return agent_executor
            else:
                logger.info("无工具，返回原始 LLM")
                return llm
        except Exception as e:
            logger.error(f"LangChain Agent 创建也失败: {e}")
            return llm

    @classmethod
    def _build_system_prompt(cls, skills: list[str], enable_rag: bool) -> str:
        """构建系统提示词，包含技能描述"""
        prompt = "你是一个智能对话助手。请友好、准确地回答用户的问题。\n\n"

        if skills:
            prompt += "## 可用技能\n\n"
            for skill in skills:
                prompt += f"{skill}\n\n"

        if enable_rag:
            prompt += (
                "## 重要说明\n"
                "- 当用户问题涉及知识库文档内容时，请使用 rag_search 工具检索相关文档。\n"
                "- 对于普通问题（闲聊、编程、常识等），直接回答即可。\n"
                "- 检索到文档后，基于文档内容给出准确回答。\n\n"
            )

        prompt += "请用中文回答，回答要简洁清晰。"
        return prompt

    @classmethod
    def get_memory(cls) -> LongTermMemory:
        """获取长期记忆管理器"""
        return LongTermMemory()
