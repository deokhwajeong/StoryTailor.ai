# StoryTailor

**A personalized reading platform for elementary classrooms.** Students get short,
original stories pitched at their own reading level and built around what they
care about. Teachers see how the class is responding. Student data stays
minimal, pseudonymous, and under the school's control.

Python · Flask · OpenAI API · SQLite · React + Vite

## Background

StoryTailor came out of classroom volunteering in the Cupertino Union School
District. In 2026 the platform was piloted with 200+ students and teachers,
and the design was iterated on feedback from those classrooms.

That experience shaped three priorities:

1. **Fit the reader.** A story is only useful if a child can read it. Every
   story is measured after generation and regenerated if it misses the target.
2. **Close the loop.** One tap ("too easy / just right / too hard") from a
   student, or a flag from a teacher, changes the next story.
3. **Treat student data as the school's.** No names, no ads, export and
   delete on request, retention by default. See [docs/PRIVACY.md](docs/PRIVACY.md).

No student data from the pilot is included in this repository.

## How it works

```
 student types a topic
          |
          v
  PII redaction  ---->  audit log (kinds removed, never values)
          |
          v
  safety check (topic) ---- blocked? -> friendly 422
          |
          v
  retrieve grounding facts (BM25 over curated knowledge base)
          |
          v
  prompt = grade + target level + interests + avoid-topics + facts
          |
          v
  OpenAI chat completion (store=False, no student identifier)
          |
          v
  soften wording -> measure readability -> too hard? regenerate once with SIMPLIFY
          |
          v
  safety check (story + moderation API) -> save -> return story with sources
          |
          v
  student / teacher feedback -> adjust target level, add avoid-topics
          |
          v
  teacher dashboard: difficulty fit, ratings, flagged stories, level spread
```

| Module | Responsibility |
|---|---|
| `storytailor/personalization.py` | Prompt building, level-fit retry loop, feedback-driven level adjustment |
| `storytailor/privacy.py` | PII redaction, pseudonyms, keyed hashing, export, delete, retention purge, audit |
| `storytailor/knowledge.py` | BM25 retrieval over `data/knowledge.json` so real-world facts in stories are grounded |
| `storytailor/readability.py` | Flesch-Kincaid grade mapped to an approximate Lexile-style band |
| `storytailor/safety.py` | Word-boundary blocklist and wording softener (plus provider moderation) |
| `storytailor/llm.py` | OpenAI provider and an offline deterministic provider for demos and zero-egress use |
| `storytailor/routes/` | Flask blueprints: classroom, stories, privacy, public utilities |
| `frontend/frontend/` | Student app (React + TypeScript + Tailwind) |

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # add OPENAI_API_KEY, or set STORYTAILOR_LLM_PROVIDER=offline

flask --app storytailor init-db
flask --app storytailor create-teacher "Room 12"     # prints a teacher token once
flask --app storytailor run
```

```bash
TOKEN=...   # from create-teacher

# Teacher: create a class and 25 pseudonymous student accounts
curl -X POST localhost:5000/api/classrooms -H "Authorization: Bearer $TOKEN" \
     -H 'Content-Type: application/json' -d '{"name": "Grade 3", "grade": 3}'
curl -X POST localhost:5000/api/classrooms/1/students -H "Authorization: Bearer $TOKEN" \
     -H 'Content-Type: application/json' -d '{"count": 25, "interests": ["ocean", "space"]}'

# Student: ask for a story with the access code from the printed roster
curl -X POST localhost:5000/api/stories -H "X-Student-Code: K7QM3XPA" \
     -H 'Content-Type: application/json' -d '{"topic": "an octopus who loves puzzles", "learning_goal": "keep trying"}'
```

Front end:

```bash
cd frontend/frontend && npm install && npm run dev
```

## API

| Method | Path | Who | Purpose |
|---|---|---|---|
| POST | `/api/classrooms` | teacher | Create a classroom |
| POST | `/api/classrooms/<id>/students` | teacher | Create pseudonymous accounts; access codes returned once |
| GET | `/api/classrooms/<id>/students` | teacher | Roster by pseudonym, level, activity |
| GET | `/api/classrooms/<id>/feedback-summary` | teacher | Difficulty fit, ratings, flags, level spread |
| POST | `/api/stories` | student | Generate a personalized, grounded, leveled story |
| GET | `/api/stories` | student | My recent stories |
| POST | `/api/stories/<id>/feedback` | student | Rating, difficulty vote, or flag |
| POST | `/api/stories/<id>/teacher-feedback` | teacher | Teacher review of a student's story |
| GET | `/api/students/<id>/export` | teacher | Everything stored about a student (records request) |
| DELETE | `/api/students/<id>` | teacher | Hard delete |
| POST | `/api/students/<id>/consent` | teacher | `school_authorized` / `pending` / `withdrawn` |
| GET | `/api/students/<id>/audit` | teacher | Access history for a student record |
| POST | `/api/readability` | anyone | Estimate the level of a passage (not stored) |
| GET | `/api/knowledge/search?q=` | anyone | Inspect grounding facts |

## Tests

```bash
pytest -q
```

The suite runs fully offline. It covers the level-fit retry, feedback-driven
level changes, PII redaction (including checking that nothing identifying
reaches the model prompt), cross-teacher access isolation, export, delete,
consent withdrawal, and retention purge.

## Design notes

- **Why Flask and SQLite.** A school pilot needs something a single volunteer
  can deploy and a district IT reviewer can read end to end. One process, one
  file database the district owns, no external services besides the model API.
- **Why BM25 instead of a vector DB.** The grounding corpus is small and
  curated by hand for accuracy. Lexical retrieval is transparent, testable,
  and runs offline. Swapping in embeddings is a contained change in `knowledge.py`.
- **Why measure after generating.** Asking a model for "grade 2 vocabulary"
  is not reliable on its own. Measuring the output and retrying once with a
  simplification instruction keeps stories near the target without a long loop.
- **Reading levels are approximate.** The Lexile-style number is mapped from
  Flesch-Kincaid grade and is meant for relative adjustment, not as an
  official Lexile measure.

## Roadmap

- Read-aloud (TTS) and fluency practice with on-device speech recognition
- Teacher web dashboard (currently JSON endpoints)
- Spanish and Korean story output for multilingual classrooms
- Teacher-editable knowledge base with review workflow

## License

MIT. See [LICENSE](LICENSE).
