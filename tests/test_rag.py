"""
RAG 시스템 테스트
할루시네이션 방지 기능 검증
"""

import pytest
from app.rag import RAGSystem


class TestRAGSystem:
    """RAG 시스템 단위 테스트"""
    
    @pytest.fixture
    def rag_system(self):
        """테스트용 RAG 시스템 인스턴스"""
        return RAGSystem(collection_name="test_collection")
    
    def test_initialization(self, rag_system):
        """RAG 시스템 초기화 테스트"""
        assert rag_system.collection_name == "test_collection"
        assert rag_system.persist_directory is None
    
    def test_default_knowledge_initialization(self, rag_system):
        """기본 지식 베이스 초기화 테스트"""
        # 기본 지식이 있는지 확인
        assert len(rag_system.default_knowledge) > 0
        
        # 각 지식 항목의 구조 검증
        for knowledge in rag_system.default_knowledge:
            assert "content" in knowledge
            assert "source" in knowledge
            assert "metadata" in knowledge
    
    def test_add_documents(self, rag_system):
        """문서 추가 테스트"""
        documents = [
            "테스트 문서 1입니다.",
            "테스트 문서 2입니다."
        ]
        sources = ["테스트 출처 1", "테스트 출처 2"]
        
        rag_system.add_documents(documents, sources)
        
        # 문서가 추가되었는지 확인
        assert rag_system.collection.count() >= 2
    
    def test_retrieve(self, rag_system):
        """문서 검색 테스트"""
        # 기본 지식에서 "용감함" 관련 검색
        results = rag_system.retrieve("용감한 토끼", n_results=2)
        
        assert len(results) > 0
        assert "content" in results[0]
        assert "source" in results[0]
    
    def test_retrieve_with_empty_query(self, rag_system):
        """빈 쿼리 검색 테스트"""
        results = rag_system.retrieve("", n_results=1)
        # 빈 쿼리도 결과 반환 (기본 지식에서)
        assert isinstance(results, list)
    
    def test_fact_check(self, rag_system):
        """팩트 체크 테스트"""
        # 지식 베이스에 있는 내용과 유사한 문장
        result = rag_system.fact_check("용감함은 두려움을 느끼면서도 옳은 일을 하는 것이다")
        
        assert "verified" in result
        assert "confidence" in result
        assert "source" in result
        assert isinstance(result["confidence"], (int, float))
        assert 0 <= result["confidence"] <= 1
    
    def test_fact_check_unknown(self, rag_system):
        """알 수 없는 내용 팩트 체크 테스트"""
        result = rag_system.fact_check("화성에는 푸른 바다가 있다")
        
        # 지식 베이스에 없는 내용이므로 신뢰도가 낮아야 함
        assert "verified" in result
        assert isinstance(result["confidence"], (int, float))


class TestRAGRetrieval:
    """RAG 검색 기능 상세 테스트"""
    
    @pytest.fixture
    def rag_with_custom_docs(self):
        """커스텀 문서가 있는 RAG 시스템"""
        rag = RAGSystem(collection_name="test_custom")
        
        # 테스트용 문서 추가
        documents = [
            "펭귄은 남극에 사는 새입니다. 날지 못하지만 수영을 잘합니다.",
            "북극곰은 북극에 살며 흰 털을 가지고 있습니다.",
            "고래는 바다에서 가장 큰 포유류입니다."
        ]
        sources = ["동물 백과", "동물 백과", "바다 생물 도감"]
        
        rag.add_documents(documents, sources)
        return rag
    
    def test_semantic_search(self, rag_with_custom_docs):
        """의미 기반 검색 테스트"""
        # "남극 동물"로 검색하면 펭귄 관련 문서가 나와야 함
        results = rag_with_custom_docs.retrieve("남극 동물", n_results=1)
        
        assert len(results) > 0
        # 펭귄 관련 내용이 포함되어야 함
        assert "펭귄" in results[0]["content"] or "남극" in results[0]["content"]
    
    def test_multiple_results(self, rag_with_custom_docs):
        """복수 결과 검색 테스트"""
        results = rag_with_custom_docs.retrieve("동물", n_results=3)
        
        # 3개의 결과가 반환되어야 함
        assert len(results) == 3
        
        # 각 결과에 거리(유사도) 정보가 있어야 함
        for result in results:
            assert "distance" in result
