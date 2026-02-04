"""
RAG (Retrieval Augmented Generation) Module
LLM 할루시네이션 방지를 위한 검색 기반 생성 시스템

RAG의 핵심 원리:
1. 외부 지식 베이스에서 관련 정보를 검색
2. 검색된 정보를 LLM 프롬프트에 컨텍스트로 제공
3. LLM이 검색된 사실에 기반하여 응답 생성
4. 출처 추적으로 검증 가능성 확보
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
    간단한 로컬 임베딩 함수 (네트워크 없이 작동)
    실제 프로덕션에서는 sentence-transformers나 OpenAI embeddings 사용 권장
    ChromaDB EmbeddingFunction 인터페이스 구현
    """
    
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self._name = "simple_embedding"
    
    def name(self) -> str:
        """ChromaDB 인터페이스 요구사항 - 임베딩 함수 이름"""
        return self._name
    
    def __call__(self, input: list[str]) -> list[list[float]]:
        """텍스트를 임베딩 벡터로 변환"""
        embeddings = []
        for text in input:
            # 간단한 해시 기반 임베딩 (데모용)
            # 실제 프로덕션에서는 더 정교한 임베딩 모델 사용
            embedding = self._text_to_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def embed_documents(self, documents: list[str]) -> list[list[float]]:
        """ChromaDB 호환 메서드 - 문서 임베딩"""
        return self(documents)
    
    def embed_query(self, input) -> list[list[float]]:
        """ChromaDB 호환 메서드 - 쿼리 임베딩 (리스트 또는 단일 문자열 처리)"""
        if isinstance(input, str):
            return [self._text_to_embedding(input)]
        elif isinstance(input, list):
            return self(input)
        else:
            return [self._text_to_embedding(str(input))]
    
    def _text_to_embedding(self, text: str) -> list[float]:
        """텍스트를 고정 크기 벡터로 변환"""
        # 한국어 텍스트를 위한 간단한 특성 추출
        features = []
        
        # 텍스트 정규화
        text = text.lower().strip()
        
        # 키워드 기반 특성 (도메인 특화)
        keywords = {
            "용감": 0, "토끼": 1, "친구": 2, "우정": 3, "모험": 4,
            "숲": 5, "동물": 6, "가족": 7, "사랑": 8, "두려움": 9,
            "용기": 10, "자연": 11, "교훈": 12, "배움": 13, "실패": 14,
            "성공": 15, "도움": 16, "함께": 17, "존중": 18, "이해": 19
        }
        
        # 키워드 존재 여부를 특성으로
        keyword_features = [0.0] * 20
        for keyword, idx in keywords.items():
            if keyword in text:
                keyword_features[idx] = 1.0
        
        # 텍스트 길이 기반 특성
        length_features = [
            min(len(text) / 100, 1.0),  # 정규화된 길이
            min(len(text.split()) / 20, 1.0),  # 단어 수
        ]
        
        # 해시 기반 추가 특성 (남은 차원 채우기)
        hash_hex = hashlib.md5(text.encode()).hexdigest()
        hash_features = []
        for i in range(0, len(hash_hex) - 1, 2):
            val = int(hash_hex[i:i+2], 16) / 255.0
            hash_features.append(val)
        
        # 모든 특성 결합
        features = keyword_features + length_features + hash_features
        
        # 차원 맞추기
        while len(features) < self.dimension:
            features.append(0.0)
        
        return features[:self.dimension]


