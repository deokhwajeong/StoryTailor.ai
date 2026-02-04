"""
Safety & Content Filtering Module
아동에게 안전한 콘텐츠 필터링
"""

import re
from typing import Optional


class ContentFilter:
    """아동용 콘텐츠 안전 필터"""
    
    # 부적절한 단어 목록 (예시)
    INAPPROPRIATE_WORDS = [
        "죽이다", "살해", "폭력", "피", "무서운", "공포",
        "술", "담배", "마약", "총", "칼"
    ]
    
    # 허용되지 않는 주제
    BLOCKED_TOPICS = [
        "전쟁", "범죄", "약물", "성인"
    ]
    
    @classmethod
    def is_safe(cls, text: str) -> tuple[bool, Optional[str]]:
        """
        텍스트가 아동에게 안전한지 확인
        
        Args:
            text: 확인할 텍스트
        
        Returns:
            (안전 여부, 문제점 설명 또는 None)
        """
        text_lower = text.lower()
        
        # 부적절한 단어 검사
        for word in cls.INAPPROPRIATE_WORDS:
            if word in text_lower:
                return False, f"부적절한 단어 감지: '{word}'"
        
        # 차단된 주제 검사
        for topic in cls.BLOCKED_TOPICS:
            if topic in text_lower:
                return False, f"부적절한 주제 감지: '{topic}'"
        
        return True, None
    
    @classmethod
    def sanitize(cls, text: str) -> str:
        """
        텍스트에서 부적절한 내용 제거/완화
        
        Args:
            text: 정화할 텍스트
        
        Returns:
            정화된 텍스트
        """
        result = text
        
        # 부적절한 단어를 순화된 표현으로 대체
        replacements = {
            "죽이다": "물리치다",
            "살해": "퇴치",
            "폭력": "모험",
            "무서운": "신비로운",
            "공포": "긴장감"
        }
        
        for bad_word, good_word in replacements.items():
            result = result.replace(bad_word, good_word)
        
        return result
    
    @classmethod
    def check_age_appropriateness(
        cls, 
        text: str, 
        age: int
    ) -> dict:
        """
        연령에 맞는 콘텐츠인지 확인
        
        Args:
            text: 확인할 텍스트
            age: 대상 연령
        
        Returns:
            적합성 평가 결과
        """
        # 문장 복잡도 분석 (간단한 휴리스틱)
        sentences = re.split(r'[.!?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return {"appropriate": True, "suggestions": []}
        
        avg_sentence_length = sum(len(s) for s in sentences) / len(sentences)
        
        suggestions = []
        
        # 연령별 권장 문장 길이
        if age <= 5:
            max_recommended_length = 30
        elif age <= 8:
            max_recommended_length = 50
        elif age <= 12:
            max_recommended_length = 80
        else:
            max_recommended_length = 100
        
        if avg_sentence_length > max_recommended_length:
            suggestions.append(
                f"문장이 {age}세 아이에게 다소 길 수 있습니다. "
                f"평균 문장 길이: {avg_sentence_length:.0f}자, "
                f"권장: {max_recommended_length}자 이하"
            )
        
        # 안전성 검사
        is_safe, issue = cls.is_safe(text)
        if not is_safe:
            suggestions.append(issue)
        
        return {
            "appropriate": is_safe and len(suggestions) <= 1,
            "suggestions": suggestions,
            "metrics": {
                "avg_sentence_length": round(avg_sentence_length, 1),
                "sentence_count": len(sentences),
                "target_age": age
            }
        }
