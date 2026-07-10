"""Unit tests for the intelligence scanner."""
import uuid
from pathlib import Path

import pytest

from app.services.intelligence.scanner import ScanResult, scan_repository
from app.services.intelligence.tree import build_tree, tree_to_text


@pytest.fixture()
def sample_repo(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    (tmp_path / "src" / "utils.py").write_text("")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("")
    (tmp_path / "requirements.txt").write_text("fastapi\n")
    (tmp_path / "Dockerfile").write_text("FROM python:3.13\n")
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "workflows").mkdir()
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text("")
    return tmp_path


def test_scan_returns_result(sample_repo: Path) -> None:
    result = scan_repository(uuid.uuid4(), str(sample_repo))
    assert isinstance(result, ScanResult)
    assert result.file_count > 0
    assert result.folder_count > 0


def test_scan_detects_python(sample_repo: Path) -> None:
    result = scan_repository(uuid.uuid4(), str(sample_repo))
    assert "Python" in result.languages


def test_scan_detects_docker(sample_repo: Path) -> None:
    result = scan_repository(uuid.uuid4(), str(sample_repo))
    assert "Dockerfile" in result.docker


def test_scan_detects_github_actions(sample_repo: Path) -> None:
    result = scan_repository(uuid.uuid4(), str(sample_repo))
    assert "GitHub Actions" in result.cicd


def test_scan_summary_not_empty(sample_repo: Path) -> None:
    result = scan_repository(uuid.uuid4(), str(sample_repo))
    assert result.summary


def test_tree_structure(sample_repo: Path) -> None:
    tree = build_tree(sample_repo)
    assert tree["type"] == "dir"
    assert len(tree["children"]) > 0


def test_tree_to_text(sample_repo: Path) -> None:
    tree = build_tree(sample_repo)
    text = tree_to_text(tree)
    assert "src" in text
    assert "Dockerfile" in text


def test_tree_captures_all_top_level_dirs_when_early_sibling_is_huge(tmp_path: Path) -> None:
    """A large 'backend' subtree must not starve the node budget before 'frontend' is visited."""
    backend = tmp_path / "backend"
    backend.mkdir()
    for i in range(500):
        (backend / f"file_{i}.py").write_text("")
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "index.tsx").write_text("")

    tree = build_tree(tmp_path, max_nodes=50)
    top_level_names = {child["name"] for child in tree["children"]}
    assert "frontend" in top_level_names
    assert "backend" in top_level_names
