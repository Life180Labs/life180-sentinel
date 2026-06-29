import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.report import ReportResponse, RepositoryScoreResponse
from app.services.report_service import get_report, get_score

router = APIRouter(prefix="/repositories", tags=["reports"])

DbDep = Annotated[Session, Depends(get_db)]


@router.get("/{repo_id}/score", response_model=RepositoryScoreResponse)
def get_repository_score(repo_id: uuid.UUID, db: DbDep):
    score = get_score(db, repo_id)
    if not score:
        raise HTTPException(status_code=404, detail="Score not available — evaluation not complete")
    return score


@router.get("/{repo_id}/report", response_model=ReportResponse)
def get_repository_report(repo_id: uuid.UUID, db: DbDep):
    report = get_report(db, repo_id)
    if not report:
        raise HTTPException(status_code=404, detail="Repository not found")
    return report


@router.get("/{repo_id}/report/markdown", response_class=PlainTextResponse)
def get_repository_report_markdown(repo_id: uuid.UUID, db: DbDep):
    report = get_report(db, repo_id)
    if not report:
        raise HTTPException(status_code=404, detail="Repository not found")
    return report.markdown_report
