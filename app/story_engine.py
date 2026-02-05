"""
Story Generation Engine
Story generation engine - RAG integration
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
    """Story generation engine"""
    
    def __init__(self, rag_system: Optional[RAGSystem] = None):
        """
        Initialize story engine
        
        Args:
            rag_system: RAG system instance (None uses default instance)
        """
        self.rag_system = rag_system or get_rag_system()
        self._openai_client = None
    
    @property
    def openai_client(self):
        """OpenAI client (lazy initialization)"""
        if self._openai_client is None:
            if not OPENAI_AVAILABLE:
                raise ImportError(
                    "openai package is not installed."
                )
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set.")
            self._openai_client = OpenAI(api_key=api_key)
        return self._openai_client
    
    def generate_story(self, request: StoryRequest) -> StoryResponse:
        """
        Generate story
        
        Args:
            request: Story generation request
        
        Returns:
            Generated story response
        """
        # Request validation
        query = " ".join(request.preferences) if request.preferences else "fun adventure"
        
        # Pre-check safety
        is_safe, issue = ContentFilter.is_safe(query)
        if not is_safe:
            return StoryResponse(
                story=f"Sorry, we cannot process the requested topic. ({issue})",
                sources=[],
                fact_checked=False,
                confidence_score=0.0
            )
        
        if request.use_rag:
            # RAG-based hallucination-free story generation
            return self._generate_with_rag(request, query)
        else:
            # Basic LLM story generation (without RAG)
            return self._generate_basic(request, query)
    
    def _generate_with_rag(
        self, 
        request: StoryRequest, 
        query: str
    ) -> StoryResponse:
        """Generate story using RAG"""
        # Search related documents
        retrieved_docs = self.rag_system.retrieve(
            query=query,
            n_results=3
        )
        
        # Extract RAG context for response
        rag_context = [doc.get("content", "")[:150] for doc in retrieved_docs]
        
        # Generate story based on context
        result = self.rag_system.generate_with_context(
            query=query,
            retrieved_docs=retrieved_docs,
            age=request.age,
            preferences=request.preferences,
            learning_goal=request.learning_goal
        )
        
        # Check and sanitize generated story safety
        story = result["story"]
        is_safe, _ = ContentFilter.is_safe(story)
        if not is_safe:
            story = ContentFilter.sanitize(story)
        
        return StoryResponse(
            story=story,
            sources=result["sources"],
            fact_checked=result["fact_checked"],
            confidence_score=result["confidence_score"],
            rag_context=rag_context
        )
    
    def _generate_basic(
        self, 
        request: StoryRequest, 
        query: str
    ) -> StoryResponse:
        """Basic LLM story generation (without RAG) - risk of hallucination"""
        system_prompt = f"""You are a children's story writer for {request.age}-year-old children.
Use vocabulary and sentence length appropriate for the child's age.
Avoid violent or scary content and include positive messages."""

        user_prompt = f"""Topic: {query}
Learning Goal: {request.learning_goal or 'A fun and educational story'}

Please create a short story on the above topic."""

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
        
        # Check and sanitize safety
        is_safe, _ = ContentFilter.is_safe(story)
        if not is_safe:
            story = ContentFilter.sanitize(story)
        
        return StoryResponse(
            story=story,
            sources=[],
            fact_checked=False,  # No fact check without RAG
            confidence_score=0.5  # Lower confidence without RAG
        )


# Global engine instance
_engine_instance: Optional[StoryEngine] = None


def get_story_engine() -> StoryEngine:
    """Return story engine singleton instance"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = StoryEngine()
    return _engine_instance
