"""
Story Generation Engine
스토리 생성 엔진 - RAG 통합
"""

import os
from typing import Optional

from .schemas import StoryRequest, StoryResponse
from .rag import get_rag_system, RAGSystem
from .safety import ContentFilter

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class StoryEngine:
    """스토리 생성 엔진"""
    
    def __init__(self, rag_system: Optional[RAGSystem] = None):
        """
        스토리 엔진 초기화
        
        Args:
            rag_system: RAG 시스템 인스턴스 (None이면 기본 인스턴스 사용)
        """
        self.rag_system = rag_system or get_rag_system()
        self._openai_client = None
    
    @property
    def openai_client(self):
        """OpenAI 클라이언트 (지연 초기화)"""
        if self._openai_client is None:
            if not OPENAI_AVAILABLE:
                raise ImportError(
                    "openai 패키지가 설치되지 않았습니다."
                )
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
            self._openai_client = OpenAI(api_key=api_key)
        return self._openai_client
    
    def generate_story(self, request: StoryRequest) -> StoryResponse:
        """
        스토리 생성
        
        Args:
            request: 스토리 생성 요청
        
        Returns:
            생성된 스토리 응답
        """
        # 요청 검증
        query = " ".join(request.preferences) if request.preferences else "재미있는 모험"
        
        # 안전성 사전 검사
        is_safe, issue = ContentFilter.is_safe(query)
        if not is_safe:
            return StoryResponse(
                story=f"죄송합니다. 요청하신 주제는 처리할 수 없습니다. ({issue})",
                sources=[],
                fact_checked=False,
                confidence_score=0.0
            )
        
        if request.use_rag:
            # RAG를 사용한 할루시네이션 방지 스토리 생성
            return self._generate_with_rag(request, query)
        else:
            # 기본 LLM 스토리 생성 (RAG 없음)
            return self._generate_basic(request, query)
    
    def _generate_with_rag(
        self, 
        request: StoryRequest, 
        query: str
    ) -> StoryResponse:
        """RAG를 사용한 스토리 생성"""
        # 관련 문서 검색
        retrieved_docs = self.rag_system.retrieve(
            query=query,
            n_results=3
        )
        
        # 컨텍스트 기반 스토리 생성
        result = self.rag_system.generate_with_context(
            query=query,
            retrieved_docs=retrieved_docs,
            age=request.age,
            preferences=request.preferences,
            learning_goal=request.learning_goal
        )
        
        # 생성된 스토리 안전성 검사 및 정화
        story = result["story"]
        is_safe, _ = ContentFilter.is_safe(story)
        if not is_safe:
            story = ContentFilter.sanitize(story)
        
        return StoryResponse(
            story=story,
            sources=result["sources"],
            fact_checked=result["fact_checked"],
            confidence_score=result["confidence_score"]
        )
    
    def _generate_basic(
        self, 
        request: StoryRequest, 
        query: str
    ) -> StoryResponse:
        """기본 LLM 스토리 생성 (RAG 없음) - 할루시네이션 위험 있음"""
        system_prompt = f"""당신은 {request.age}세 아이를 위한 동화 작가입니다.
아이의 나이에 맞는 어휘와 문장 길이를 사용하세요.
폭력적이거나 무서운 내용은 피하고, 긍정적인 메시지를 담아주세요."""

        user_prompt = f"""주제: {query}
학습 목표: {request.learning_goal or '재미있고 교훈적인 이야기'}

위 주제로 짧은 동화를 만들어주세요."""

        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=1000
        )
        
        story = response.choices[0].message.content
        
        # 안전성 검사 및 정화
        is_safe, _ = ContentFilter.is_safe(story)
        if not is_safe:
            story = ContentFilter.sanitize(story)
        
        return StoryResponse(
            story=story,
            sources=[],
            fact_checked=False,  # RAG 없이는 팩트 체크 안됨
            confidence_score=0.5  # RAG 없이는 신뢰도 낮음
        )


# 전역 엔진 인스턴스
_engine_instance: Optional[StoryEngine] = None


def get_story_engine() -> StoryEngine:
    """스토리 엔진 싱글톤 인스턴스 반환"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = StoryEngine()
    return _engine_instance
