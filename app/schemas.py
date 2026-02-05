"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional


class StoryRequest(BaseModel):
    """Story generation request model"""
    age: int = Field(..., ge=3, le=15, description="Child's age (3-15 years)")
    reading_level: Optional[int] = Field(None, description="Lexile level")
    preferences: list[str] = Field(default_factory=list, description="List of preferred topics")
    learning_goal: Optional[str] = Field(None, description="Learning goal")
    use_rag: bool = Field(True, description="Whether to use RAG (hallucination prevention)")


class KnowledgeAddRequest(BaseModel):
    """RAG knowledge base document addition request"""
    documents: list[str] = Field(..., description="List of document contents")
    sources: list[str] = Field(..., description="List of sources")


class StoryResponse(BaseModel):
    """Story generation response model"""
    story: str = Field(..., description="Generated story")
    sources: list[str] = Field(default_factory=list, description="Reference sources (RAG)")
    fact_checked: bool = Field(False, description="Whether fact-checked")
    confidence_score: float = Field(1.0, ge=0, le=1, description="Confidence score")
    rag_context: list[str] = Field(default_factory=list, description="Retrieved knowledge context")


class RAGDocument(BaseModel):
    """RAG document model"""
    content: str = Field(..., description="Document content")
    source: str = Field(..., description="Source")
    metadata: dict = Field(default_factory=dict, description="Metadata")


class ReadingDiagnosticRequest(BaseModel):
    """Reading level diagnostic request"""
    user_id: str
    reading_sample: str
    use_rag: bool = Field(True, description="Whether to use RAG for analysis")


class ReadingDiagnosticResponse(BaseModel):
    """Reading level diagnostic response"""
    user_id: str
    lexile_level: int
    assessment_details: dict
    rag_recommendations: list[str] = Field(default_factory=list, description="RAG-based improvement recommendations")


class BookRecommendationRequest(BaseModel):
    """Book recommendation request"""
    user_id: str
    reading_level: int
    preferences: list[str] = Field(default_factory=list)
    use_rag: bool = Field(True, description="Whether to use RAG for recommendations")


class BookRecommendation(BaseModel):
    """Book recommendation item"""
    title: str
    author: str
    lexile_level: int
    description: str


class BookRecommendationResponse(BaseModel):
    """Book recommendation response"""
    recommendations: list[BookRecommendation]
    rag_sources: list[str] = Field(default_factory=list, description="RAG knowledge sources used")


class RAGStatsResponse(BaseModel):
    """RAG system statistics response"""
    total_documents: int = Field(..., description="Total documents in knowledge base")
    categories: list[str] = Field(default_factory=list, description="Available knowledge categories")
    recent_queries: int = Field(0, description="Number of recent queries")
