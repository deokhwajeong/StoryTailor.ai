# StoryTailor.ai


StoryTailor.ai는 아동 친화적 AI 스토리텔링 및 리딩 플랫폼 연구 프로젝트입니다. OpenAI 기반 생성형 AI와 머신러닝을 활용해, 아동의 리딩레벨(예: 렉사일), 선호, 학습 목표에 맞춘 맞춤형 이야기 생성, 리딩 진단, 도서 추천, 읽기 연습, 음성 읽어주기, 분석 리포트 제공까지 지원합니다.

## 주요 특징
- **생성형 AI 기반 이야기 생성**: 연령, 리딩레벨, 선호, 학습 목표에 맞춘 맞춤형 스토리 생성
- **리딩레벨/렉사일 진단**: 아동의 읽기 실력(리딩레벨, 렉사일 등) 자동 진단 및 추적
- **AI 도서 추천**: 진단 결과와 선호 기반 AI 추천 도서 목록 제공
- **읽기 연습 및 음성 읽어주기**: AI가 추천 도서를 읽어주고, 아동의 읽기 연습을 지원(음성 인식 연동 가능)
- **분석 리포트**: 읽기 습관, 성장 추이, 추천 이력 등 상세 리포트 자동 생성
- **내러티브 구조 분석**: 다양한 이야기 구조와 플롯을 자동 탐색 및 적용
- **접근성 및 안전성**: 유해 콘텐츠 필터링, 연령별 안전 가이드라인 내장

# StoryTailor.ai

StoryTailor.ai is a research-driven project focused on generative AI applications for child-safe storytelling and reading platforms. It leverages OpenAI-based generative AI and machine learning to provide personalized story generation, reading diagnostics, book recommendations, reading practice, voice reading, and analytics reports tailored to children's reading levels, preferences, and learning goals.

## Key Features
- **Generative AI Storytelling**: Create personalized stories based on age, reading level, preferences, and learning goals
- **Reading Level Diagnostics**: Automatically assess and track children's reading skills (e.g., Lexile)
- **AI Book Recommendations**: Suggest books based on diagnostics and preferences
- **Reading Practice & Voice Reading**: Support reading practice and voice reading (with speech recognition integration)
- **Analytics Reports**: Generate detailed reports on reading habits, progress, and recommendations
- **Narrative Structure Analysis**: Explore and apply various story structures and plots
- **Accessibility & Safety**: Built-in content filtering and age-appropriate safety guidelines
- **ML-based Personalization**: Continuous personalization based on feedback, interactions, and reading data

## Tech Stack
- Python 3.10+
- PyTorch (or TensorFlow)
- OpenAI API (GPT series)
- FastAPI (RESTful API server)
- Pydantic (data validation)
- pytest (testing)
- (Optional) SpeechRecognition, TTS for voice features

## Installation & Usage
```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload
```

## Project Structure
```
StoryTailor.ai/
├── app/
│   ├── main.py             # FastAPI entry point & API routing
│   ├── schemas.py          # Data models & validation
│   ├── story_engine.py     # Story generation, recommendation, reading engine
│   ├── personalization.py  # Reading diagnostics, personalized recommendations
│   ├── safety.py           # Safety/filtering module
│   └── report.py           # Analytics report module
├── tests/
│   └── test_story.py       # Main feature tests
├── requirements.txt        # Dependencies
└── README.md               # Project introduction (this file)
```

## Example API
```http
POST /diagnose_reading_level
{
  "user_id": "child01",
  "reading_sample": "Once upon a time..."
}

POST /recommend_books
{
  "user_id": "child01",
  "reading_level": 420,
  "preferences": ["animals", "adventure"]
}

POST /generate_story
{
  "age": 7,
  "reading_level": 420,
  "preferences": ["animals", "adventure"],
  "learning_goal": "value of friendship"
}

POST /reading_practice
{
  "user_id": "child01",
  "book_id": "book123",
  "practice_text": "The fox ran fast."
}

GET /report/{user_id}
```

## Contributing
PRs and issues are welcome! We encourage participation from those interested in child safety, AI ethics, and reading education.
## Project Structure
