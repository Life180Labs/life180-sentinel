"""Orchestrates the full repository intelligence scan."""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from app.core.logging import get_logger
from app.services.intelligence.detectors import (
    _IGNORE_DIRS,
    detect_ai_frameworks,
    detect_cicd,
    detect_databases,
    detect_docker,
    detect_frameworks,
    detect_languages,
    detect_package_managers,
)
from app.services.intelligence.tree import build_tree, tree_to_text

logger = get_logger(__name__)


@dataclass
class ScanResult:
    repo_id: uuid.UUID
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    package_managers: list[str] = field(default_factory=list)
    databases: list[str] = field(default_factory=list)
    docker: list[str] = field(default_factory=list)
    cicd: list[str] = field(default_factory=list)
    ai_frameworks: list[str] = field(default_factory=list)
    file_count: int = 0
    folder_count: int = 0
    tree: dict = field(default_factory=dict)
    tree_text: str = ""
    summary: str = ""


def _count_files_and_folders(root: Path) -> tuple[int, int]:
    files = 0
    folders = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _IGNORE_DIRS]
        folders += len(dirnames)
        files += len(filenames)
    return files, folders


def _build_summary(result: ScanResult) -> str:
    lines = [
        f"Repository contains {result.file_count} files across {result.folder_count} folders.",
    ]
    if result.languages:
        lines.append(f"Languages: {', '.join(result.languages)}.")
    if result.frameworks:
        lines.append(f"Frameworks: {', '.join(result.frameworks)}.")
    if result.package_managers:
        lines.append(f"Package managers: {', '.join(result.package_managers)}.")
    if result.databases:
        lines.append(f"Databases: {', '.join(result.databases)}.")
    if result.docker:
        lines.append(f"Docker: {', '.join(result.docker)}.")
    if result.cicd:
        lines.append(f"CI/CD: {', '.join(result.cicd)}.")
    if result.ai_frameworks:
        lines.append(f"AI/ML frameworks: {', '.join(result.ai_frameworks)}.")
    return " ".join(lines)


def scan_repository(repo_id: uuid.UUID, local_path: str) -> ScanResult:
    root = Path(local_path)
    logger.info("Starting intelligence scan: %s", local_path)

    result = ScanResult(repo_id=repo_id)
    result.languages = detect_languages(root)
    result.frameworks = detect_frameworks(root)
    result.package_managers = detect_package_managers(root)
    result.databases = detect_databases(root)
    result.docker = detect_docker(root)
    result.cicd = detect_cicd(root)
    result.ai_frameworks = detect_ai_frameworks(root)
    result.file_count, result.folder_count = _count_files_and_folders(root)
    result.tree = build_tree(root)
    result.tree_text = tree_to_text(result.tree)
    result.summary = _build_summary(result)

    logger.info(
        "Scan complete for %s: %d files, langs=%s",
        local_path,
        result.file_count,
        result.languages,
    )
    return result
