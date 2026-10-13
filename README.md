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

No student data from the pilot is included in this repository. The demo
classrooms described below are synthetic and are not pilot results.

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
  teacher dashboard: difficulty fit, ratings, flagged stories, level spread, reading minutes
```

### Classroom library

Alongside generated stories, students get **real books from the classroom
library**. The catalog (`storytailor/data/books.json`, 148 titles) comes from
the book list a classroom kept for its digital library search page: title,
Lexile, and guided reading letter level, deduplicated from 155 rows.

- **Recommendations** use the reader's band of 100L below to 50L above their
  target level, rank by interest overlap and closeness to target, skip books
  already read, and widen the band when few books are left at that level.
- **Search** filters by title, letter level, and Lexile range, and falls back
  to fuzzy matching (Levenshtein over title windows) because kids misspell:
  `matlida` finds *Matilda*, `wimpy kidd` finds *Diary of a Wimpy Kid*.
- **Reading log**: "I read it" records the book, feeds the teacher summary,
  and removes it from future recommendations.

Lexile and letter levels are kept as recorded in the classroom list and have
not been re-verified. Topic tags are keyword guesses from titles.

| Module | Responsibility |
|---|---|
| `storytailor/personalization.py` | Prompt building, level-fit retry loop, feedback-driven level adjustment |
| `storytailor/privacy.py` | PII redaction, pseudonyms, keyed hashing, export, delete, retention purge, audit |
| `storytailor/knowledge.py` | BM25 retrieval over `data/knowledge.json` so real-world facts in stories are grounded |
| `storytailor/books.py` | Classroom library catalog, leveled recommendations, fuzzy title search |
| `storytailor/demo.py` | Synthetic demo classrooms (generator, and importer that only accepts files marked synthetic) |
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

Try it with demo classrooms (synthetic, labeled "Demo"):

```bash
flask --app storytailor seed-demo        # 8 classrooms, grades 2-5, 200 fictional pseudonymous students
# or: flask --app storytailor seed-demo --from-file path/to/synthetic_dataset.json
# prints a demo teacher token; student codes go to instance/demo_access_codes.csv
```

See [docs/DEMO_DATA.md](docs/DEMO_DATA.md).

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
| GET | `/api/books/recommendations` | student | Library books in my band, matched to my interests |
| POST | `/api/books/log` | student | Record a book I read |
| GET | `/api/books/search?q=&level=&min_lexile=&max_lexile=` | anyone | Library search with fuzzy fallback |
| POST | `/api/readability` | anyone | Estimate the level of a passage (not stored) |
| GET | `/api/knowledge/search?q=` | anyone | Inspect grounding facts |

## Tests

```bash
pytest -q
```

The suite runs fully offline. It covers the level-fit retry, feedback-driven
level changes, library recommendations and fuzzy search, PII redaction (including checking that nothing identifying
reaches the model prompt), cross-teacher access isolation, export, delete,
consent withdrawal, retention purge, and that the demo importer rejects files
not marked synthetic and drops display names.

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
