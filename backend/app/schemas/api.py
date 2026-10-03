from typing import Any, Optional
from pydantic import BaseModel, Field


class CandidateCreate(BaseModel):
    candidate_id: str
    name: str
    email: str
    experience_years: float = 0
    domain: str = ""
    education: str = ""
    job_type: str = ""
    skills_text: str = ""
    skills_and_achievements: str = ""


class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    experience_years: Optional[float] = None
    domain: Optional[str] = None
    education: Optional[str] = None
    job_type: Optional[str] = None
    skills_text: Optional[str] = None
    skills_and_achievements: Optional[str] = None


class QuestionCreate(BaseModel):
    question_id: str
    text: str
    difficulty: str = "Medium"
    category: str = "General"
    source_role: str = ""
    keywords: list[str] = Field(default_factory=list)


class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    difficulty: Optional[str] = None
    category: Optional[str] = None
    source_role: Optional[str] = None
    keywords: Optional[list[str]] = None


class SkillCreate(BaseModel):
    skill_id: str
    name: str
    category: str = "General"


class RoleCreate(BaseModel):
    role_id: str
    title: str
    department: str = "General"


class TechnologyCreate(BaseModel):
    tech_id: str
    name: str


class InterviewCreate(BaseModel):
    candidate_id: str
    round_id: str
    question_id: str
    answer: str = ""
    difficulty: str = "Medium"
    target_role: str = "General"
    source_type: str = "Synthetic"
    answer_id: Optional[str] = None


class RawInterviewCreate(BaseModel):
    candidate_id: str
    round_id: str
    question_id: str
    transcript: str
    answer_id: Optional[str] = None
    target_role: str = "General"
    difficulty: str = "Medium"
    domain: str = ""
    source_type: str = "Synthetic"
    emotion_timeline: list[dict[str, Any]] = Field(default_factory=list)


class InterviewUpdate(BaseModel):
    transcript: Optional[str] = None
    emotion_timeline: Optional[list[dict[str, Any]]] = None
    metadata: Optional[dict[str, Any]] = None


class EmotionLogCreate(BaseModel):
    interview_id: str
    candidate_id: str
    round_id: str = ""
    question_id: str = ""
    timestamp: Any = 0
    timestamp_sec: float = 0
    emotion: str
    confidence: float = 0.5


class EvaluationRequest(BaseModel):
    candidate_id: str
    target_role: Optional[str] = None


class CompareRequest(BaseModel):
    candidate_ids: list[str] = Field(min_length=2)
