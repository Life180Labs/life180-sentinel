"""Unit tests for GitHub URL validation logic."""
import re

import pytest

_GITHUB_URL_RE = re.compile(
    r"^https://github\.com/[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+$"
)


def validate_github_url(url: str) -> str:
    url = url.strip().rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    if not _GITHUB_URL_RE.match(url):
        raise ValueError(f"Invalid GitHub URL: {url}")
    return url


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/owner/repo", "https://github.com/owner/repo"),
        ("https://github.com/owner/repo.git", "https://github.com/owner/repo"),
        ("https://github.com/owner/repo/", "https://github.com/owner/repo"),
        ("https://github.com/my-org/my.repo", "https://github.com/my-org/my.repo"),
    ],
)
def test_valid_urls(url: str, expected: str) -> None:
    assert validate_github_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "http://github.com/owner/repo",
        "https://gitlab.com/owner/repo",
        "https://github.com/owner",
        "not-a-url",
        "",
        "https://github.com/owner/repo/extra",
    ],
)
def test_invalid_urls(url: str) -> None:
    with pytest.raises(ValueError):
        validate_github_url(url)
