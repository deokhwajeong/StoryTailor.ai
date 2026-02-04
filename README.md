

# StoryTailor.ai

StoryTailor.ai is a research-driven project focused on generative AI applications for child-safe storytelling and reading platforms. It leverages OpenAI-based generative AI and machine learning to provide personalized story generation, reading diagnostics, book recommendations, reading practice, voice reading, and analytics reports tailored to children's reading levels, preferences, and learning goals.

## Key Features
- **Generative AI Storytelling**: Create personalized stories based on age, reading level, preferences, and learning goals
- **🆕 RAG 기반 할루시네이션 방지**: Retrieval Augmented Generation으로 사실에 기반한 스토리 생성
- **Reading Level Diagnostics**: Automatically assess and track children's reading skills (e.g., Lexile)
- **AI Book Recommendations**: Suggest books based on diagnostics and preferences
- **Reading Practice & Voice Reading**: Support reading practice and voice reading (with speech recognition integration)
- **Analytics Reports**: Generate detailed reports on reading habits, progress, and recommendations
- **Narrative Structure Analysis**: Explore and apply various story structures and plots
- **Accessibility & Safety**: Built-in content filtering and age-appropriate safety guidelines
- **ML-based Personalization**: Continuous personalization based on feedback, interactions, and reading data

## RAG (Retrieval Augmented Generation) - 할루시네이션 방지

### RAG란?
RAG(Retrieval Augmented Generation)는 LLM의 **할루시네이션(환각)을 방지**하기 위한 기술입니다. LLM이 학습하지 않은 정보를 만들어내는 것을 방지하고, 검증된 정보에 기반한 응답을 생성합니다.

### 작동 원리
```
1. 사용자 요청 → 2. 지식 베이스 검색 → 3. 관련 문서 추출 → 4. 컨텍스트 + LLM → 5. 사실 기반 응답
     ↓                    ↓                    ↓                    ↓                ↓
  "용감한 토끼"      ChromaDB 검색        용기, 토끼 정보      프롬프트 강화      검증된 스토리
```

### 주요 기능
1. **지식 베이스 관리**: ChromaDB를 활용한 벡터 데이터베이스
2. **의미 기반 검색**: 사용자 요청과 관련된 정보를 의미적으로 검색
3. **컨텍스트 주입**: 검색된 정보를 LLM 프롬프트에 포함
4. **팩트 체크**: 생성된 내용이 지식 베이스와 일치하는지 검증
5. **출처 추적**: 참조된 정보의 출처를 함께 제공
6. **신뢰도 점수**: 생성된 콘텐츠의 신뢰도를 수치로 제공

### 사용 예시
```python
from app.rag import get_rag_system

# RAG 시스템 초기화
rag = get_rag_system()

# 지식 추가
rag.add_documents(
    documents=["토끼는 시속 70km로 달릴 수 있습니다."],
    sources=["동물 백과사전"]
)

# 관련 정보 검색
results = rag.retrieve("빠른 토끼", n_results=3)

# 팩트 체크
fact_result = rag.fact_check("토끼는 빠르게 달릴 수 있다")
print(fact_result)  # {"verified": True, "confidence": 0.85, ...}
```

### RAG vs 일반 LLM 비교
| 구분 | 일반 LLM | RAG 적용 |
|------|---------|----------|
| 할루시네이션 | 높음 | 낮음 |
| 사실 정확도 | 중간 | 높음 |
| 출처 제공 | ❌ | ✅ |
| 검증 가능성 | ❌ | ✅ |
| 최신 정보 | ❌ (학습 데이터 한정) | ✅ (지식 베이스 업데이트) |

## Tech Stack
- Python 3.10+
- PyTorch (or TensorFlow)
- OpenAI API (GPT series)
- FastAPI (RESTful API server)
- Pydantic (data validation)
- **ChromaDB** (Vector Database for RAG)
- **LangChain** (LLM Orchestration)
- pytest (testing)
- (Optional) SpeechRecognition, TTS for voice features

## Installation & Usage
```bash
# Install dependencies
pip install -r requirements.txt

# Set OpenAI API Key
export OPENAI_API_KEY="your-api-key-here"

# Run the server
uvicorn app.main:app --reload
```

### API 문서
서버 실행 후 http://localhost:8000/docs 에서 Swagger UI로 API 문서를 확인할 수 있습니다.

## Project Structure
```
StoryTailor.ai/
├── app/
│   ├── __init__.py         # Package initialization
│   ├── main.py             # FastAPI entry point & API routing
│   ├── schemas.py          # Data models & validation (Pydantic)
│   ├── story_engine.py     # Story generation engine (RAG integration)
│   ├── rag.py              # 🆕 RAG system (Hallucination prevention)
│   └── safety.py           # Safety/filtering module
├── tests/
│   ├── test_api.py         # API integration tests
│   ├── test_rag.py         # RAG system unit tests
│   └── test_safety.py      # Safety filter tests
├── frontend/
│   └── frontend/           # React + Vite frontend
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

## Example API
```http
POST /generate_story
{
  "age": 7,
  "reading_level": 420,
  "preferences": ["animals", "adventure"],
  "learning_goal": "value of friendship",
  "use_rag": true  // RAG 사용으로 할루시네이션 방지
}

Response:
{
  "story": "옛날 옛적에 용감한 토끼가...",
  "sources": ["아동 교육 원칙", "동물 백과사전"],  // 참조 출처
  "fact_checked": true,
  "confidence_score": 0.87  // 신뢰도 점수
}

POST /rag/fact_check
{
  "statement": "토끼는 시속 70km로 달릴 수 있다"
}

Response:
{
  "verified": true,
  "confidence": 0.85,
  "source": "동물 백과사전",
  "message": "검증됨"
}

GET /rag/search?query=용감한+토끼&n_results=3
```

## Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_rag.py -v
```

## Contributing
PRs and issues are welcome! We encourage participation from those interested in child safety, AI ethics, and reading education.

## License
MIT License - See [LICENSE](LICENSE) for details.
