from typing import List, Optional

from pydantic import BaseModel, Field


class CandidateCreate(BaseModel):
    candidate_id: Optional[str] = None
    name: str = Field(min_length=1)
    email: Optional[str] = None
    education: Optional[str] = None
    domain: Optional[str] = None
    job_type: Optional[str] = None
    experience_years: Optional[float] = Field(default=None, ge=0)
    skills: List[str] = Field(default_factory=list)


class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    education: Optional[str] = None
    domain: Optional[str] = None
    job_type: Optional[str] = None
    experience_years: Optional[float] = Field(default=None, ge=0)
    skills: Optional[List[str]] = None