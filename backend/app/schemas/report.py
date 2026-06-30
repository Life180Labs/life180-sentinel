import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.evaluation import CategoryEvaluationResponse
from app.schemas.intelligence import IntelligenceResponse


class RepositoryScoreResponse(BaseModel):
    repository_id: uuid.UUID
    overall_score: int
    grade: str
    category_scores: dict[str, int]


class ReportResponse(BaseModel):
    repository_id: uuid.UUID
    owner: str
    name: str
    url: str
    status: str
    default_branch: str | None
    eval_run: int
    overall_score: int
    grade: str
    overall_summary: str | None
    intelligence: IntelligenceResponse | None
    evaluations: list[CategoryEvaluationResponse]
    markdown_report: str
    generated_at: datetime
