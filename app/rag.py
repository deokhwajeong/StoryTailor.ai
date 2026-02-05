"""
RAG (Retrieval Augmented Generation) Module
Retrieval-based generation system for LLM hallucination prevention

Core principles of RAG:
1. Search for relevant information from external knowledge base
2. Provide retrieved information as context in LLM prompts
3. LLM generates responses based on retrieved facts
4. Enable verification through source tracking
"""

import hashlib
import os
from typing import Optional

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class SimpleEmbeddingFunction:
    """
    Simple local embedding function (works without network)
    For production, recommend using sentence-transformers or OpenAI embeddings
    Implements ChromaDB EmbeddingFunction interface
    """
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self._name = "simple_embedding"
    
    def name(self) -> str:
        """ChromaDB interface requirement - embedding function name"""
        return self._name
    
    def __call__(self, input: list[str]) -> list[list[float]]:
        """Convert text to embedding vectors"""
        embeddings = []
        for text in input:
            # Simple hash-based embedding (for demo)
            # Use more sophisticated embedding models in production
            embedding = self._text_to_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        """ChromaDB compatible method - document embedding"""
        return self(documents)
    
    def embed_query(self, input) -> list[list[float]]:
        """ChromaDB compatible method - query embedding (handles list or single string)"""
        if isinstance(input, str):
            return [self._text_to_embedding(input)]
        elif isinstance(input, list):
            return self(input)
        else:
            return [self._text_to_embedding(str(input))]
    
    def _text_to_embedding(self, text: str) -> list[float]:
        """Convert text to fixed-size vector"""
        # Simple feature extraction for Korean text
        features = []
        
        # Text normalization
        text = text.lower().strip()
        
        # Keyword-based features (domain-specific)
        keywords = {
            "brave": 0, "rabbit": 1, "friend": 2, "friendship": 3, "adventure": 4,
            "forest": 5, "animal": 6, "family": 7, "love": 8, "fear": 9,
            "courage": 10, "nature": 11, "lesson": 12, "learning": 13, "failure": 14,
            "success": 15, "help": 16, "together": 17, "respect": 18, "understand": 19
        }
        
        # Keyword presence as features
        keyword_features = [0.0] * 20
        for keyword, idx in keywords.items():
            if keyword in text:
                keyword_features[idx] = 1.0
        
        # Text length-based features
        length_features = [
            min(len(text) / 100, 1.0),  # Normalized length
            min(len(text.split()) / 20, 1.0),  # Word count
        ]
        
        # Hash-based additional features (fill remaining dimensions)
        # Using SHA256 for collision resistance (for feature generation, not security)
        hash_hex = hashlib.sha256(text.encode()).hexdigest()
        hash_features = []
        for i in range(0, min(len(hash_hex) - 1, 32), 2):
            val = int(hash_hex[i:i+2], 16) / 255.0
            hash_features.append(val)
        
        # Combine all features
        features = keyword_features + length_features + hash_features
        
        # Pad to target dimension
        while len(features) < self.dimension:
            features.append(0.0)
        
        return features[:self.dimension]