class RAGSystem:
    """
    RAG 시스템 - 할루시네이션 방지를 위한 검색 기반 생성
    
    사용 방법:
    1. 지식 베이스에 문서 추가: add_documents()
    2. 스토리 생성 시 관련 문서 검색: retrieve()
    3. 검색된 문서를 컨텍스트로 사용하여 스토리 생성: generate_with_context()
    """
    
    def __init__(
        self, 
        collection_name: str = "storytailor_knowledge",
        persist_directory: Optional[str] = None
    ):
        """
        RAG 시스템 초기화
        
        Args:
            collection_name: ChromaDB 컬렉션 이름
            persist_directory: 벡터 DB 저장 경로 (None이면 인메모리)
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self._client = None
        self._collection = None
        self._openai_client = None
        
        # 아동용 동화에 대한 기본 지식 베이스
        self.default_knowledge = [
            {
                "content": "동화에서 용감함은 두려움을 느끼면서도 옳은 일을 하는 것을 의미합니다. "
                          "아이들에게 용기란 완벽하게 두려움이 없는 것이 아니라, "
                          "두려움에도 불구하고 행동하는 것임을 알려주는 것이 중요합니다.",
                "source": "아동 교육 원칙",
                "metadata": {"category": "character_traits", "theme": "courage"}
            },
            {
                "content": "우정의 가치는 서로를 이해하고, 어려울 때 돕고, 함께 기쁨을 나누는 것입니다. "
                          "좋은 친구는 서로의 다름을 존중하고 받아들입니다.",
                "source": "아동 발달 심리학",
                "metadata": {"category": "relationships", "theme": "friendship"}
            },
            {
                "content": "자연과 동물에 대한 이야기는 아이들에게 생태계의 중요성과 "
                          "모든 생명을 존중하는 마음을 기를 수 있도록 도와줍니다.",
                "source": "환경 교육 가이드",
                "metadata": {"category": "nature", "theme": "animals"}
            },
            {
                "content": "가족의 사랑은 무조건적입니다. 부모와 자녀 간의 유대감은 "
                          "아이의 정서적 안정과 자존감 형성에 핵심적인 역할을 합니다.",
                "source": "가족 심리학",
                "metadata": {"category": "relationships", "theme": "family"}
            },
            {
                "content": "실패와 실수는 배움의 기회입니다. 아이들에게 실패해도 괜찮다는 것을 "
                          "알려주고, 다시 시도하는 용기를 북돋아 주는 것이 중요합니다.",
                "source": "성장 마인드셋 연구",
                "metadata": {"category": "life_lessons", "theme": "perseverance"}
            },
            {
                "content": "토끼는 실제로 빠르게 달릴 수 있으며, 최대 시속 70km까지 달릴 수 있습니다. "
                          "토끼의 긴 귀는 천적의 소리를 듣고 체온을 조절하는 데 도움을 줍니다.",
                "source": "동물 백과사전",
                "metadata": {"category": "animals", "theme": "rabbits"}
            },
            {
                "content": "숲에는 다양한 동물들이 살고 있습니다. 다람쥐, 여우, 사슴, 새들이 "
                          "서로 어울려 생태계를 이룹니다. 각 동물은 숲에서 중요한 역할을 합니다.",
                "source": "생태학 기초",
                "metadata": {"category": "nature", "theme": "forest"}
            },
            {
                "content": "모험 이야기에서 주인공은 보통 집을 떠나 새로운 세계를 탐험하고, "
                          "도전을 극복한 후 성장하여 돌아옵니다. 이것이 '영웅의 여정' 구조입니다.",
                "source": "서사 구조론",
                "metadata": {"category": "narrative", "theme": "adventure"}
            }
        ]
    
    @property
    def client(self):
        """ChromaDB 클라이언트 (지연 초기화)"""
        if self._client is None:
            if not CHROMADB_AVAILABLE:
                raise ImportError(
                    "chromadb 패키지가 설치되지 않았습니다. "
                    "'pip install chromadb'를 실행하세요."
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
        """ChromaDB 컬렉션 (지연 초기화)"""
        if self._collection is None:
            # 로컬 임베딩 함수 사용 (네트워크 불필요)
            embedding_fn = SimpleEmbeddingFunction()
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "StoryTailor.ai 지식 베이스"},
                embedding_function=embedding_fn
            )
        return self._collection
    
    @property
    def openai_client(self):
        """OpenAI 클라이언트 (지연 초기화)"""
        if self._openai_client is None:
            if not OPENAI_AVAILABLE:
                raise ImportError(
                    "openai 패키지가 설치되지 않았습니다. "
                    "'pip install openai'를 실행하세요."
                )
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
            self._openai_client = OpenAI(api_key=api_key)
        return self._openai_client
    
    def initialize_default_knowledge(self):
        """기본 지식 베이스 초기화"""
        documents = [doc["content"] for doc in self.default_knowledge]
        metadatas = [doc["metadata"] | {"source": doc["source"]} 
                     for doc in self.default_knowledge]
        ids = [f"default_{i}" for i in range(len(documents))]
        
        # 기존 문서 확인 후 추가
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
        지식 베이스에 문서 추가
        
        Args:
            documents: 문서 내용 리스트
            sources: 출처 리스트
            metadatas: 메타데이터 리스트 (선택)
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
        관련 문서 검색
        
        Args:
            query: 검색 쿼리
            n_results: 반환할 결과 수
            filter_metadata: 메타데이터 필터 (선택)
        
        Returns:
            검색된 문서 리스트 (content, source, metadata, distance 포함)
        """
        # 컬렉션이 비어있으면 기본 지식 초기화
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
        검색된 컨텍스트를 기반으로 스토리 생성 (할루시네이션 방지)
        
        Args:
            query: 사용자 요청
            retrieved_docs: 검색된 문서들
            age: 아이의 나이
            preferences: 선호 주제
            learning_goal: 학습 목표
        
        Returns:
            생성된 스토리와 메타데이터
        """
        # 컨텍스트 구성
        context_parts = []
        sources = []
        for doc in retrieved_docs:
            context_parts.append(f"- {doc['content']}")
            if doc["source"] not in sources:
                sources.append(doc["source"])
        
        context = "\n".join(context_parts)
        
        # RAG 강화 프롬프트 구성
        system_prompt = f"""당신은 {age}세 아이를 위한 동화 작가입니다.
