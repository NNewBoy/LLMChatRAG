"""文档请求/响应模型"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    created_at: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]


class DocumentStatusResponse(BaseModel):
    document: dict


class BadCaseResponse(BaseModel):
    id: str
    message_id: str
    question: str
    wrong_answer: str
    correct_answer: str
    use_as_example: bool
    created_at: str


class BadCaseListResponse(BaseModel):
    bad_cases: list[BadCaseResponse]


class BadCaseUpdateRequest(BaseModel):
    correct_answer: str
    use_as_example: bool


class BadCaseUpdateResponse(BaseModel):
    bad_case: dict


class FeedbackRequest(BaseModel):
    is_correct: bool


class FeedbackResponse(BaseModel):
    status: str
    message_id: str
    is_correct: bool
