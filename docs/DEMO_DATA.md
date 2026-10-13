# Demo Data

StoryTailor ships with no student data. To explore the teacher and student
flows, load **synthetic** classrooms. Nothing here is a classroom result,
assessment, or evidence of learning outcomes.

## Generated demo (default)

```bash
flask --app storytailor seed-demo --seed 2026
```

Creates one demo teacher, 8 classrooms (grades 2-5, two per grade, named
"Demo · Grade N · Room 10x"), 25 pseudonymous students per classroom, and a
few reading-log entries per student drawn from each student's level band.
Target levels are randomized around a grade default; they are test inputs,
not norms.

## Importing a synthetic dataset file

```bash
flask --app storytailor seed-demo --from-file synthetic_dataset.json
```

The importer accepts this shape and **refuses** any file whose
`metadata.is_synthetic` is not `true`:

```json
{
  "metadata": {"is_synthetic": true},
  "classrooms": [{"classroom_id": "CLS-001", "grade": 2, "display_name": "Grade 2 · Room 101"}],
  "books": [{"book_id": "BOOK-001", "title_original": "Diary of a Worm"}],
  "students": [{"student_id": "STU-001", "classroom_id": "CLS-001", "grade": 2,
                "lexile": 590, "interest_tags": ["animals", "humor"]}],
  "reading_sessions": [{"student_id": "STU-001", "book_id": "BOOK-001", "date": "2026-09-16",
                        "reading_minutes": 8, "status": "completed", "student_rating": 3}]
}
```

On import:

- Source student IDs and any `display_name` are discarded. Each student gets a
  fresh `stu_...` pseudonym and access code, same as a real account.
- `lexile: null` (not assessed) falls back to the grade default level.
- Interest tags outside the app's tag set are dropped.
- Books are matched to the catalog by title; sessions for unknown books are skipped and counted.

Access codes are written to `instance/demo_access_codes.csv` (git-ignored).
