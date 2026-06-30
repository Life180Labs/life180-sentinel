import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas.repository import RepositoryCreate, RepositoryResponse
from app.services import repository_service

router = APIRouter(prefix="/repositories", tags=["repositories"])

DbDep = Annotated[Session, Depends(get_db)]


@router.post("/", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
def add_repository(payload: RepositoryCreate, background_tasks: BackgroundTasks, db: DbDep):
    from app.models.repository import Repository as RepoModel

    existing = db.query(RepoModel).filter(RepoModel.url == payload.url).first()
    if existing:
        return existing

    repo = repository_service.create_repository(db, payload.url)
    background_tasks.add_task(repository_service.clone_repository_background, repo.id)
    return repo


@router.get("/", response_model=list[RepositoryResponse])
def list_repositories(db: DbDep, skip: int = 0, limit: int = 50):
    return repository_service.list_repositories(db, skip=skip, limit=limit)


@router.get("/{repo_id}", response_model=RepositoryResponse)
def get_repository(repo_id: uuid.UUID, db: DbDep):
    repo = repository_service.get_repository(db, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.post("/{repo_id}/re-evaluate", response_model=RepositoryResponse)
def re_evaluate_repository(repo_id: uuid.UUID, background_tasks: BackgroundTasks, db: DbDep):
    repo = repository_service.get_repository(db, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.status in ("cloning", "scanning", "evaluating"):
        raise HTTPException(status_code=409, detail="Evaluation already in progress")
    repository_service.reset_repository(db, repo)
    background_tasks.add_task(repository_service.clone_repository_background, repo.id)
    return repo


@router.delete("/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_repository(repo_id: uuid.UUID, db: DbDep):
    repo = repository_service.get_repository(db, repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    repository_service.delete_repository(db, repo)
