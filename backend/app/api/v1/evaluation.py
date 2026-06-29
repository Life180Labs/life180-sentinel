import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.evaluation import EvaluationResult
from app.schemas.evaluation import CategoryEvaluationResponse, EvaluationSummaryResponse

router = APIRouter(prefix="/repositories", tags=["evaluation"])

DbDep = Annotated[Session, Depends(get_db)]


@router.get("/{repo_id}/evaluations", response_model=EvaluationSummaryResponse)
def get_evaluations(repo_id: uuid.UUID, db: DbDep):
    results = (
        db.query(EvaluationResult)
        .filter(EvaluationResult.repository_id == repo_id)
        .order_by(EvaluationResult.category)
        .all()
    )
    if not results:
        raise HTTPException(status_code=404, detail="Evaluation results not found")

    overall_score = round(sum(r.score for r in results) / len(results)) if results else 0
    return EvaluationSummaryResponse(
        repository_id=repo_id,
        overall_score=overall_score,
        categories=results,
    )


@router.get(
    "/{repo_id}/evaluations/{category}", response_model=CategoryEvaluationResponse
)
def get_evaluation_category(repo_id: uuid.UUID, category: str, db: DbDep):
    result = (
        db.query(EvaluationResult)
        .filter(
            EvaluationResult.repository_id == repo_id,
            EvaluationResult.category == category,
        )
        .first()
    )
    if not result:
        raise HTTPException(
            status_code=404, detail=f"Evaluation for category '{category}' not found"
        )
    return result
