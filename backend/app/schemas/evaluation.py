import uuid
from datetime import datetime

from pydantic import BaseModel


class CategoryEvaluationResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    eval_run: int
    category: str
    score: int
    reasoning: str | None
    confidence: int | None
    findings: list[str]
    recommendations: list[str]
    recommendation_scores: list[int] | None
    summary: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EvaluationSummaryResponse(BaseModel):
    repository_id: uuid.UUID
    overall_score: int
    categories: list[CategoryEvaluationResponse]


class EvaluationRunResponse(BaseModel):
    run: int
    overall_score: int
    grade: str
    category_scores: dict[str, int]
    evaluated_at: datetime
