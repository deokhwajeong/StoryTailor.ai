"""
StoryTailor.ai FastAPI Main Entry Point
Child-safe story generation API with RAG-based hallucination prevention
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
    BookRecommendation,
    KnowledgeAddRequest,
    RAGStatsResponse
)
from .story_engine import get_story_engine
from .rag import get_rag_system
from .safety import ContentFilter

app = FastAPI(
    title="StoryTailor.ai API",
    description="""
    AI Story Generation Platform API for Children
    
    ## Key Features
    - **Story Generation**: RAG-based hallucination-free story generation
    - **Reading Level Diagnostics**: Lexile level measurement
    - **Book Recommendations**: Personalized book recommendations
    
    ## RAG (Retrieval Augmented Generation)
    Uses retrieval-based generation system to prevent LLM hallucinations:
    1. Search for relevant information in knowledge base
    2. Provide retrieved information as context to LLM
    3. Generate fact-based stories
    4. Enable verification through source tracking
    """,
    version="1.0.0"
)

# CORS configuration (for frontend integration)
# In production, use ALLOWED_ORIGINS environment variable to allow only specific domains
# Example: export ALLOWED_ORIGINS="https://storytailor.ai,https://www.storytailor.ai"
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
    """API root endpoint"""
    return {
        "message": "Welcome to StoryTailor.ai API!",
        "docs": "/docs",
        "features": [
            "RAG-based hallucination-free story generation",
            "Child-safe content filtering",
            "Reading level diagnostics",
            "Personalized book recommendations"
        ]
    }


@app.post("/generate_story", response_model=StoryResponse)
async def generate_story(request: StoryRequest):
    """
    Story Generation API
    
    Uses RAG (Retrieval Augmented Generation) to prevent hallucinations and
    generate fact-based children's stories.
    
    Args:
        request: Story generation request (age, preferences, learning goal, etc.)
    
    Returns:
        Generated story with reference sources and confidence score
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
        raise HTTPException(status_code=500, detail=f"Error during story generation: {str(e)}")


@app.post("/diagnose_reading_level", response_model=ReadingDiagnosticResponse)
async def diagnose_reading_level(request: ReadingDiagnosticRequest):
    """
    Reading Level Diagnostics API
    
    Analyzes a child's reading sample to measure Lexile level.
    Uses RAG to provide personalized improvement recommendations.
    """
    # Simple heuristic-based diagnosis (actual implementation uses ML models)
    sample = request.reading_sample
    word_count = len(sample.split())
    sentence_count = len([s for s in sample.split('.') if s.strip()])
    
    if sentence_count == 0:
        sentence_count = 1
    
    avg_words_per_sentence = word_count / sentence_count
    
    # Lexile level estimation (simple formula)
    estimated_lexile = int(100 + avg_words_per_sentence * 20)
    estimated_lexile = max(100, min(1500, estimated_lexile))
    
    # RAG-based recommendations
    rag_recommendations = []
    if request.use_rag:
        try:
            rag = get_rag_system()
            # Search for learning-related knowledge
            results = rag.retrieve("reading education learning children", n_results=2)
            for result in results:
                rag_recommendations.append(result.get("content", "")[:200])
        except Exception:
            pass  # Continue without RAG if it fails
    
    return ReadingDiagnosticResponse(
        user_id=request.user_id,
        lexile_level=estimated_lexile,
        assessment_details={
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_words_per_sentence": round(avg_words_per_sentence, 1),
            "method": "heuristic",
            "rag_enabled": request.use_rag
        },
        rag_recommendations=rag_recommendations
    )


