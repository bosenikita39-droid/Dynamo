"""HTTP contracts. All assessments are research-only; no clinical cutoffs."""
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    recording_id: str = Field(min_length=1, max_length=80)
    start_s: float = Field(default=0, ge=0)
    duration_s: float = Field(default=10, ge=5, le=60)
    noise_percent: float = Field(default=0, ge=0, le=100)
    noise_seed: int = Field(default=42, ge=0, le=2**31 - 1)


class EvaluationRequest(BaseModel):
    recording_id: str = Field(min_length=1, max_length=80)
    start_s: float = Field(default=0, ge=0)
    duration_s: float = Field(default=10, ge=5, le=30)
    noise_seed: int = Field(default=42, ge=0, le=2**31 - 1)
