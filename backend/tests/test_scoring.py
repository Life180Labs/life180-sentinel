"""Unit tests for scoring and report generation."""
import pytest

from app.services.report_service import compute_overall_score, score_to_grade


@pytest.mark.parametrize(
    "score,expected_grade",
    [
        (95, "A+"),
        (87, "A"),
        (82, "A-"),
        (77, "B+"),
        (72, "B"),
        (67, "B-"),
        (62, "C+"),
        (57, "C"),
        (52, "C-"),
        (45, "D"),
        (30, "F"),
        (0, "F"),
    ],
)
def test_score_to_grade(score: int, expected_grade: str) -> None:
    assert score_to_grade(score) == expected_grade


def test_overall_score_average() -> None:
    class _FakeEval:
        def __init__(self, score: int):
            self.score = score

    evals = [_FakeEval(80), _FakeEval(60), _FakeEval(70)]
    assert compute_overall_score(evals) == 70  # type: ignore[arg-type]


def test_overall_score_empty() -> None:
    assert compute_overall_score([]) == 0


def test_overall_score_rounds() -> None:
    class _FakeEval:
        def __init__(self, score: int):
            self.score = score

    evals = [_FakeEval(67), _FakeEval(68)]
    assert compute_overall_score(evals) == 68  # type: ignore[arg-type]
