from storytailor import readability, safety
from storytailor.knowledge import default_kb
from storytailor.personalization import adjust_level


def test_safety_uses_word_boundaries():
    assert safety.is_safe("She won an award and walked toward the drugstore")[0] is True
    assert safety.is_safe("The war ended")[1] == ["war"]


def test_soften_preserves_case():
    assert safety.soften("Scary night. It was scary.") == "Mysterious night. It was mysterious."


def test_readability_orders_texts():
    easy = readability.estimate("The cat sat. The dog ran. We had fun.")
    hard = readability.estimate(
        "Photosynthesis transforms electromagnetic radiation into chemical energy, "
        "facilitating carbohydrate biosynthesis within chloroplasts."
    )
    assert easy["approx_level"] < hard["approx_level"]


def test_knowledge_search_ranks_relevant_fact():
    results = default_kb().search("owls at night", k=2)
    assert results[0]["id"] == "animals-owls"


def test_adjust_level():
    assert adjust_level(500, ["too_hard", "too_hard", "just_right"]) == 450
    assert adjust_level(500, ["too_easy", "just_right"]) == 550
    assert adjust_level(500, ["just_right", "just_right"]) == 500
    assert adjust_level(120, ["too_hard"]) == 100
