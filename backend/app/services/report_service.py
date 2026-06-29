"""Generates structured and human-readable reports from evaluation results."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.evaluation import EvaluationResult
from app.models.intelligence import RepositoryIntelligence
from app.models.repository import Repository
from app.schemas.evaluation import CategoryEvaluationResponse
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


def score_to_grade(score: int) -> str:
    for threshold, grade in _GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return "F"


def compute_overall_score(evaluations: list[EvaluationResult]) -> int:
    if not evaluations:
        return 0
    return round(sum(e.score for e in evaluations) / len(evaluations))


def get_score(db: Session, repo_id: uuid.UUID) -> RepositoryScoreResponse | None:
    evaluations = (
        db.query(EvaluationResult)
        .filter(EvaluationResult.repository_id == repo_id)
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


def _build_markdown_report(
    repo: Repository,
    intel: RepositoryIntelligence | None,
    evaluations: list[EvaluationResult],
    overall_score: int,
    grade: str,
) -> str:
    lines: list[str] = []

    lines.append(f"# Life180 Sentinel Report: {repo.owner}/{repo.name}")
    lines.append(f"\n**URL:** {repo.url}")
    if repo.default_branch:
        lines.append(f"**Branch:** {repo.default_branch}")
    lines.append(f"**Overall Score:** {overall_score}/100  **Grade:** {grade}")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

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
    lines.append("| Category | Score | Grade |")
    lines.append("|----------|-------|-------|")
    for ev in sorted(evaluations, key=lambda e: e.score, reverse=True):
        lines.append(
            f"| {ev.category.capitalize()} | {ev.score}/100 | {score_to_grade(ev.score)} |"
        )
    lines.append(f"| **Overall** | **{overall_score}/100** | **{grade}** |")

    lines.append("\n---\n\n## Detailed Evaluations\n")
    for ev in sorted(evaluations, key=lambda e: e.category):
        lines.append(f"### {ev.category.capitalize()} — {ev.score}/100 ({score_to_grade(ev.score)})\n")
        if ev.summary:
            lines.append(f"{ev.summary}\n")
        if ev.findings:
            lines.append("**Findings:**")
            for f in ev.findings:
                lines.append(f"- {f}")
            lines.append("")
        if ev.recommendations:
            lines.append("**Recommendations:**")
            for r in ev.recommendations:
                lines.append(f"- {r}")
            lines.append("")

    return "\n".join(lines)


def get_report(db: Session, repo_id: uuid.UUID) -> ReportResponse | None:
    repo = db.get(Repository, repo_id)
    if not repo:
        return None

    intel = (
        db.query(RepositoryIntelligence)
        .filter(RepositoryIntelligence.repository_id == repo_id)
        .first()
    )
    evaluations = (
        db.query(EvaluationResult)
        .filter(EvaluationResult.repository_id == repo_id)
        .order_by(EvaluationResult.category)
        .all()
    )

    overall_score = compute_overall_score(evaluations)
    grade = score_to_grade(overall_score)
    markdown = _build_markdown_report(repo, intel, evaluations, overall_score, grade)

    return ReportResponse(
        repository_id=repo_id,
        owner=repo.owner,
        name=repo.name,
        url=repo.url,
        status=repo.status,
        default_branch=repo.default_branch,
        overall_score=overall_score,
        grade=grade,
        intelligence=IntelligenceResponse.model_validate(intel) if intel else None,
        evaluations=[CategoryEvaluationResponse.model_validate(e) for e in evaluations],
        markdown_report=markdown,
        generated_at=datetime.now(timezone.utc),
    )
