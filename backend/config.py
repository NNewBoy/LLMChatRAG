"""环境变量配置加载模块"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置，从环境变量或 .env 文件加载"""

    # 服务器
    host: str = "0.0.0.0"
    port: int = 8000

    # LLM
    llm_model: str = "deepseek-chat"
    llm_api_key: str = ""
    llm_api_base_url: str = "https://api.deepseek.com/v1"

    # SQLite
    sqlite_db_path: str = "./data/sqlite/chatrag.db"
    bad_case_db_path: str = ""  # 为空则使用 sqlite_db_path

    # Embedding
    embedding_model: str = "BAAI/bge-large-zh-v1.5"
    embedding_api_key: str = ""
    embedding_api_base_url: str = "https://api.siliconflow.cn/v1"
    embedding_provider: str = "siliconflow"  # "llama_index" 或 "siliconflow"

    # FAISS
    faiss_db_path: str = "./data/faiss/"

    # RAG 开关 (默认值，前端可运行时覆盖)
    enable_query_rewriting: bool = True
    enable_hybrid_search: bool = False
    enable_reranking: bool = False

    # 混合检索
    hybrid_alpha: float = 0.7
    hybrid_beta: float = 0.3

    # RAG 参数
    rag_top_k: int = 10
    rag_top_n: int = 5
    rag_chunk_size: int = 512
    rag_chunk_overlap: int = 50

    # 联网搜索
    search_api_key: str = ""
    search_api_url: str = ""
    # MCP npx 可执行文件路径（为空时自动探测；systemd 环境找不到 npx 时可手动指定）
    npx_path: str = ""

    # 日志
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    def get_bad_case_db_path(self) -> str:
        """获取错题集数据库路径，为空则使用主库"""
        return self.bad_case_db_path if self.bad_case_db_path else self.sqlite_db_path

    def ensure_dirs(self):
        """确保所需目录存在"""
        paths = [
            Path(self.sqlite_db_path).parent,
            Path(self.faiss_db_path),
            Path(self.log_file).parent,
            Path("./data/uploads"),
        ]
        for p in paths:
            p.mkdir(parents=True, exist_ok=True)


settings = Settings()
