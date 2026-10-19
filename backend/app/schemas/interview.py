from typing import List, Optional

from pydantic import BaseModel, Field


class InterviewQA(BaseModel):
    question_id: str
    answer_text: str = Field(min_length=1)
    score: Optional[float] = Field(default=None, ge=0, le=10)


class InterviewCreate(BaseModel):
    candidate_id: str
    round_label: Optional[str] = None
    target_role: Optional[str] = None
    notes: Optional[str] = None
    qa: List[InterviewQA] = Field(min_length=1)

class InterviewAnswerUpdate(BaseModel):
    answer_id: str
    answer_text: str = Field(min_length=1)


class InterviewUpdate(BaseModel):
    target_role: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    answers: Optional[List[InterviewAnswerUpdate]] = None