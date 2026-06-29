"""模型列表接口"""

from fastapi import APIRouter
from config import settings

router = APIRouter(prefix="/api", tags=["models"])

# 可用 LLM 模型列表 (含多模态标记)
AVAILABLE_LLM_MODELS = [
    {"id": "deepseek-v4-flash", "name": "Deepseek V4 Flash", "provider": "openai", "multimodal": False},
    {"id": "glm-5.2", "name": "GLM-5.2", "provider": "openai", "multimodal": False},
    {"id": "doubao-seed-2.0-pro", "name": "Doubao-Seed-2.0-pro", "provider": "openai", "multimodal": True},
    {"id": "doubao-seed-2.0-lite", "name": "Doubao-Seed-2.0-lite", "provider": "openai", "multimodal": True},
    {"id": "kimi-k2.6", "name": "Kimi K2.6", "provider": "openai", "multimodal": True}
]

# 可用 Embedding 模型列表
AVAILABLE_EMBEDDING_MODELS = [
    {"id": "BAAI/bge-m3", "name": "BGE M3", "provider": "siliconflow", "dimension": 1024},
    {"id": "Qwen/Qwen3-Embedding-8B", "name": "Qwen3-Embedding-8B", "provider": "siliconflow", "dimension": 1024},
]


@router.get("/models")
async def get_models():
    """获取可用 LLM 模型列表"""
    return {"models": AVAILABLE_LLM_MODELS}


@router.get("/embedding-models")
async def get_embedding_models():
    """获取可用 Embedding 模型列表"""
    return {"models": AVAILABLE_EMBEDDING_MODELS}