class RAGSystem:
    """
    RAG System - Retrieval-based generation for hallucination prevention
    
    Usage:
    1. Add documents to knowledge base: add_documents()
    2. Search related documents during story generation: retrieve()
    3. Generate story using retrieved documents as context: generate_with_context()
    """
    
    def __init__(
        self, 
        collection_name: str = "storytailor_knowledge",
        persist_directory: Optional[str] = None
    ):
        """
        Initialize RAG system
        
        Args:
            collection_name: ChromaDB collection name
            persist_directory: Vector DB storage path (None for in-memory)
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self._client = None
        self._collection = None
        self._openai_client = None
        
        # Default knowledge base for children's stories
        self.default_knowledge = [
            {
                "content": "In stories, bravery means doing the right thing even when feeling afraid. "
                          "It's important to teach children that courage is not the absence of fear, "
                          "but acting despite the fear.",
                "source": "Child Education Principles",
                "metadata": {"category": "character_traits", "theme": "courage"}
            },
            {
                "content": "The value of friendship lies in understanding each other, helping in difficult times, "
                          "and sharing joy together. Good friends respect and accept each other's differences.",
                "source": "Child Development Psychology",
                "metadata": {"category": "relationships", "theme": "friendship"}
            },
            {
                "content": "Stories about nature and animals help children understand the importance of ecosystems "
                          "and develop respect for all living things.",
                "source": "Environmental Education Guide",
                "metadata": {"category": "nature", "theme": "animals"}
            },
            {
                "content": "Family love is unconditional. The bond between parents and children plays "
                          "a crucial role in a child's emotional stability and self-esteem development.",
                "source": "Family Psychology",
                "metadata": {"category": "relationships", "theme": "family"}
            },
            {
                "content": "Failure and mistakes are opportunities for learning. It's important to let children know "
                          "that it's okay to fail and encourage them to try again.",
                "source": "Growth Mindset Research",
                "metadata": {"category": "life_lessons", "theme": "perseverance"}
            },
            {
                "content": "Rabbits can actually run fast, reaching speeds up to 70 km/h. "
                          "A rabbit's long ears help detect predators and regulate body temperature.",
                "source": "Animal Encyclopedia",
                "metadata": {"category": "animals", "theme": "rabbits"}
            },
            {
                "content": "Forests are home to diverse animals. Squirrels, foxes, deer, and birds "
                          "live together forming an ecosystem. Each animal plays an important role in the forest.",
                "source": "Ecology Basics",
                "metadata": {"category": "nature", "theme": "forest"}
            },
            {
                "content": "In adventure stories, the protagonist typically leaves home to explore a new world, "
                          "overcomes challenges, and returns having grown. This is the 'Hero's Journey' structure.",
                "source": "Narrative Structure Theory",
                "metadata": {"category": "narrative", "theme": "adventure"}
            }
        ]
    
    @property
    def client(self):
        """ChromaDB client (lazy initialization)"""
        if self._client is None:
            if not CHROMADB_AVAILABLE:
                raise ImportError(
                    "chromadb package is not installed. "
                    "Run 'pip install chromadb'."
                )
            
            if self.persist_directory:
                self._client = chromadb.PersistentClient(
                    path=self.persist_directory
                )
            else:
                self._client = chromadb.Client()
        return self._client
    
    @property
    def collection(self):
        """ChromaDB collection (lazy initialization)"""
        if self._collection is None:
            # Use local embedding function (no network required)
            embedding_fn = SimpleEmbeddingFunction()
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "StoryTailor.ai Knowledge Base"},
                embedding_function=embedding_fn
            )
        return self._collection
    
    @property
    def openai_client(self):
        """OpenAI client (lazy initialization)"""
        if self._openai_client is None:
            if not OPENAI_AVAILABLE:
                raise ImportError(
                    "openai package is not installed. "
                    "Run 'pip install openai'."
                )
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is not set.")
            self._openai_client = OpenAI(api_key=api_key)
        return self._openai_client
    
    def initialize_default_knowledge(self):
        """Initialize default knowledge base"""
        documents = [doc["content"] for doc in self.default_knowledge]
        metadatas = [doc["metadata"] | {"source": doc["source"]} 
                     for doc in self.default_knowledge]
        ids = [f"default_{i}" for i in range(len(documents))]
        
        # Check existing documents before adding
        existing = self.collection.get(ids=ids)
        if not existing["ids"]:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
    
    def add_documents(
        self, 
        documents: list[str], 
        sources: list[str],
        metadatas: Optional[list[dict]] = None
    ):
        """
        Add documents to knowledge base
        
        Args:
            documents: List of document contents
            sources: List of sources
            metadatas: List of metadata (optional)
        """
        if metadatas is None:
            metadatas = [{"source": src} for src in sources]
        else:
            for i, meta in enumerate(metadatas):
                meta["source"] = sources[i]
        
        ids = [f"doc_{self.collection.count() + i}" for i in range(len(documents))]
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def retrieve(
        self, 
        query: str, 
        n_results: int = 3,
        filter_metadata: Optional[dict] = None
    ) -> list[dict]:
        """
        Search for related documents
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Metadata filter (optional)
        
        Returns:
            List of retrieved documents (content, source, metadata, distance included)
        """
        # Initialize default knowledge if collection is empty
        if self.collection.count() == 0:
            self.initialize_default_knowledge()
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filter_metadata
        )
        
        retrieved_docs = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                retrieved_docs.append({
                    "content": doc,
                    "source": results["metadatas"][0][i].get("source", "unknown"),
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if results["distances"] else None
                })
        
        return retrieved_docs
    
    def generate_with_context(
        self,
        query: str,
        retrieved_docs: list[dict],
        age: int,
        preferences: list[str],
        learning_goal: Optional[str] = None
    ) -> dict:
        """
        Generate story based on retrieved context (hallucination prevention)
        
        Args:
            query: User request
            retrieved_docs: Retrieved documents
            age: Child's age
            preferences: Preferred topics
            learning_goal: Learning goal
        
        Returns:
            Generated story and metadata
        """
        # Build context
        context_parts = []
        sources = []
        for doc in retrieved_docs:
            context_parts.append(f"- {doc['content']}")
            if doc["source"] not in sources:
                sources.append(doc["source"])
        
        context = "\n".join(context_parts)
        
        # Build RAG-enhanced prompt
        system_prompt = f"""You are a children's story writer for {age}-year-old children.