아래 참조 정보를 반드시 활용하여 사실에 기반한 이야기를 만들어주세요.

## 참조 정보 (이 정보에 기반하여 작성하세요):
{context}

## 중요 지침:
1. 참조 정보에 있는 사실만 사용하세요
2. 확실하지 않은 정보는 포함하지 마세요
3. 아이의 나이({age}세)에 맞는 어휘와 문장 길이를 사용하세요
4. 폭력적이거나 무서운 내용은 피하세요
5. 긍정적인 메시지와 교훈을 담아주세요
"""
        
        user_prompt = f"""주제: {', '.join(preferences) if preferences else query}
학습 목표: {learning_goal or '재미있고 교훈적인 이야기'}

위 주제로 짧은 동화를 만들어주세요. 참조 정보에 있는 사실들을 자연스럽게 녹여주세요."""

        # OpenAI API 호출
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
        
        # 신뢰도 점수 계산 (검색된 문서의 유사도 기반)
        if retrieved_docs:
            avg_distance = sum(d["distance"] or 0 for d in retrieved_docs) / len(retrieved_docs)
            # distance가 낮을수록 유사도가 높음 (0~2 범위를 0~1로 변환)
            confidence_score = max(0, min(1, 1 - (avg_distance / 2)))
        else:
            confidence_score = 0.5  # 참조 문서 없을 경우 기본값
        
        return {
            "story": story,
            "sources": sources,
            "fact_checked": len(retrieved_docs) > 0,
            "confidence_score": round(confidence_score, 2)
        }
    
    def fact_check(self, statement: str, threshold: float = 0.5) -> dict:
        """
        문장의 사실 여부 확인
        
        Args:
            statement: 확인할 문장
            threshold: 유사도 임계값
        
        Returns:
            검증 결과
        """
        results = self.retrieve(statement, n_results=1)
        
        if not results:
            return {
                "verified": False,
                "confidence": 0.0,
                "source": None,
                "message": "관련 정보를 찾을 수 없습니다."
            }
        
        top_result = results[0]
        distance = top_result["distance"] or 2.0
        confidence = max(0, min(1, 1 - (distance / 2)))
        
        return {
            "verified": confidence >= threshold,
            "confidence": round(confidence, 2),
            "source": top_result["source"],
            "related_content": top_result["content"],
            "message": "검증됨" if confidence >= threshold else "검증되지 않음"
        }


# 전역 RAG 인스턴스
_rag_instance: Optional[RAGSystem] = None


def get_rag_system() -> RAGSystem:
    """RAG 시스템 싱글톤 인스턴스 반환"""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = RAGSystem()
    return _rag_instance
