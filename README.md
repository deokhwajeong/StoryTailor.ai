

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
