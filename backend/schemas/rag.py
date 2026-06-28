"""RAG 请求/响应模型"""

from pydantic import BaseModel, Field
from typing import Optional


class RAGMessageRequest(BaseModel):
    content: str
    model: str
    parent_message_id: Optional[str] = None
    embedding_model: str = "BAAI/bge-large-zh-v1.5"
    enable_query_rewriting: bool = True
    enable_hybrid_search: bool = False
    enable_reranking: bool = False


class RAGRegenerateRequest(BaseModel):
    model: str
    embedding_model: str = "BAAI/bge-large-zh-v1.5"
    enable_query_rewriting: bool = True
    enable_hybrid_search: bool = False
    enable_reranking: bool = False


class FeedbackRequest(BaseModel):
    is_correct: bool


class FeedbackResponse(BaseModel):
    status: str
    message_id: str
    is_correct: bool


class BadCaseResponse(BaseModel):
    id: str
    message_id: str
    question: str
    wrong_answer: str
    correct_answer: str
    use_as_example: bool
    created_at: str
    updated_at: Optional[str] = None


class BadCaseListResponse(BaseModel):
    bad_cases: list[BadCaseResponse]


class BadCaseUpdateRequest(BaseModel):
    correct_answer: str
    use_as_example: bool = False


class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    multimodal: bool = False


class ModelListResponse(BaseModel):
    models: list[ModelInfo]


class EmbeddingModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    dimension: int


class EmbeddingModelListResponse(BaseModel):
    models: list[EmbeddingModelInfo]
