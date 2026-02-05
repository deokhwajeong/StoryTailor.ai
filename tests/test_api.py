"""
API Integration Tests
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


class TestAPIEndpoints:
    """API Endpoint Tests"""
    
    def test_root_endpoint(self, client):
        """Root endpoint test"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "features" in data
        assert "RAG" in str(data["features"])
    
    def test_reading_level_diagnosis(self, client):
        """Reading level diagnosis test"""
        response = client.post(
            "/diagnose_reading_level",
            json={
                "user_id": "test_user",
                "reading_sample": "The rabbit jumped. The flower bloomed."
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user"
        assert "lexile_level" in data
        assert isinstance(data["lexile_level"], int)
    
    def test_book_recommendation(self, client):
        """Book recommendation test"""
        response = client.post(
            "/recommend_books",
            json={
                "user_id": "test_user",
                "reading_level": 400,
                "preferences": ["animals", "adventure"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) > 0
    
    def test_user_report(self, client):
        """User report test"""
        response = client.get("/report/test_user")
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user"
        assert "report" in data
    
    def test_content_safety_check(self, client):
        """Content safety check test"""
        response = client.post(
            "/safety/check",
            params={"text": "A cute rabbit played in the forest", "age": 7}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "is_safe" in data
        assert data["is_safe"] is True
    
    def test_content_safety_check_unsafe(self, client):
        """Unsafe content check test"""
        response = client.post(
            "/safety/check",
            params={"text": "A scary monster appeared", "age": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_safe"] is False


class TestRAGEndpoints:
    """RAG-related API Tests"""
    
    def test_rag_search(self, client):
        """RAG search test"""
        response = client.get(
            "/rag/search",
            params={"query": "brave rabbit", "n_results": 2}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert "count" in data
    
    def test_rag_fact_check(self, client):
        """RAG fact check test"""
        response = client.post(
            "/rag/fact_check",
            params={"statement": "Bravery is about overcoming fear"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "verified" in data
        assert "confidence" in data


class TestStoryGeneration:
    """Story generation tests (without OpenAI API)"""
    
    def test_story_request_validation(self, client):
        """Story request validation test"""
        # Invalid age value
        response = client.post(
            "/generate_story",
            json={
                "age": 2,  # Minimum 3 years old
                "preferences": ["rabbit"],
                "use_rag": True
            }
        )
        
        # Pydantic validation failure
        assert response.status_code == 422
    
    def test_story_request_valid_structure(self, client):
        """Valid story request structure test"""
        import os
        
        response = client.post(
            "/generate_story",
            json={
                "age": 7,
                "preferences": ["rabbit", "adventure"],
                "learning_goal": "value of friendship",
                "use_rag": True
            }
        )
        
        # If API key is set: 200, if not: 400 (ValueError)
        has_api_key = bool(os.getenv("OPENAI_API_KEY"))
        if has_api_key:
            assert response.status_code == 200
        else:
            # No API key -> ValueError -> 400 Bad Request
            assert response.status_code == 400