You must use the reference information below to create fact-based stories.

## Reference Information (base your writing on this):
{context}

## Important Guidelines:
1. Only use facts from the reference information
2. Do not include uncertain information
3. Use vocabulary and sentence length appropriate for a {age}-year-old
4. Avoid violent or scary content
5. Include positive messages and lessons
"""
        
        user_prompt = f"""Topic: {', '.join(preferences) if preferences else query}
Learning Goal: {learning_goal or 'A fun and educational story'}

Please create a short story on the above topic. Naturally incorporate the facts from the reference information."""

        # OpenAI API call
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        story = response.choices[0].message.content
        
        # Calculate confidence score (based on similarity of retrieved documents)
        if retrieved_docs:
            avg_distance = sum(d["distance"] or 0 for d in retrieved_docs) / len(retrieved_docs)
            # Lower distance means higher similarity (convert 0~2 range to 0~1)
            confidence_score = max(0, min(1, 1 - (avg_distance / 2)))
        else:
            confidence_score = 0.5  # Default value if no reference documents
        
        return {
            "story": story,
            "sources": sources,
            "fact_checked": len(retrieved_docs) > 0,
            "confidence_score": round(confidence_score, 2)
        }
    
    def fact_check(self, statement: str, threshold: float = 0.5) -> dict:
        """
        Verify the factuality of a statement
        
        Args:
            statement: Statement to verify
            threshold: Similarity threshold
        
        Returns:
            Verification result
        """
        results = self.retrieve(statement, n_results=1)
        
        if not results:
            return {
                "verified": False,
                "confidence": 0.0,
                "source": None,
                "message": "No related information found."
            }
        
        top_result = results[0]
        distance = top_result["distance"] or 2.0
        confidence = max(0, min(1, 1 - (distance / 2)))
        
        return {
            "verified": confidence >= threshold,
            "confidence": round(confidence, 2),
            "source": top_result["source"],
            "related_content": top_result["content"],
            "message": "Verified" if confidence >= threshold else "Not verified"
        }


# Global RAG instance
_rag_instance: Optional[RAGSystem] = None


def get_rag_system() -> RAGSystem:
    """Return RAG system singleton instance"""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGSystem()
    return _rag_instance
