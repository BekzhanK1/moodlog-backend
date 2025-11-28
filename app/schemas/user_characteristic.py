from pydantic import BaseModel
from typing import Optional, List


class EmotionalProfile(BaseModel):
    average_mood: float
    dominant_emotions: List[str]
    emotional_range: str


class WritingStyle(BaseModel):
    average_length: str
    tone: str
    common_patterns: List[str]


class UserCharacteristicResponse(BaseModel):
    general_description: Optional[str] = None
    main_themes: Optional[List[str]] = None
    emotional_profile: Optional[EmotionalProfile] = None
    writing_style: Optional[WritingStyle] = None

    class Config:
        from_attributes = True