@app.post("/recommend_books", response_model=BookRecommendationResponse)
async def recommend_books(request: BookRecommendationRequest):
    """
    Book Recommendation API
    
    Recommends books based on reading level and preferences.
    Uses RAG to enhance recommendations with knowledge base.
    """
    # Sample recommendations (actual implementation integrates with DB or external API)
    sample_books = [
        BookRecommendation(
            title="The Brave Rabbit's Adventure",
            author="Kim Donghwa",
            lexile_level=400,
            description="A story of a brave rabbit helping friends in the forest"
        ),
        BookRecommendation(
            title="The Flying Elephant",
            author="Lee Sangsang",
            lexile_level=450,
            description="A journey of a little elephant who never gives up on dreams"
        ),
        BookRecommendation(
            title="Friends of the Magic Forest",
            author="Park Yojung",
            lexile_level=380,
            description="A friendship story with various animal friends"
        )
    ]
    
    # Filter books by reading level
    filtered_books = [
        book for book in sample_books
        if abs(book.lexile_level - request.reading_level) <= 100
    ]
    
    if not filtered_books:
        filtered_books = sample_books[:2]
    
    # RAG-based source tracking
    rag_sources = []
    if request.use_rag and request.preferences:
        try:
            rag = get_rag_system()
            query = " ".join(request.preferences)
            results = rag.retrieve(query, n_results=2)
            rag_sources = [r.get("source", "Unknown") for r in results]
        except Exception:
            pass  # Continue without RAG if it fails
    
    return BookRecommendationResponse(
        recommendations=filtered_books,
        rag_sources=rag_sources
    )


@app.get("/report/{user_id}")
async def get_user_report(user_id: str):
    """
    User Report API
    
    Returns the user's reading activity and progress report.
    Includes RAG system statistics and usage.
    """
    # Get RAG statistics
    rag_stats = {}
    try:
        rag = get_rag_system()
        rag_stats = {
            "total_knowledge_documents": rag.collection.count(),
            "rag_enabled": True
        }
    except Exception:
        rag_stats = {
            "total_knowledge_documents": 0,
            "rag_enabled": False
        }
    
    # Sample report (actual implementation integrates with DB)
    return {
        "user_id": user_id,
        "report": {
            "total_stories_read": 15,
            "total_reading_time_minutes": 180,
            "current_lexile_level": 450,
            "level_progress": "+30 from last month",
            "favorite_topics": ["animals", "adventure", "friendship"],
            "achievements": ["First story completed", "10 books achieved", "7 consecutive days of reading"]
        },
        "rag_stats": rag_stats
    }


@app.post("/rag/add_knowledge")
async def add_knowledge(request: KnowledgeAddRequest):
    """
    Add documents to RAG knowledge base
    
    Adds new knowledge to be referenced during story generation.
    """
    if len(request.documents) != len(request.sources):
        raise HTTPException(
            status_code=400, 
            detail="Length of documents and sources must match."
        )
    
    try:
        rag = get_rag_system()
        rag.add_documents(request.documents, request.sources)
        return {
            "message": f"{len(request.documents)} documents have been added to the knowledge base.",
            "total_documents": rag.collection.count()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rag/search")
async def search_knowledge(query: str, n_results: int = 3):
    """
    RAG Knowledge Base Search
    
    Searches for knowledge related to the query.
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
    Fact Check API
    
    Verifies if a statement matches information in the knowledge base.
    Can be used for hallucination detection.
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
    Content Safety Check API
    
    Verifies if text is safe for children.
    """
    is_safe, issue = ContentFilter.is_safe(text)
    age_check = ContentFilter.check_age_appropriateness(text, age)
    
    return {
        "is_safe": is_safe,
        "issue": issue,
        "age_appropriateness": age_check
    }


@app.get("/rag/stats", response_model=RAGStatsResponse)
async def get_rag_stats():
    """
    RAG System Statistics API
    
    Returns statistics about the RAG knowledge base.
    """
    try:
        rag = get_rag_system()
        total_docs = rag.collection.count()
        
        # Get unique categories from default knowledge
        categories = list(set(
            doc.get("metadata", {}).get("category", "general")
            for doc in rag.default_knowledge
        ))
        
        return RAGStatsResponse(
            total_documents=total_docs,
            categories=categories,
            recent_queries=0  # Would track in production
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
