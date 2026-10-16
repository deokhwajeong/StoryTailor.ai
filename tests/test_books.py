import json

import pytest

from storytailor import books, demo
from storytailor.db import get_db


def test_catalog_is_deduplicated_and_clean():
    cat = books.catalog()
    assert len(cat) == 148
    assert all(b["title"] and isinstance(b["lexile"], int) and b["guided_level"] == b["guided_level"].upper()
               for b in cat)
    assert len({(b["title"].lower(), b["lexile"], b["guided_level"]) for b in cat}) == len(cat)


def test_search_substring_and_filters():
    res = books.search("bad kitty", max_lexile=600)
    assert not res["fuzzy"]
    assert res["results"] and all("bad kitty" in b["title"].lower() and b["lexile"] <= 600 for b in res["results"])
    assert all(b["guided_level"] == "N" for b in books.search("", guided_level="n")["results"])


def test_search_fuzzy_fallback_handles_typos():
    res = books.search("wimpy kidd")
    assert res["fuzzy"]
    assert res["results"][0]["title"].startswith("Diary of a Wimpy Kid")
    assert books.search("zzzzqqqq")["results"] == []


def test_recommend_band_interests_and_history():
    recs = books.recommend(550, ["humor"], set(), k=5)
    assert len(recs) == 5
    assert all(450 <= b["lexile"] <= 600 for b in recs)
    assert recs[0]["interest_matches"] == ["humor"]
    read = {recs[0]["id"]}
    assert recs[0]["id"] not in {b["id"] for b in books.recommend(550, ["humor"], read, k=5)}


def test_recommend_widens_band_for_sparse_levels():
    assert len(books.recommend(150, [], set(), k=3)) == 3


def test_recommendation_and_log_endpoints(client, student, teacher, classroom):
    h = student["headers"]
    recs = client.get("/api/books/recommendations", headers=h).get_json()
    assert recs["band"] == [350, 500]
    first = recs["books"][0]["id"]
    assert client.post("/api/books/log", json={"book_id": first, "minutes": 15, "rating": 5},
                       headers=h).status_code == 201
    assert first not in {b["id"] for b in client.get("/api/books/recommendations", headers=h).get_json()["books"]}
    assert client.post("/api/books/log", json={"book_id": "nope"}, headers=h).status_code == 400

    summary = client.get(f"/api/classrooms/{classroom['id']}/feedback-summary", headers=teacher).get_json()
    assert summary["reading"] == {"sessions": 1, "minutes": 15, "readers": 1, "average_rating": 5.0}
    export = client.get(f"/api/students/{student['id']}/export", headers=teacher).get_json()
    assert export["reading_log"][0]["book_id"] == first


def test_public_search_endpoint(client):
    data = client.get("/api/books/search?q=matlida").get_json()
    assert data["fuzzy"] and "Matilda" in data["results"][0]["title"]
    assert client.get("/api/books/search?min_lexile=abc").status_code == 400


def test_generate_demo(app, tmp_path):
    with app.app_context():
        result = demo.generate(tmp_path / "codes.csv", classrooms=2, per_class=5)
        assert result["students"] == 10
        names = [r[0] for r in get_db().execute("SELECT name FROM classrooms WHERE name LIKE 'Demo%'")]
    assert len(names) == 2
    assert (tmp_path / "codes.csv").read_text().count("\n") == 11


def _synthetic_file(tmp_path, synthetic=True):
    data = {
        "metadata": {"is_synthetic": synthetic},
        "classrooms": [{"classroom_id": "CLS-001", "grade": 2, "display_name": "Grade 2 · Room 101"}],
        "books": [{"book_id": "BOOK-1", "title_original": "Diary of a Worm"}],
        "students": [
            {"student_id": "STU-001", "display_name": "Fictional Kid", "classroom_id": "CLS-001", "grade": 2,
             "lexile": None, "interest_tags": ["animals", "not-a-tag"]},
            {"student_id": "STU-002", "display_name": "Another Kid", "classroom_id": "CLS-001", "grade": 2,
             "lexile": 590, "interest_tags": ["humor"]},
        ],
        "reading_sessions": [
            {"student_id": "STU-002", "book_id": "BOOK-1", "date": "2026-09-16", "reading_minutes": 8,
             "status": "completed", "student_rating": 3},
            {"student_id": "STU-002", "book_id": "BOOK-404", "date": "2026-09-17", "reading_minutes": 8},
        ],
    }
    path = tmp_path / "data.json"
    path.write_text(json.dumps(data))
    return path


def test_load_synthetic_file_drops_names(app, tmp_path):
    with app.app_context():
        result = demo.load_file(_synthetic_file(tmp_path), tmp_path / "codes.csv")
        rows = get_db().execute("SELECT * FROM students").fetchall()
        dump = json.dumps([dict(r) for r in rows])
    assert result["students"] == 2 and result["reading_sessions"] == 1 and result["skipped_sessions"] == 1
    assert "Kid" not in dump and "STU-00" not in dump
    assert sorted(r["target_level"] for r in rows) == [450, 590]


def test_load_refuses_non_synthetic(app, tmp_path):
    with app.app_context(), pytest.raises(demo.NotSynthetic):
        demo.load_file(_synthetic_file(tmp_path, synthetic=False), tmp_path / "codes.csv")


def test_catalog_coverage_facts_quoted_in_readme():
    lexiles = [b["lexile"] for b in books.catalog()]
    assert len(lexiles) == 148
    assert sum(500 <= x <= 699 for x in lexiles) == 80
    assert sum(x < 400 for x in lexiles) == 7
    assert sum(x >= 900 for x in lexiles) == 13


def test_class_coverage_counts_titles_and_readers_per_band():
    cov = books.class_coverage([350, 380, 560, 610, 920])
    by_low = {b["low"]: b for b in cov["bands"]}
    assert sum(b["titles"] for b in cov["bands"]) == cov["total_titles"] == 148
    assert by_low[500]["titles"] == 43 and by_low[600]["titles"] == 37
    assert by_low[300] == {"low": 300, "high": 399, "titles": 4, "readers": 2, "thin": True}
    assert by_low[900]["readers"] == 1 and by_low[900]["thin"]
    assert cov["readers_in_thin_bands"] == 3
    assert cov["thin_threshold"] == books.THIN_SHELF


def test_class_coverage_includes_readers_beyond_the_shelf():
    cov = books.class_coverage([1350])
    assert cov["bands"][-1] == {"low": 1300, "high": 1399, "titles": 0, "readers": 1, "thin": True}


def test_shelf_for_reader_uses_the_recommendation_band():
    shelf = books.shelf_for_reader(600)
    assert shelf["band"] == [500, 650]
    assert shelf["titles"] == books.titles_between(500, 650) and not shelf["thin"]
    assert books.shelf_for_reader(300)["thin"]


def test_feedback_summary_includes_library_coverage(client, teacher, classroom, student):
    summary = client.get(f"/api/classrooms/{classroom['id']}/feedback-summary", headers=teacher).get_json()
    cov = summary["library_coverage"]
    assert cov["total_titles"] == 148
    assert sum(b["readers"] for b in cov["bands"]) == 1
