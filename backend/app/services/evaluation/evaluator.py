"""AI-powered repository evaluator — supports Anthropic (Claude) and Google (Gemini)."""
from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field

from app.core.config import settings
from app.core.logging import get_logger
from app.services.intelligence.scanner import ScanResult

logger = get_logger(__name__)

CATEGORIES = [
    "architecture",
    "security",
    "backend",
    "frontend",
    "database",
    "performance",
    "testing",
    "documentation",
]

_CATEGORY_FOCUS = {
    "architecture": (
        "Evaluate the overall architecture and structural design of this repository. "
        "Consider: separation of concerns, modularity, layering (e.g. MVC/clean arch), "
        "monorepo vs monolith vs microservices indicators, configuration management, "
        "dependency organization, and scalability signals visible from the file structure."
    ),
    "security": (
        "Evaluate security posture based on the repository structure and detected technologies. "
        "Consider: presence of .env files (are secrets committed?), authentication/authorization "
        "patterns, dependency management (lockfiles, known-vulnerable package signals), "
        "secrets management, HTTPS enforcement signals, input validation patterns, "
        "security-related CI steps, and OWASP top-10 exposure indicators."
    ),
    "backend": (
        "Evaluate the backend implementation quality. "
        "Consider: framework usage and conventions, API design patterns (REST/GraphQL/gRPC), "
        "error handling structure, middleware organization, service/repository layer separation, "
        "async patterns, background job handling, and code organization visible from the tree."
    ),
    "frontend": (
        "Evaluate the frontend implementation quality. "
        "Consider: framework and tooling choices, component organization, state management "
        "patterns, build tooling, asset handling, responsiveness/accessibility signals, "
        "and whether a frontend even exists. If no frontend is detected, score accordingly "
        "and note it is backend-only."
    ),
    "database": (
        "Evaluate the database design and data layer quality. "
        "Consider: database technology choices, ORM usage, migration tooling presence, "
        "schema organization, indexing signals, connection pooling patterns, "
        "multiple database usage, caching layer integration, and data modeling quality "
        "inferred from model/entity file structure."
    ),
    "performance": (
        "Evaluate performance engineering signals. "
        "Consider: caching strategy (Redis, Memcached, in-memory), async/concurrent "
        "processing patterns, background job queues, CDN/static asset handling, "
        "database query optimization signals (indexes, pagination patterns), "
        "load balancing configuration, and performance testing presence."
    ),
    "testing": (
        "Evaluate the testing strategy and coverage signals. "
        "Consider: presence and organization of test directories, test framework choices, "
        "unit vs integration vs e2e test separation, CI/CD test automation, coverage tooling, "
        "fixture/factory patterns, mocking strategies, and overall test-to-source ratio signals."
    ),
    "documentation": (
        "Evaluate documentation quality and completeness. "
        "Consider: README presence and apparent quality, API documentation (OpenAPI/Swagger), "
        "inline code documentation patterns, changelog/changelog files, contribution guidelines, "
        "architecture decision records, deployment guides, and developer onboarding materials."
    ),
}

_SYSTEM_PROMPT = """\
You are an expert software engineer and technical reviewer. You will evaluate a GitHub repository \
based on its structural metadata, detected technologies, and file tree. You do NOT have access \
to the actual source code — base your evaluation on what is structurally observable.

Respond ONLY with a valid JSON object in this exact format:
{
  "score": <integer 0-100>,
  "findings": [<string>, ...],
  "recommendations": [<string>, ...],
  "summary": "<string>"
}

Scoring guide:
- 90-100: Exemplary — best practices thoroughly applied
- 75-89: Good — solid implementation with minor gaps
- 60-74: Adequate — functional but with notable improvements needed
- 40-59: Needs work — significant gaps or anti-patterns present
- 0-39: Poor — major issues, missing fundamentals

Findings: concrete observations (what you see or notably don't see).
Recommendations: actionable improvements, ordered by priority.
Summary: 2-3 sentence overall assessment for this category.
Return 3-6 findings and 3-5 recommendations. Be specific and practical."""


def _build_user_message(repo_name: str, owner: str, scan: ScanResult, category: str) -> str:
    tech_context = []
    if scan.languages:
        tech_context.append(f"Languages: {', '.join(scan.languages)}")
    if scan.frameworks:
        tech_context.append(f"Frameworks: {', '.join(scan.frameworks)}")
    if scan.package_managers:
        tech_context.append(f"Package managers: {', '.join(scan.package_managers)}")
    if scan.databases:
        tech_context.append(f"Databases: {', '.join(scan.databases)}")
    if scan.docker:
        tech_context.append(f"Docker: {', '.join(scan.docker)}")
    if scan.cicd:
        tech_context.append(f"CI/CD: {', '.join(scan.cicd)}")
    if scan.ai_frameworks:
        tech_context.append(f"AI/ML: {', '.join(scan.ai_frameworks)}")
    tech_context.append(f"Files: {scan.file_count} | Folders: {scan.folder_count}")

    tree_text = scan.tree_text or ""
    if len(tree_text) > 6000:
        tree_text = tree_text[:6000] + "\n... (truncated)"

    return (
        f"Repository: {owner}/{repo_name}\n\n"
        f"## Detected Technologies\n"
        + "\n".join(tech_context)
        + f"\n\n## Structural Summary\n{scan.summary}\n\n"
        f"## File Tree\n```\n{tree_text}\n```\n\n"
        f"## Evaluation Focus\n{_CATEGORY_FOCUS[category]}"
    )


