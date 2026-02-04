"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional


class StoryRequest(BaseModel):
    """스토리 생성 요청 모델"""
    age: int = Field(..., ge=3, le=15, description="아이의 나이 (3-15세)")
    reading_level: Optional[int] = Field(None, description="Lexile 수준")
    preferences: list[str] = Field(default_factory=list, description="선호 주제 목록")
    learning_goal: Optional[str] = Field(None, description="학습 목표")
    use_rag: bool = Field(True, description="RAG 사용 여부 (할루시네이션 방지)")


class StoryResponse(BaseModel):
    """스토리 생성 응답 모델"""
    story: str = Field(..., description="생성된 스토리")
    sources: list[str] = Field(default_factory=list, description="참조된 출처 (RAG)")
    fact_checked: bool = Field(False, description="팩트 체크 여부")
    confidence_score: float = Field(1.0, ge=0, le=1, description="신뢰도 점수")


class RAGDocument(BaseModel):
    """RAG 문서 모델"""
    content: str = Field(..., description="문서 내용")
    source: str = Field(..., description="출처")
    metadata: dict = Field(default_factory=dict, description="메타데이터")


class ReadingDiagnosticRequest(BaseModel):
    """읽기 수준 진단 요청"""
    user_id: str
    reading_sample: str


class ReadingDiagnosticResponse(BaseModel):
    """읽기 수준 진단 응답"""
    user_id: str
    lexile_level: int
    assessment_details: dict


class BookRecommendationRequest(BaseModel):
    """책 추천 요청"""
    user_id: str
    reading_level: int
    preferences: list[str] = Field(default_factory=list)


class BookRecommendation(BaseModel):
    """책 추천 항목"""
    title: str
    author: str
    lexile_level: int
    description: str


class BookRecommendationResponse(BaseModel):
    """책 추천 응답"""
    recommendations: list[BookRecommendation]
