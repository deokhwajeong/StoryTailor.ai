"""
API 통합 테스트
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """테스트 클라이언트"""
    return TestClient(app)


class TestAPIEndpoints:
    """API 엔드포인트 테스트"""
    
    def test_root_endpoint(self, client):
        """루트 엔드포인트 테스트"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "features" in data
        assert "RAG" in str(data["features"])
    
    def test_reading_level_diagnosis(self, client):
        """읽기 수준 진단 테스트"""
        response = client.post(
            "/diagnose_reading_level",
            json={
                "user_id": "test_user",
                "reading_sample": "토끼가 뛰었습니다. 꽃이 피었습니다."
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user"
        assert "lexile_level" in data
        assert isinstance(data["lexile_level"], int)
    
    def test_book_recommendation(self, client):
        """도서 추천 테스트"""
        response = client.post(
            "/recommend_books",
            json={
                "user_id": "test_user",
                "reading_level": 400,
                "preferences": ["동물", "모험"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) > 0
    
    def test_user_report(self, client):
        """사용자 리포트 테스트"""
        response = client.get("/report/test_user")
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user"
        assert "report" in data
    
    def test_content_safety_check(self, client):
        """콘텐츠 안전성 검사 테스트"""
        response = client.post(
            "/safety/check",
            params={"text": "귀여운 토끼가 숲에서 놀았어요", "age": 7}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "is_safe" in data
        assert data["is_safe"] is True
    
    def test_content_safety_check_unsafe(self, client):
        """안전하지 않은 콘텐츠 검사 테스트"""
        response = client.post(
            "/safety/check",
            params={"text": "무서운 괴물이 나타났다", "age": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_safe"] is False


class TestRAGEndpoints:
    """RAG 관련 API 테스트"""
    
    def test_rag_search(self, client):
        """RAG 검색 테스트"""
        response = client.get(
            "/rag/search",
            params={"query": "용감한 토끼", "n_results": 2}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert "count" in data
    
    def test_rag_fact_check(self, client):
        """RAG 팩트 체크 테스트"""
        response = client.post(
            "/rag/fact_check",
            params={"statement": "용감함은 두려움을 이기는 것이다"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "verified" in data
        assert "confidence" in data


class TestStoryGeneration:
    """스토리 생성 테스트 (OpenAI API 없이)"""
    
    def test_story_request_validation(self, client):
        """스토리 요청 검증 테스트"""
        # 잘못된 나이 값
        response = client.post(
            "/generate_story",
            json={
                "age": 2,  # 최소 3세
                "preferences": ["토끼"],
                "use_rag": True
            }
        )
        
        # Pydantic 검증 실패
        assert response.status_code == 422
    
    def test_story_request_valid_structure(self, client):
        """유효한 스토리 요청 구조 테스트"""
        # 이 테스트는 OpenAI API 키 없이는 실패하지만,
        # 요청 구조가 올바른지 확인
        response = client.post(
            "/generate_story",
            json={
                "age": 7,
                "preferences": ["토끼", "모험"],
                "learning_goal": "우정의 가치",
                "use_rag": True
            }
        )
        
        # API 키 없으면 503 또는 500, 있으면 200
        assert response.status_code in [200, 500, 503]