def _parse_json_response(raw: str, category: str) -> tuple[int, list[str], list[str], str]:
    """Extract score/findings/recommendations/summary from a raw JSON response string.

    Handles both bare JSON and JSON wrapped in markdown code fences.
    """
    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    clean = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    clean = re.sub(r"\s*```\s*$", "", clean.strip(), flags=re.MULTILINE)

    for candidate in (clean, raw):
        try:
            json_match = re.search(r"\{[\s\S]*\}", candidate)
            if json_match:
                data = json.loads(json_match.group())
                score = max(0, min(100, int(data.get("score", 0))))
                findings = [str(f) for f in data.get("findings", [])]
                recommendations = [str(r) for r in data.get("recommendations", [])]
                summary = str(data.get("summary", ""))
                return score, findings, recommendations, summary
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            logger.warning("Failed to parse evaluation JSON for %s: %s", category, exc)

    return 50, [], [], raw[:500] if raw else "Evaluation parsing failed."


@dataclass
class CategoryEvaluation:
    category: str
    score: int = 0
    findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    summary: str = ""
    raw_response: str = ""


# ---------------------------------------------------------------------------
# Anthropic backend
# ---------------------------------------------------------------------------

def _evaluate_category_anthropic(
    client,  # anthropic.Anthropic
    repo_name: str,
    owner: str,
    scan: ScanResult,
    category: str,
) -> CategoryEvaluation:
    user_msg = _build_user_message(repo_name, owner, scan, category)
    logger.info("[anthropic] Evaluating category '%s' for %s/%s", category, owner, repo_name)

    with client.messages.stream(
        model="claude-opus-4-8",
        max_tokens=2048,
        thinking={"type": "adaptive"},
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    ) as stream:
        final = stream.get_final_message()

    raw = ""
    for block in final.content:
        if block.type == "text":
            raw = block.text
            break

    score, findings, recommendations, summary = _parse_json_response(raw, category)
    logger.info("[anthropic] Category '%s' score: %d", category, score)
    return CategoryEvaluation(
        category=category,
        score=score,
        findings=findings,
        recommendations=recommendations,
        summary=summary,
        raw_response=raw,
    )


def _run_anthropic(
    repo_name: str, owner: str, scan: ScanResult
) -> list[CategoryEvaluation]:
    import anthropic as _anthropic

    client = _anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    evaluations: list[CategoryEvaluation] = []
    for category in CATEGORIES:
        try:
            ev = _evaluate_category_anthropic(client, repo_name, owner, scan, category)
            evaluations.append(ev)
        except Exception as exc:
            logger.exception("[anthropic] Evaluation failed for category '%s': %s", category, exc)
            evaluations.append(
                CategoryEvaluation(category=category, score=0, summary=f"Evaluation failed: {exc}")
            )
    return evaluations


# ---------------------------------------------------------------------------
# Gemini backend
# ---------------------------------------------------------------------------

def _evaluate_category_gemini(
    model,  # google.generativeai.GenerativeModel
    repo_name: str,
    owner: str,
    scan: ScanResult,
    category: str,
) -> CategoryEvaluation:
    user_msg = _build_user_message(repo_name, owner, scan, category)
    logger.info("[gemini] Evaluating category '%s' for %s/%s", category, owner, repo_name)

    response = model.generate_content(user_msg)
    raw = response.text or ""

    score, findings, recommendations, summary = _parse_json_response(raw, category)
    logger.info("[gemini] Category '%s' score: %d", category, score)
    return CategoryEvaluation(
        category=category,
        score=score,
        findings=findings,
        recommendations=recommendations,
        summary=summary,
        raw_response=raw,
    )


def _run_gemini(
    repo_name: str, owner: str, scan: ScanResult
) -> list[CategoryEvaluation]:
    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=_SYSTEM_PROMPT,
        generation_config={"max_output_tokens": 8192, "temperature": 0.2},
    )

    evaluations: list[CategoryEvaluation] = []
    for category in CATEGORIES:
        try:
            ev = _evaluate_category_gemini(model, repo_name, owner, scan, category)
            evaluations.append(ev)
        except Exception as exc:
            logger.exception("[gemini] Evaluation failed for category '%s': %s", category, exc)
            evaluations.append(
                CategoryEvaluation(category=category, score=0, summary=f"Evaluation failed: {exc}")
            )
    return evaluations


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def evaluate_repository(
    repo_id: uuid.UUID,
    repo_name: str,
    owner: str,
    scan: ScanResult,
) -> list[CategoryEvaluation]:
    provider = settings.AI_PROVIDER.lower()

    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY not configured — skipping evaluation")
            return _skipped("GEMINI_API_KEY not configured.")
        return _run_gemini(repo_name, owner, scan)

    # Default: anthropic
    if not settings.ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not configured — skipping evaluation")
        return _skipped("ANTHROPIC_API_KEY not configured.")
    return _run_anthropic(repo_name, owner, scan)


def _skipped(reason: str) -> list[CategoryEvaluation]:
    return [
        CategoryEvaluation(category=cat, score=0, summary=f"Evaluation skipped: {reason}")
        for cat in CATEGORIES
    ]
