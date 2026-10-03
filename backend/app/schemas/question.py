from typing import List, Optional

from pydantic import BaseModel, Field


class QuestionCreate(BaseModel):
    question_id: Optional[str] = None
    text: str = Field(min_length=5)
    category: Optional[str] = None
    difficulty: Optional[str] = None
    target_role: Optional[str] = None
    experience: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)


class QuestionUpdate(BaseModel):
    text: Optional[str] = Field(default=None, min_length=5)
    category: Optional[str] = None
    difficulty: Optional[str] = None
    target_role: Optional[str] = None
    experience: Optional[str] = None
    keywords: Optional[List[str]] = None
    skills: Optional[List[str]] = None