

# StoryTailor.ai

StoryTailor.ai is a research-driven project focused on generative AI applications for child-safe storytelling and reading platforms. It leverages OpenAI-based generative AI and machine learning to provide personalized story generation, reading diagnostics, book recommendations, reading practice, voice reading, and analytics reports tailored to children's reading levels, preferences, and learning goals.

## Key Features
- **Generative AI Storytelling**: Create personalized stories based on age, reading level, preferences, and learning goals
- **🆕 RAG-based Hallucination Prevention**: Fact-based story generation using Retrieval Augmented Generation
- **Reading Level Diagnostics**: Automatically assess and track children's reading skills (e.g., Lexile)
- **AI Book Recommendations**: Suggest books based on diagnostics and preferences
- **Reading Practice & Voice Reading**: Support reading practice and voice reading (with speech recognition integration)
- **Analytics Reports**: Generate detailed reports on reading habits, progress, and recommendations
- **Narrative Structure Analysis**: Explore and apply various story structures and plots
- **Accessibility & Safety**: Built-in content filtering and age-appropriate safety guidelines
- **ML-based Personalization**: Continuous personalization based on feedback, interactions, and reading data

## RAG (Retrieval Augmented Generation) - Hallucination Prevention

### What is RAG?
RAG (Retrieval Augmented Generation) is a technology to **prevent hallucinations** in LLMs. It prevents LLMs from generating information they haven't learned and generates responses based on verified information.

### How It Works
```
1. User Request → 2. Knowledge Base Search → 3. Relevant Doc Extraction → 4. Context + LLM → 5. Fact-based Response
       ↓                      ↓                         ↓                        ↓                    ↓
  "Brave Rabbit"      ChromaDB Search         Courage, Rabbit Info      Prompt Enhancement    Verified Story
```

### Key Features
1. **Knowledge Base Management**: Vector database using ChromaDB
2. **Semantic Search**: Semantically search for information related to user requests
3. **Context Injection**: Include retrieved information in LLM prompts
4. **Fact Checking**: Verify that generated content matches the knowledge base
5. **Source Tracking**: Provide sources of referenced information
6. **Confidence Score**: Provide numerical confidence scores for generated content

### Usage Example
```python
from app.rag import get_rag_system

# Initialize RAG system
rag = get_rag_system()

# Add knowledge
rag.add_documents(
    documents=["Rabbits can run up to 70 km/h."],
    sources=["Animal Encyclopedia"]
)

# Search for relevant information
results = rag.retrieve("fast rabbit", n_results=3)

# Fact check
fact_result = rag.fact_check("Rabbits can run fast")
print(fact_result)  # {"verified": True, "confidence": 0.85, ...}
```

### RAG vs Standard LLM Comparison
| Category | Standard LLM | With RAG |
|----------|-------------|----------|
| Hallucination | High | Low |
| Factual Accuracy | Medium | High |
| Source Provided | ❌ | ✅ |
| Verifiability | ❌ | ✅ |
| Latest Information | ❌ (Limited to training data) | ✅ (Knowledge base updates) |

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

### API Documentation
After starting the server, you can view the API documentation via Swagger UI at http://localhost:8000/docs.

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
  "use_rag": true  // Use RAG to prevent hallucinations
}

Response:
{
  "story": "Once upon a time, a brave rabbit...",
  "sources": ["Child Education Principles", "Animal Encyclopedia"],  // Reference sources
  "fact_checked": true,
  "confidence_score": 0.87  // Confidence score
}

POST /rag/fact_check
{
  "statement": "Rabbits can run at 70 km/h"
}

Response:
{
  "verified": true,
  "confidence": 0.85,
  "source": "Animal Encyclopedia",
  "message": "Verified"
}

GET /rag/search?query=brave+rabbit&n_results=3
```

## Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_rag.py -v
```

## Project Roadmap

Track project progress and roadmap on [GitHub Projects](https://github.com/deokhwajeong/StoryTailor.ai/projects).

### Current Progress
- [x] Core story generation engine
- [x] RAG-based hallucination prevention system
- [x] FastAPI server setup
- [x] Safety filtering module
- [ ] Voice reading features (TTS/STT)
- [ ] Reading level diagnostics
- [ ] AI book recommendation engine
- [ ] Analytics report dashboard
- [ ] Frontend UI completion

### Future Plans
1. **Phase 1**: Core feature stabilization and test enhancement
2. **Phase 2**: Voice features and reading diagnostics system development
3. **Phase 3**: Personalized recommendation engine and analytics expansion
4. **Phase 4**: Frontend completion and user feedback integration

## Contributing
PRs and issues are welcome! We encourage participation from those interested in child safety, AI ethics, and reading education.

## License
MIT License - See [LICENSE](LICENSE) for details.
