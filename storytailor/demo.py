"""Synthetic demo data.

Everything this module creates is fictional and labeled "Demo" so it can never
be mistaken for classroom results. Two sources:

- generate(): a seeded generator (default: 8 classrooms, grades 2-5, 25 students each)
- load_file(): imports a synthetic dataset JSON (schema in docs/DEMO_DATA.md).
  It refuses any file whose metadata is not marked is_synthetic, so this path
  can never be used to import real student records, and it drops display names.
"""

import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

from . import books
from .db import get_db, utcnow
from .personalization import default_level
from .privacy import audit, hash_access_code, hash_secret, new_access_code, new_pseudonym, new_teacher_token

TAGS = ["animals", "science", "fantasy", "humor", "sports", "mystery", "community", "adventure"]


class NotSynthetic(ValueError):
    pass


def _teacher(db, name: str) -> tuple[int, str]:
    token = new_teacher_token()
    cur = db.execute("INSERT INTO teachers (display_name, token_hash, created_at) VALUES (?, ?, ?)",
                     (name, hash_secret(token), utcnow()))
    return cur.lastrowid, token


def _classroom(db, teacher_id: int, name: str, grade: int) -> int:
    return db.execute("INSERT INTO classrooms (teacher_id, name, grade, created_at) VALUES (?, ?, ?, ?)",
                      (teacher_id, f"Demo · {name}", grade, utcnow())).lastrowid


def _student(db, classroom_id: int, grade: int, level: int, interests: list[str]) -> tuple[str, str]:
    sid, code = new_pseudonym(), new_access_code()
    db.execute(
        "INSERT INTO students (id, classroom_id, access_code_hash, grade, target_level, interests, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (sid, classroom_id, hash_access_code(code), grade, level, json.dumps(interests), utcnow()),
    )
    return sid, code


def _log(db, sid: str, book_id: str, minutes: int, completed: bool, rating: int | None, day: str) -> None:
    db.execute(
        "INSERT INTO reading_log (student_id, book_id, minutes, completed, rating, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (sid, book_id, minutes, int(completed), rating, f"{day}T15:00:00+00:00"),
    )


def _write_codes(rows: list[dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["classroom", "student_id", "access_code"])
        w.writeheader()
        w.writerows(rows)


def generate(out: Path, seed: int = 2026, classrooms: int = 8, per_class: int = 25) -> dict:
    rng = random.Random(seed)
    db = get_db()
    teacher_id, token = _teacher(db, "Demo Teacher")
    codes, sessions = [], 0
    for c in range(classrooms):
        grade = 2 + c * 4 // classrooms
        name = f"Grade {grade} · Room {101 + c}"
        cid = _classroom(db, teacher_id, name, grade)
        for _ in range(per_class):
            level = max(100, min(1300, default_level(grade) + rng.randint(-150, 150) // 10 * 10))
            sid, code = _student(db, cid, grade, level, rng.sample(TAGS, 3))
            codes.append({"classroom": name, "student_id": sid, "access_code": code})
            for book in rng.sample(books.recommend(level, [], set(), k=12), rng.randint(0, 4)):
                day = (date(2026, 9, 1) + timedelta(days=rng.randint(0, 40))).isoformat()
                _log(db, sid, book["id"], rng.randint(5, 30), rng.random() > 0.15, rng.randint(2, 5), day)
                sessions += 1
            audit("system", "seed_demo", sid, "synthetic")
    db.commit()
    _write_codes(codes, out)
    return {"teacher_token": token, "classrooms": classrooms, "students": len(codes), "reading_sessions": sessions}


def load_file(path: Path, out: Path) -> dict:
    data = json.loads(Path(path).read_text())
    if data.get("metadata", {}).get("is_synthetic") is not True:
        raise NotSynthetic("Refusing to import: metadata.is_synthetic must be true. "
                           "Real student records are never loaded through the demo path.")

    title_to_id = {b["title"].lower(): b["id"] for b in books.catalog()}
    src_books = {b["book_id"]: title_to_id.get(b.get("title_original", "").strip().lower())
                 for b in data.get("books", [])}

    db = get_db()
    teacher_id, token = _teacher(db, "Demo Teacher")
    rooms, students, codes = {}, {}, []
    for room in data["classrooms"]:
        rooms[room["classroom_id"]] = (
            _classroom(db, teacher_id, room.get("display_name") or room["classroom_id"], room["grade"]),
            room.get("display_name") or room["classroom_id"], room["grade"],
        )
    for s in data["students"]:  # display_name is intentionally ignored
        cid, room_name, grade = rooms[s["classroom_id"]]
        level = s["lexile"] if isinstance(s.get("lexile"), int) else default_level(grade)
        sid, code = _student(db, cid, grade, level, [t for t in s.get("interest_tags", []) if t in TAGS][:5])
        students[s["student_id"]] = sid
        codes.append({"classroom": room_name, "student_id": sid, "access_code": code})
        audit("system", "seed_demo", sid, "synthetic file import")
    sessions = skipped = 0
    for r in data.get("reading_sessions", []):
        book_id = src_books.get(r["book_id"])
        if r["student_id"] not in students or book_id is None:
            skipped += 1
            continue
        rating = r.get("student_rating") if isinstance(r.get("student_rating"), int) else None
        _log(db, students[r["student_id"]], book_id, max(1, min(240, r.get("reading_minutes") or 1)),
             r.get("status") == "completed", rating, r.get("date", "2026-09-01"))
        sessions += 1
    db.commit()
    _write_codes(codes, out)
    return {"teacher_token": token, "classrooms": len(rooms), "students": len(students),
            "reading_sessions": sessions, "skipped_sessions": skipped}
