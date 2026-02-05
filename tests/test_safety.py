"""
Content Safety Filter Tests
"""

import pytest
from app.safety import ContentFilter


class TestContentFilter:
    """Content Filter Tests"""
    
    def test_safe_content(self):
        """Safe content test"""
        safe_text = "A cute rabbit played with friends in the forest."
        is_safe, issue = ContentFilter.is_safe(safe_text)
        
        assert is_safe is True
        assert issue is None
    
    def test_unsafe_content_detection(self):
        """Inappropriate content detection test"""
        unsafe_texts = [
            "The bad person tried to kill the rabbit",
            "A scary monster appeared",
        ]
        
        for text in unsafe_texts:
            is_safe, issue = ContentFilter.is_safe(text)
            assert is_safe is False
            assert issue is not None
    
    def test_sanitize(self):
        """Content sanitization test"""
        unsafe_text = "A scary monster appeared"
        sanitized = ContentFilter.sanitize(unsafe_text)
        
        # "scary" should be replaced with "mysterious"
        assert "scary" not in sanitized
        assert "mysterious" in sanitized
    
    def test_age_appropriateness_young_child(self):
        """Young child (5 years) appropriateness test"""
        text = "The rabbit jumps. The flower is pretty."
        result = ContentFilter.check_age_appropriateness(text, age=5)
        
        assert "appropriate" in result
        assert "metrics" in result
        assert result["metrics"]["target_age"] == 5
    
    def test_age_appropriateness_long_sentences(self):
        """Long sentence appropriateness test"""
        long_text = (
            "A very long time ago, a small rabbit living deep in the forest "
            "decided to embark on a long journey to find friends. "
            "The rabbit was very brave and wise, earning the respect of all animals."
        )
        result = ContentFilter.check_age_appropriateness(long_text, age=5)
        
        # For 5-year-olds, there should be suggestions about long sentences
        assert len(result["suggestions"]) > 0 or result["metrics"]["avg_sentence_length"] <= 30


class TestContentFilterEdgeCases:
    """Content Filter Edge Case Tests"""
    
    def test_empty_text(self):
        """Empty text test"""
        is_safe, issue = ContentFilter.is_safe("")
        assert is_safe is True
    
    def test_age_appropriateness_empty_text(self):
        """Empty text age appropriateness test"""
        result = ContentFilter.check_age_appropriateness("", age=7)
        assert result["appropriate"] is True
    
    def test_mixed_content(self):
        """Mixed content test"""
        # Text containing some unsafe words
        text = "They went on an adventure with friends but encountered the cave of horror"
        is_safe, issue = ContentFilter.is_safe(text)
        
        assert is_safe is False
        assert "horror" in issue
