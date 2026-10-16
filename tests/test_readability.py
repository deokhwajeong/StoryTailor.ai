import pytest

from storytailor.readability import count_syllables, estimate, fk_grade, grade_to_level


@pytest.mark.parametrize("word,expected", [
    ("cat", 1), ("the", 1), ("happy", 2), ("rabbit", 2), ("jumped", 1), ("octopus", 3), ("library", 3),
])
def test_count_syllables(word, expected):
    assert count_syllables(word) == expected


def test_grade_to_level_endpoints_and_interpolation():
    assert grade_to_level(-1) == 100
    assert grade_to_level(0) == 100
    assert grade_to_level(3) == 640
    assert grade_to_level(2.5) == 570          # halfway between 500 (grade 2) and 640 (grade 3)
    assert grade_to_level(11) == 1160          # 10 -> 1120 and 12 -> 1200
    assert grade_to_level(18) == 1200          # capped at the top band


def test_grade_to_level_is_monotonic():
    levels = [grade_to_level(g / 4) for g in range(0, 60)]
    assert levels == sorted(levels)


def test_empty_text_is_lowest_band():
    assert estimate("") == {"fk_grade": 0.0, "approx_level": 100, "words": 0, "sentences": 1,
                            "method": "flesch-kincaid, mapped to approximate Lexile-style band"}


def test_fk_grade_counts_words_and_sentences():
    grade, words, sentences = fk_grade("The cat sat on the mat. It was happy! Was it?")
    assert (words, sentences) == (11, 3)
    assert grade < 2


def test_longer_sentences_read_harder_with_same_words():
    short = "The owl flew. The owl saw the moon. The owl went home."
    long_ = "The owl flew and the owl saw the moon and the owl went home."
    assert estimate(long_)["approx_level"] > estimate(short)["approx_level"]


def test_readability_endpoint_does_not_store(client):
    resp = client.post("/api/readability", json={"text": "The cat sat. The dog ran."})
    assert resp.status_code == 200
    assert resp.get_json()["approx_level"] < 300
