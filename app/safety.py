"""
Safety & Content Filtering Module
Content filtering for child safety
"""

import re
from typing import Optional


class ContentFilter:
    """Content safety filter for children"""
    
    # List of inappropriate words (examples)
    INAPPROPRIATE_WORDS = [
        "kill", "murder", "violence", "blood", "scary", "horror",
        "alcohol", "cigarette", "drug", "gun", "knife"
    ]
    
    # Blocked topics
    BLOCKED_TOPICS = [
        "war", "crime", "drugs", "adult"
    ]
    
    @classmethod
    def is_safe(cls, text: str) -> tuple[bool, Optional[str]]:
        """
        Check if text is safe for children
        
        Args:
            text: Text to check
        
        Returns:
            (safety status, issue description or None)
        """
        text_lower = text.lower()
        
        # Check for inappropriate words
        for word in cls.INAPPROPRIATE_WORDS:
            if word in text_lower:
                return False, f"Inappropriate word detected: '{word}'"
        
        # Check for blocked topics
        for topic in cls.BLOCKED_TOPICS:
            if topic in text_lower:
                return False, f"Inappropriate topic detected: '{topic}'"
        
        return True, None
    
    @classmethod
    def sanitize(cls, text: str) -> str:
        """
        Remove/soften inappropriate content from text
        
        Args:
            text: Text to sanitize
        
        Returns:
            Sanitized text
        """
        result = text
        
        # Replace inappropriate words with softened expressions
        replacements = {
            "kill": "defeat",
            "murder": "stop",
            "violence": "adventure",
            "scary": "mysterious",
            "horror": "suspense"
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
        Check if content is appropriate for the target age
        
        Args:
            text: Text to check
            age: Target age
        
        Returns:
            Appropriateness evaluation result
        """
        # Sentence complexity analysis (simple heuristic)
        sentences = re.split(r'[.!?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return {"appropriate": True, "suggestions": []}
        
        avg_sentence_length = sum(len(s) for s in sentences) / len(sentences)
        
        suggestions = []
        
        # Recommended sentence length by age
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
                f"Sentences may be too long for a {age}-year-old. "
                f"Average sentence length: {avg_sentence_length:.0f} chars, "
                f"recommended: {max_recommended_length} chars or less"
            )
        
        # Safety check
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
