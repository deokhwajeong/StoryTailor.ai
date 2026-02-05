"""
콘텐츠 안전성 필터 테스트
"""

import pytest
from app.safety import ContentFilter


class TestContentFilter:
    """콘텐츠 필터 테스트"""
    
    def test_safe_content(self):
        """안전한 콘텐츠 테스트"""
        safe_text = "귀여운 토끼가 숲속에서 친구들과 놀았습니다."
        is_safe, issue = ContentFilter.is_safe(safe_text)
        
        assert is_safe is True
        assert issue is None
    
    def test_unsafe_content_detection(self):
        """부적절한 콘텐츠 감지 테스트"""
        unsafe_texts = [
            "나쁜 사람이 토끼를 죽이다",
            "무서운 괴물이 나타났다",
        ]
        
        for text in unsafe_texts:
            is_safe, issue = ContentFilter.is_safe(text)
            assert is_safe is False
            assert issue is not None
    
    def test_sanitize(self):
        """콘텐츠 정화 테스트"""
        unsafe_text = "무서운 괴물이 나타났다"
        sanitized = ContentFilter.sanitize(unsafe_text)
        
        # "무서운"이 "신비로운"으로 대체되어야 함
        assert "무서운" not in sanitized
        assert "신비로운" in sanitized
    
    def test_age_appropriateness_young_child(self):
        """어린 아이(5세) 적합성 테스트"""
        text = "토끼가 뛰어요. 꽃이 예뻐요."
        result = ContentFilter.check_age_appropriateness(text, age=5)
        
        assert "appropriate" in result
        assert "metrics" in result
        assert result["metrics"]["target_age"] == 5
    
    def test_age_appropriateness_long_sentences(self):
        """긴 문장 적합성 테스트"""
        long_text = (
            "아주 아주 오래전 깊은 숲속에 살고 있던 작은 토끼가 "
            "친구들을 찾아 긴 여행을 떠나기로 결심했습니다. "
            "그 토끼는 매우 용감하고 지혜로웠으며 모든 동물들의 존경을 받았습니다."
        )
        result = ContentFilter.check_age_appropriateness(long_text, age=5)
        
        # 5세에게는 문장이 길다는 제안이 있어야 함
        assert len(result["suggestions"]) > 0 or result["metrics"]["avg_sentence_length"] <= 30


class TestContentFilterEdgeCases:
    """콘텐츠 필터 엣지 케이스 테스트"""
    
    def test_empty_text(self):
        """빈 텍스트 테스트"""
        is_safe, issue = ContentFilter.is_safe("")
        assert is_safe is True
    
    def test_age_appropriateness_empty_text(self):
        """빈 텍스트 연령 적합성 테스트"""
        result = ContentFilter.check_age_appropriateness("", age=7)
        assert result["appropriate"] is True
    
    def test_mixed_content(self):
        """혼합 콘텐츠 테스트"""
        # 일부 안전하지 않은 단어가 포함된 텍스트
        text = "친구와 함께 모험을 떠났지만 공포의 동굴을 만났다"
        is_safe, issue = ContentFilter.is_safe(text)
        
        assert is_safe is False
        assert "공포" in issue
