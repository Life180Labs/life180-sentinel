import uuid
from datetime import datetime

from pydantic import BaseModel


class CategoryEvaluationResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    category: str
    score: int
    findings: list[str]
    recommendations: list[str]
    summary: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EvaluationSummaryResponse(BaseModel):
    repository_id: uuid.UUID
    overall_score: int
    categories: list[CategoryEvaluationResponse]
