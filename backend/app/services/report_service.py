"""Generates structured and human-readable reports from evaluation results."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.evaluation import EvaluationResult
from app.models.intelligence import RepositoryIntelligence
from app.models.repository import Repository
from app.schemas.evaluation import CategoryEvaluationResponse, EvaluationRunResponse
from app.schemas.intelligence import IntelligenceResponse
from app.schemas.report import ReportResponse, RepositoryScoreResponse

_GRADE_THRESHOLDS = [
    (90, "A+"),
    (85, "A"),
    (80, "A-"),
    (75, "B+"),
    (70, "B"),
    (65, "B-"),
    (60, "C+"),
    (55, "C"),
    (50, "C-"),
    (40, "D"),
    (0, "F"),
]

_PRODUCTION_READINESS = [
    (80, "Production Ready"),
    (65, "Ready With Conditions"),
    (50, "Needs Improvement"),
    (0, "Not Production Ready"),
]


def score_to_grade(score: int) -> str:
    for threshold, grade in _GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"


def score_to_readiness(score: int) -> str:
    for threshold, label in _PRODUCTION_READINESS:
        if score >= threshold:
            return label
    return "Not Production Ready"


def compute_overall_score(evaluations: list[EvaluationResult]) -> int:
    if not evaluations:
        return 0
    return round(sum(e.score for e in evaluations) / len(evaluations))


def get_score(db: Session, repo_id: uuid.UUID) -> RepositoryScoreResponse | None:
    repo = db.get(Repository, repo_id)
    if not repo:
        return None
    evaluations = (
        db.query(EvaluationResult)
        .filter(
            EvaluationResult.repository_id == repo_id,
            EvaluationResult.eval_run == (repo.eval_run or 1),
        )
        .all()
    )
    if not evaluations:
        return None
    overall = compute_overall_score(evaluations)
    return RepositoryScoreResponse(
        repository_id=repo_id,
        overall_score=overall,
        grade=score_to_grade(overall),
        category_scores={e.category: e.score for e in evaluations},
    )


def get_history(db: Session, repo_id: uuid.UUID) -> list[EvaluationRunResponse]:
    """Return per-run score summaries ordered oldest to newest."""
    runs = (
        db.query(
            EvaluationResult.eval_run,
            func.max(EvaluationResult.created_at).label("evaluated_at"),
        )
        .filter(EvaluationResult.repository_id == repo_id)
        .group_by(EvaluationResult.eval_run)
        .order_by(EvaluationResult.eval_run)
        .all()
    )

    result: list[EvaluationRunResponse] = []
    for run_num, evaluated_at in runs:
        evals = (
            db.query(EvaluationResult)
            .filter(
                EvaluationResult.repository_id == repo_id,
                EvaluationResult.eval_run == run_num,
            )
            .all()
        )
        overall = compute_overall_score(evals)
        result.append(
            EvaluationRunResponse(
                run=run_num,
                overall_score=overall,
                grade=score_to_grade(overall),
                category_scores={e.category: e.score for e in evals},
                evaluated_at=evaluated_at,
            )
        )
    return result


def _build_markdown_report(
    repo: Repository,
    intel: RepositoryIntelligence | None,
    evaluations: list[EvaluationResult],
    overall_score: int,
    grade: str,
) -> str:
    readiness = score_to_readiness(overall_score)
    lines: list[str] = []

    lines.append(f"# Life180 Sentinel Report: {repo.owner}/{repo.name}")
    lines.append(f"\n**URL:** {repo.url}")
    if repo.default_branch:
        lines.append(f"**Branch:** {repo.default_branch}")
    lines.append(f"**Overall Score:** {overall_score}/100  **Grade:** {grade}  **Status:** {readiness}")
    lines.append(f"**Evaluation Run:** #{repo.eval_run or 1}")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    if repo.overall_summary:
        lines.append("\n---\n\n## Executive Summary\n")
        lines.append(repo.overall_summary)

    if intel:
        lines.append("\n---\n\n## Repository Overview\n")
        lines.append(intel.summary or "")
        if intel.languages:
            lines.append(f"\n**Languages:** {', '.join(intel.languages)}")
        if intel.frameworks:
            lines.append(f"**Frameworks:** {', '.join(intel.frameworks)}")
        if intel.databases:
            lines.append(f"**Databases:** {', '.join(intel.databases)}")
        if intel.docker:
            lines.append(f"**Docker:** {', '.join(intel.docker)}")
        if intel.cicd:
            lines.append(f"**CI/CD:** {', '.join(intel.cicd)}")
        if intel.ai_frameworks:
            lines.append(f"**AI/ML:** {', '.join(intel.ai_frameworks)}")
        lines.append(f"**Files:** {intel.file_count} | **Folders:** {intel.folder_count}")

    lines.append("\n---\n\n## Score Summary\n")
    lines.append("| Category | Score | Grade | Confidence |")
    lines.append("|----------|-------|-------|------------|")
    for ev in sorted(evaluations, key=lambda e: e.score, reverse=True):
        conf = f"{ev.confidence}%" if ev.confidence is not None else "—"
        lines.append(
            f"| {ev.category.capitalize()} | {ev.score}/100 | {score_to_grade(ev.score)} | {conf} |"
        )
    lines.append(f"| **Overall** | **{overall_score}/100** | **{grade}** | — |")

    lines.append("\n---\n\n## Detailed Evaluations\n")
    for ev in sorted(evaluations, key=lambda e: e.category):
        conf = f" (Confidence: {ev.confidence}%)" if ev.confidence is not None else ""
        lines.append(f"### {ev.category.capitalize()} — {ev.score}/100 ({score_to_grade(ev.score)}){conf}\n")
        if ev.reasoning:
            lines.append(f"**Why this score:** {ev.reasoning}\n")
        if ev.summary:
            lines.append(f"{ev.summary}\n")
        if ev.findings:
            lines.append("**What Works Well (Findings):**")
            for f in ev.findings:
                lines.append(f"- {f}")
            lines.append("")
        if ev.recommendations:
            lines.append("**Recommendations:**")
            rec_scores = ev.recommendation_scores or []
            for i, r in enumerate(ev.recommendations):
                pts = f" *(+{rec_scores[i]} pts)*" if i < len(rec_scores) else ""
                lines.append(f"- {r}{pts}")
            lines.append("")

    return "\n".join(lines)


def get_report(db: Session, repo_id: uuid.UUID, run: int | None = None) -> ReportResponse | None:
    repo = db.get(Repository, repo_id)
    if not repo:
        return None

    current_run = repo.eval_run or 1
    effective_run = run if run is not None else current_run
    is_current = effective_run == current_run

    # Intelligence metadata only exists for the current run
    intel = None
    if is_current:
        intel = (
            db.query(RepositoryIntelligence)
            .filter(RepositoryIntelligence.repository_id == repo_id)
            .first()
        )

    evaluations = (
        db.query(EvaluationResult)
        .filter(
            EvaluationResult.repository_id == repo_id,
            EvaluationResult.eval_run == effective_run,
        )
        .order_by(EvaluationResult.category)
        .all()
    )

    overall_score = compute_overall_score(evaluations)
    grade = score_to_grade(overall_score)
    # Executive summary only stored for the current run
    overall_summary = repo.overall_summary if is_current else None
    markdown = _build_markdown_report(repo, intel, evaluations, overall_score, grade)

    return ReportResponse(
        repository_id=repo_id,
        owner=repo.owner,
        name=repo.name,
        url=repo.url,
        status=repo.status,
        default_branch=repo.default_branch,
        eval_run=effective_run,
        overall_score=overall_score,
        grade=grade,
        overall_summary=overall_summary,
        intelligence=IntelligenceResponse.model_validate(intel) if intel else None,
        evaluations=[CategoryEvaluationResponse.model_validate(e) for e in evaluations],
        markdown_report=markdown,
        generated_at=datetime.now(timezone.utc),
    )
