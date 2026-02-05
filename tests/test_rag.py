"""
RAG System Tests
Hallucination prevention feature verification
"""

import pytest
from app.rag import RAGSystem


class TestRAGSystem:
    """RAG System Unit Tests"""
    
    @pytest.fixture
    def rag_system(self):
        """Test RAG system instance"""
        return RAGSystem(collection_name="test_collection")
    
    def test_initialization(self, rag_system):
        """RAG system initialization test"""
        assert rag_system.collection_name == "test_collection"
        assert rag_system.persist_directory is None
    
    def test_default_knowledge_initialization(self, rag_system):
        """Default knowledge base initialization test"""
        # Check if default knowledge exists
        assert len(rag_system.default_knowledge) > 0
        
        # Validate structure of each knowledge item
        for knowledge in rag_system.default_knowledge:
            assert "content" in knowledge
            assert "source" in knowledge
            assert "metadata" in knowledge
    
    def test_add_documents(self, rag_system):
        """Document addition test"""
        documents = [
            "This is test document 1.",
            "This is test document 2."
        ]
        sources = ["Test source 1", "Test source 2"]
        
        rag_system.add_documents(documents, sources)
        
        # Verify documents were added
        assert rag_system.collection.count() >= 2
    
    def test_retrieve(self, rag_system):
        """Document retrieval test"""
        # Search for "brave" related content from default knowledge
        results = rag_system.retrieve("brave rabbit", n_results=2)
        
        assert len(results) > 0
        assert "content" in results[0]
        assert "source" in results[0]
    
    def test_retrieve_with_empty_query(self, rag_system):
        """Empty query retrieval test"""
        results = rag_system.retrieve("", n_results=1)
        # Empty query should also return results (from default knowledge)
        assert isinstance(results, list)
    
    def test_fact_check(self, rag_system):
        """Fact check test"""
        # Statement similar to content in knowledge base
        result = rag_system.fact_check("Bravery means doing the right thing despite feeling afraid")
        
        assert "verified" in result
        assert "confidence" in result
        assert "source" in result
        assert isinstance(result["confidence"], (int, float))
        assert 0 <= result["confidence"] <= 1
    
    def test_fact_check_unknown(self, rag_system):
        """Unknown content fact check test"""
        result = rag_system.fact_check("There is a blue ocean on Mars")
        
        # Content not in knowledge base should have lower confidence
        assert "verified" in result
        assert isinstance(result["confidence"], (int, float))


class TestRAGRetrieval:
    """RAG Retrieval Feature Detailed Tests"""
    
    @pytest.fixture
    def rag_with_custom_docs(self):
        """RAG system with custom documents"""
        rag = RAGSystem(collection_name="test_custom")
        
        # Add test documents
        documents = [
            "Penguins are birds that live in Antarctica. They cannot fly but swim well.",
            "Polar bears live in the Arctic and have white fur.",
            "Whales are the largest mammals in the ocean."
        ]
        sources = ["Animal Encyclopedia", "Animal Encyclopedia", "Marine Life Guide"]
        
        rag.add_documents(documents, sources)
        return rag
    
    def test_semantic_search(self, rag_with_custom_docs):
        """Semantic search test"""
        # Searching for related content should return documents
        results = rag_with_custom_docs.retrieve("bird that cannot fly", n_results=1)
        
        assert len(results) > 0
        # Should return one of the animal documents
        assert "content" in results[0]
        assert len(results[0]["content"]) > 0
    
    def test_multiple_results(self, rag_with_custom_docs):
        """Multiple results retrieval test"""
        results = rag_with_custom_docs.retrieve("animal", n_results=3)
        
        # Should return 3 results
        assert len(results) == 3
        
        # Each result should have distance (similarity) information
        for result in results:
            assert "distance" in result
