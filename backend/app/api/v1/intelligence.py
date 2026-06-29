import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.intelligence import RepositoryIntelligence
from app.schemas.intelligence import IntelligenceResponse

router = APIRouter(prefix="/repositories", tags=["intelligence"])

DbDep = Annotated[Session, Depends(get_db)]


@router.get("/{repo_id}/intelligence", response_model=IntelligenceResponse)
def get_intelligence(repo_id: uuid.UUID, db: DbDep):
    intel = (
        db.query(RepositoryIntelligence)
        .filter(RepositoryIntelligence.repository_id == repo_id)
        .first()
    )
    if not intel:
        raise HTTPException(status_code=404, detail="Intelligence data not found")
    return intel
