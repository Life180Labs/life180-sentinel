import os
import shutil
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.evaluation import EvaluationResult
from app.models.intelligence import RepositoryIntelligence
from app.models.repository import Repository
from app.services.evaluation.evaluator import evaluate_repository, generate_overall_summary
from app.services.intelligence.scanner import scan_repository

logger = get_logger(__name__)


def _parse_github_url(url: str) -> tuple[str, str]:
    """Return (owner, repo_name) from a validated GitHub URL."""
    parts = url.rstrip("/").split("/")
    return parts[-2], parts[-1]


def create_repository(db: Session, url: str) -> Repository:
    owner, name = _parse_github_url(url)
    repo = Repository(url=url, owner=owner, name=name, status="pending")
    db.add(repo)
    db.commit()
    db.refresh(repo)
    logger.info("Repository record created: %s/%s (id=%s)", owner, name, repo.id)
    return repo


def clone_repository(db: Session, repo: Repository) -> Repository:
    clone_dir = Path(settings.REPOS_DIR) / str(repo.id)
    clone_url = repo.url + ".git"

    repo.status = "cloning"
    db.commit()

    try:
        import git  # lazy import — git binary must exist at clone time, not app startup

        logger.info("Cloning %s into %s", clone_url, clone_dir)
        if clone_dir.exists():
            shutil.rmtree(clone_dir)
        # Let git create the target directory — do NOT pre-create it
        clone_dir.parent.mkdir(parents=True, exist_ok=True)
        git_repo = git.Repo.clone_from(clone_url, str(clone_dir))

        repo.local_path = str(clone_dir)
        repo.default_branch = git_repo.active_branch.name
        repo.status = "cloned"
        db.commit()
        db.refresh(repo)
        logger.info("Clone complete: %s", repo.local_path)

        # Run intelligence scan immediately after clone
        _run_intelligence_scan(db, repo)
    except Exception as exc:
        logger.exception("Clone failed for %s", repo.url)
        repo.status = "error"
        repo.error_message = str(exc)
        db.commit()
        db.refresh(repo)

    return repo


def clone_repository_background(repo_id: uuid.UUID) -> None:
    from app.db.base import SessionLocal
    with SessionLocal() as db:
        repo = get_repository(db, repo_id)
        if repo:
            clone_repository(db, repo)


def _run_intelligence_scan(db: Session, repo: Repository) -> None:
    if not repo.local_path:
        return
    repo.status = "scanning"
    db.commit()
    try:
        result = scan_repository(repo.id, repo.local_path)
        intel = RepositoryIntelligence(
            repository_id=repo.id,
            languages=result.languages,
            frameworks=result.frameworks,
            package_managers=result.package_managers,
            databases=result.databases,
            docker=result.docker,
            cicd=result.cicd,
            ai_frameworks=result.ai_frameworks,
            file_count=result.file_count,
            folder_count=result.folder_count,
            tree=result.tree,
            tree_text=result.tree_text,
            summary=result.summary,
        )
        db.add(intel)
        repo.status = "scanned"
        db.commit()
        logger.info("Intelligence scan stored for repo %s", repo.id)

        # Run AI evaluation immediately after scan
        _run_evaluation(db, repo, result)
    except Exception as exc:
        logger.exception("Intelligence scan failed for repo %s", repo.id)
        repo.status = "error"
        repo.error_message = str(exc)
        db.commit()


def _run_evaluation(db: Session, repo: Repository, scan_result) -> None:
    repo.status = "evaluating"
    db.commit()
    try:
        evaluations = evaluate_repository(repo.id, repo.name, repo.owner, scan_result)
        for ev in evaluations:
            db.add(
                EvaluationResult(
                    repository_id=repo.id,
                    eval_run=repo.eval_run or 1,
                    category=ev.category,
                    score=ev.score,
                    reasoning=ev.reasoning,
                    confidence=ev.confidence,
                    findings=ev.findings,
                    recommendations=ev.recommendations,
                    recommendation_scores=ev.recommendation_scores,
                    summary=ev.summary,
                    raw_response=ev.raw_response,
                )
            )
        overall_score = round(sum(ev.score for ev in evaluations) / len(evaluations)) if evaluations else 0
        repo.overall_summary = generate_overall_summary(repo.name, repo.owner, overall_score, evaluations)
        repo.status = "done"
        db.commit()
        logger.info("Evaluation complete for repo %s", repo.id)
    except Exception as exc:
        logger.exception("Evaluation failed for repo %s", repo.id)
        repo.status = "error"
        repo.error_message = str(exc)
        db.commit()


def reset_repository(db: Session, repo: Repository) -> Repository:
    """Preserve old evaluation results (version history) and start a new run."""
    from app.models.intelligence import RepositoryIntelligence

    # Intelligence is technical metadata regenerated each run — not historically interesting
    db.query(RepositoryIntelligence).filter(RepositoryIntelligence.repository_id == repo.id).delete()

    if repo.local_path and os.path.exists(repo.local_path):
        shutil.rmtree(repo.local_path, ignore_errors=True)

    repo.eval_run = (repo.eval_run or 1) + 1
    repo.local_path = None
    repo.default_branch = None
    repo.overall_summary = None
    repo.error_message = None
    repo.status = "pending"
    db.commit()
    db.refresh(repo)
    logger.info("Repository %s reset for re-evaluation (now run #%d)", repo.id, repo.eval_run)
    return repo


def get_repository(db: Session, repo_id: uuid.UUID) -> Repository | None:
    return db.get(Repository, repo_id)


def list_repositories(db: Session, skip: int = 0, limit: int = 50) -> list[Repository]:
    return (
        db.query(Repository)
        .order_by(Repository.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def delete_repository(db: Session, repo: Repository) -> None:
    if repo.local_path and os.path.exists(repo.local_path):
        shutil.rmtree(repo.local_path, ignore_errors=True)
    db.delete(repo)
    db.commit()
