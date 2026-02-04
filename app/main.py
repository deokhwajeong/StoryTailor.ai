"""
StoryTailor.ai FastAPI Main Entry Point
RAG 기반 할루시네이션 방지 기능이 포함된 아동용 스토리 생성 API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    StoryRequest, 
    StoryResponse,
    ReadingDiagnosticRequest,
    ReadingDiagnosticResponse,
    BookRecommendationRequest,
    BookRecommendationResponse,
    BookRecommendation
)
from .story_engine import get_story_engine
from .rag import get_rag_system
from .safety import ContentFilter

app = FastAPI(
    title="StoryTailor.ai API",
    description="""
    아동을 위한 AI 동화 생성 플랫폼 API
    
    ## 주요 기능
    - **스토리 생성**: RAG 기반 할루시네이션 방지 스토리 생성
    - **읽기 수준 진단**: Lexile 수준 측정
    - **도서 추천**: 맞춤형 도서 추천
    
    ## RAG (Retrieval Augmented Generation)
    LLM의 할루시네이션을 방지하기 위해 검색 기반 생성 시스템을 사용합니다:
    1. 지식 베이스에서 관련 정보 검색
    2. 검색된 정보를 컨텍스트로 LLM에 제공
    3. 사실에 기반한 스토리 생성
    4. 출처 추적으로 검증 가능
    """,
    version="1.0.0"
)

# CORS 설정 (프론트엔드 연동용)
# 프로덕션 환경에서는 ALLOWED_ORIGINS 환경 변수로 특정 도메인만 허용하세요
# 예: export ALLOWED_ORIGINS="https://storytailor.ai,https://www.storytailor.ai"
import os
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """API 루트 엔드포인트"""
    return {
        "message": "StoryTailor.ai API에 오신 것을 환영합니다!",
        "docs": "/docs",
        "features": [
            "RAG 기반 할루시네이션 방지 스토리 생성",
            "아동 안전 콘텐츠 필터링",
            "읽기 수준 진단",
            "맞춤형 도서 추천"
        ]
    }


@app.post("/generate_story", response_model=StoryResponse)
async def generate_story(request: StoryRequest):
    """
    스토리 생성 API
    
    RAG(Retrieval Augmented Generation)를 사용하여 할루시네이션을 방지하고
    사실에 기반한 아동용 동화를 생성합니다.
    
    Args:
        request: 스토리 생성 요청 (나이, 선호도, 학습 목표 등)
    
    Returns:
        생성된 스토리, 참조 출처, 신뢰도 점수 포함
    """
    try:
        engine = get_story_engine()
        response = engine.generate_story(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ImportError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"스토리 생성 중 오류 발생: {str(e)}")


@app.post("/diagnose_reading_level", response_model=ReadingDiagnosticResponse)
async def diagnose_reading_level(request: ReadingDiagnosticRequest):
    """
    읽기 수준 진단 API
    
    아이의 읽기 샘플을 분석하여 Lexile 수준을 측정합니다.
    """
    # 간단한 휴리스틱 기반 진단 (실제 구현에서는 ML 모델 사용)
    sample = request.reading_sample
    word_count = len(sample.split())
    sentence_count = len([s for s in sample.split('.') if s.strip()])
    
    if sentence_count == 0:
        sentence_count = 1
    
    avg_words_per_sentence = word_count / sentence_count
    
    # Lexile 수준 추정 (간단한 공식)
    estimated_lexile = int(100 + avg_words_per_sentence * 20)
    estimated_lexile = max(100, min(1500, estimated_lexile))
    
    return ReadingDiagnosticResponse(
        user_id=request.user_id,
        lexile_level=estimated_lexile,
        assessment_details={
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_words_per_sentence": round(avg_words_per_sentence, 1),
            "method": "heuristic"
        }
    )


@app.post("/recommend_books", response_model=BookRecommendationResponse)
async def recommend_books(request: BookRecommendationRequest):
    """
    도서 추천 API
    
    읽기 수준과 선호도에 맞는 도서를 추천합니다.
    """
    # 샘플 추천 (실제 구현에서는 DB 또는 외부 API 연동)
    sample_books = [
        BookRecommendation(
            title="용감한 토끼의 모험",
            author="김동화",
            lexile_level=400,
            description="숲 속에서 친구들을 돕는 용감한 토끼의 이야기"
        ),
        BookRecommendation(
            title="하늘을 나는 코끼리",
            author="이상상",
            lexile_level=450,
            description="꿈을 포기하지 않는 작은 코끼리의 여정"
        ),
        BookRecommendation(
            title="마법의 숲 친구들",
            author="박요정",
            lexile_level=380,
            description="다양한 동물 친구들이 함께하는 우정 이야기"
        )
    ]
    
    # 읽기 수준에 맞는 책 필터링
    filtered_books = [
        book for book in sample_books
        if abs(book.lexile_level - request.reading_level) <= 100
    ]
    
    if not filtered_books:
        filtered_books = sample_books[:2]
    
    return BookRecommendationResponse(recommendations=filtered_books)


@app.get("/report/{user_id}")
async def get_user_report(user_id: str):
    """
    사용자 리포트 API
    
    사용자의 읽기 활동 및 진행 상황 리포트를 반환합니다.
    """
    # 샘플 리포트 (실제 구현에서는 DB 연동)
    return {
        "user_id": user_id,
        "report": {
            "total_stories_read": 15,
            "total_reading_time_minutes": 180,
            "current_lexile_level": 450,
            "level_progress": "+30 from last month",
            "favorite_topics": ["동물", "모험", "우정"],
            "achievements": ["첫 번째 스토리 완독", "10권 달성", "매일 읽기 7일 연속"]
        }
    }


@app.post("/rag/add_knowledge")
async def add_knowledge(documents: list[str], sources: list[str]):
    """
    RAG 지식 베이스에 문서 추가
    
    새로운 지식을 추가하여 스토리 생성 시 참조할 수 있도록 합니다.
    """
    if len(documents) != len(sources):
        raise HTTPException(
            status_code=400, 
            detail="documents와 sources의 길이가 일치해야 합니다."
        )
    
    try:
        rag = get_rag_system()
        rag.add_documents(documents, sources)
        return {
            "message": f"{len(documents)}개의 문서가 지식 베이스에 추가되었습니다.",
            "total_documents": rag.collection.count()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rag/search")
async def search_knowledge(query: str, n_results: int = 3):
    """
    RAG 지식 베이스 검색
    
    쿼리와 관련된 지식을 검색합니다.
    """
    try:
        rag = get_rag_system()
        results = rag.retrieve(query, n_results=n_results)
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rag/fact_check")
async def fact_check(statement: str):
    """
    팩트 체크 API
    
    문장이 지식 베이스의 정보와 일치하는지 확인합니다.
    할루시네이션 감지에 활용할 수 있습니다.
    """
    try:
        rag = get_rag_system()
        result = rag.fact_check(statement)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/safety/check")
async def check_content_safety(text: str, age: int = 7):
    """
    콘텐츠 안전성 검사 API
    
    텍스트가 아동에게 안전한지 확인합니다.
    """
    is_safe, issue = ContentFilter.is_safe(text)
    age_check = ContentFilter.check_age_appropriateness(text, age)
    
    return {
        "is_safe": is_safe,
        "issue": issue,
        "age_appropriateness": age_check
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
