from typing import Any, List, Optional

from pydantic import BaseModel


class EvaluationOut(BaseModel):
    candidate_id: str
    name: Optional[str] = None
    role: Optional[str] = None
    label: str
    overall_score: float
    technical_score: float
    communication_score: float
    skill_coverage: float
    strengths: List[str]
    weaknesses: List[str]
    summary: str
    explanation: List[str]
    breakdown: dict[str, Any]