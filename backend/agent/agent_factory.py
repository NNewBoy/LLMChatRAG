"""Agent 工厂 - 创建 DeepAgents 实例"""

import os
import shutil
from typing import Optional
from config import settings
from utils.logger import logger
from utils.timezone import now_iso, now_str
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

            # 跨平台兼容: Windows 需通过 cmd /c 启动 npx，Linux/macOS 直接调用 npx
            # Systemd 服务 PATH 通常仅含 venv，需解析 npx 绝对路径
            if os.name == "nt":
                command, args = "cmd", ["/c", "npx", "-y", "bing-cn-mcp"]
            else:
                # 优先使用 .env 中显式配置的 NPX_PATH
                npx_path = settings.npx_path or shutil.which("npx") or "/usr/bin/npx"
                command, args = npx_path, ["-y", "bing-cn-mcp"]

                # systemd 环境 PATH 可能不含 node 和系统工具目录
                # 1. 把 npx 所在目录加入 PATH，让子进程能找到 node
                # 2. 确保 /usr/bin、/bin 等系统目录在 PATH 中，npx 内部 spawn sh 需要
                current_path = os.environ.get("PATH", "")
                needed_dirs = [os.path.dirname(npx_path), "/usr/local/bin", "/usr/bin", "/bin"]
                for d in needed_dirs:
                    if d and d not in current_path:
                        current_path = d + os.pathsep + current_path
                os.environ["PATH"] = current_path
                logger.info(f"MCP PATH: {os.environ['PATH']}")
                logger.info(f"npx path: {npx_path}")

            client = MultiServerMCPClient(
                {
                    "bing-search": {
                        "transport": "stdio",
                        "command": command,
                        "args": args,
                    }
                }
            )
            cls._mcp_tools = await client.get_tools()
            logger.info(f"MCP 工具加载成功: {[t.name for t in cls._mcp_tools]}")
        except Exception as e:
            logger.error(
                f"MCP 工具加载失败: {e} | "
                f"npx_path={settings.npx_path or '(未配置)'} | "
                f"PATH={os.environ.get('PATH', '(空)')}"
            )
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
    async def create_deep_agent_stream(
        cls,
        llm,
        messages: list,
        enable_rag: bool = True,
    ):
        """
        使用 DeepAgents 创建 Agent 并流式执行，返回 (event_type, data) 异步生成器。
        DeepAgents 内部自动处理工具调用循环（规划、子代理、文件系统），无需手动管理。

        Yields:
            ("token", str)          - 文本 token
            ("thinking", str)       - 思考过程
            ("tool_call", dict)     - 工具调用
            ("tool_result", dict)   - 工具结果
        """
        from deepagents import create_deep_agent
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage

        # 加载技能
        skills_loader = SkillsLoader()
        skills = skills_loader.load_all()

        # 准备工具列表
        tools = []
        if enable_rag and cls._rag_pipeline:
            rag_tool = create_rag_tool(cls._rag_pipeline)
            tools.append(rag_tool)
            logger.info("RAG 工具已加载 (DeepAgents)")

        # 加载 MCP 工具
        mcp_tools = await cls.get_mcp_tools()
        tools.extend(mcp_tools)

        # 构建系统提示
        system_prompt = cls._build_system_prompt(skills, enable_rag)

        # 创建 DeepAgents Agent
        agent = create_deep_agent(
            model=llm,
            tools=tools,
            system_prompt=system_prompt,
        )
        logger.info(f"DeepAgents Agent 创建成功, 工具数: {len(tools)}")

        # 确保消息列表以 system 开头
        graph_messages = list(messages)

        # 流式执行 (stream_mode="messages" 返回 (message_chunk, metadata))
        async for event in agent.astream(
            {"messages": graph_messages},
            stream_mode="messages",
        ):
            msg_chunk, metadata = event

            # 获取消息类型
            msg_type = msg_chunk.__class__.__name__

            # 处理文本 token
            if hasattr(msg_chunk, "content") and msg_chunk.content:
                if isinstance(msg_chunk.content, str) and msg_chunk.content:
                    yield ("token", msg_chunk.content)

            # 处理工具调用
            if hasattr(msg_chunk, "tool_call_chunks") and msg_chunk.tool_call_chunks:
                for tc_chunk in msg_chunk.tool_call_chunks:
                    if tc_chunk.get("name"):
                        yield ("thinking", f"正在调用工具: {tc_chunk['name']}...")
                        yield ("tool_call", {
                            "tool_name": tc_chunk["name"],
                            "tool_input": {},
                            "timestamp": now_iso(),
                        })

            # ToolMessage 返回工具结果
            if isinstance(msg_chunk, ToolMessage):
                content = msg_chunk.content
                if isinstance(content, str):
                    yield ("tool_result", {
                        "tool_name": getattr(msg_chunk, "name", "tool"),
                        "tool_output": content[:500],
                        "timestamp": now_iso(),
                    })

    @classmethod
    def _build_system_prompt(cls, skills: list[str], enable_rag: bool) -> str:
        """构建系统提示词，包含技能描述"""
        today = now_str()
        prompt = f"你是一个智能对话助手。请友好、准确地回答用户的问题。\n\n当前日期：{today}。当用户询问实时信息（如今日油价、天气、新闻等）时，请使用当前日期进行搜索，不要使用过时的日期。\n\n"

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
