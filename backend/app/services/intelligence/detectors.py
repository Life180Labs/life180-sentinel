"""
File-based detectors for languages, frameworks, package managers, databases,
Docker, CI/CD, and AI frameworks. All functions accept a repo_path (str | Path)
and return lists of detected items.
"""
from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_IGNORE_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".next",
    "dist", "build", "out", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "coverage", ".nyc_output",
}


def _iter_files(root: Path):
    """Yield (relative_path_str, filename) for every file under root, skipping ignored dirs."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _IGNORE_DIRS]
        for fname in filenames:
            full = Path(dirpath) / fname
            rel = str(full.relative_to(root))
            yield rel, fname


def _has_file(root: Path, *names: str) -> bool:
    return any((root / n).exists() for n in names)


def _read_file(path: Path, max_bytes: int = 65536) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_bytes]
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

_LANG_EXT: dict[str, str] = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".swift": "Swift",
    ".scala": "Scala",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".hs": "Haskell",
    ".lua": "Lua",
    ".r": "R",
    ".jl": "Julia",
    ".dart": "Dart",
}


def detect_languages(root: Path) -> list[str]:
    found: set[str] = set()
    for _, fname in _iter_files(root):
        ext = Path(fname).suffix.lower()
        if ext in _LANG_EXT:
            found.add(_LANG_EXT[ext])
    return sorted(found)


# ---------------------------------------------------------------------------
# Framework detection
# ---------------------------------------------------------------------------

def detect_frameworks(root: Path) -> list[str]:
    found: set[str] = set()

    # Next.js
    pkg = root / "package.json"
    if pkg.exists():
        content = _read_file(pkg)
        if '"next"' in content:
            found.add("Next.js")
        if '"react"' in content:
            found.add("React")
        if '"vue"' in content:
            found.add("Vue")
        if '"nuxt"' in content:
            found.add("Nuxt")
        if '"svelte"' in content:
            found.add("Svelte")
        if '"@angular/core"' in content:
            found.add("Angular")
        if '"express"' in content:
            found.add("Express")
        if '"fastify"' in content:
            found.add("Fastify")
        if '"nestjs"' in content or '"@nestjs/core"' in content:
            found.add("NestJS")

    # Python frameworks — look for imports / dependencies
    for rel, fname in _iter_files(root):
        if fname in ("requirements.txt", "pyproject.toml", "setup.cfg", "Pipfile"):
            content = _read_file(root / rel)
            _lower = content.lower()
            if "fastapi" in _lower:
                found.add("FastAPI")
            if "django" in _lower:
                found.add("Django")
            if "flask" in _lower:
                found.add("Flask")
            if "sqlalchemy" in _lower:
                found.add("SQLAlchemy")
            if "alembic" in _lower:
                found.add("Alembic")
            if "celery" in _lower:
                found.add("Celery")

    # Go
    if (root / "go.mod").exists():
        content = _read_file(root / "go.mod")
        if "gin-gonic/gin" in content:
            found.add("Gin")
        if "labstack/echo" in content:
            found.add("Echo")
        if "gofiber/fiber" in content:
            found.add("Fiber")

    # Ruby
    gemfile = root / "Gemfile"
    if gemfile.exists():
        content = _read_file(gemfile)
        if "rails" in content.lower():
            found.add("Ruby on Rails")
        if "sinatra" in content.lower():
            found.add("Sinatra")

    # Java / Kotlin
    for rel, fname in _iter_files(root):
        if fname in ("pom.xml", "build.gradle", "build.gradle.kts"):
            content = _read_file(root / rel)
            if "spring-boot" in content.lower() or "springframework" in content.lower():
                found.add("Spring Boot")

    return sorted(found)


# ---------------------------------------------------------------------------
# Package manager detection
# ---------------------------------------------------------------------------

def detect_package_managers(root: Path) -> list[str]:
    found: set[str] = set()
    checks = {
        "package-lock.json": "npm",
        "yarn.lock": "Yarn",
        "pnpm-lock.yaml": "pnpm",
        "bun.lockb": "Bun",
        "requirements.txt": "pip",
        "Pipfile": "Pipenv",
        "pyproject.toml": "Poetry/pip",
        "go.sum": "Go modules",
        "Cargo.lock": "Cargo",
        "Gemfile.lock": "Bundler",
        "composer.lock": "Composer",
        "pom.xml": "Maven",
        "build.gradle": "Gradle",
        "build.gradle.kts": "Gradle",
        "pubspec.yaml": "pub (Dart)",
    }
    for filename, manager in checks.items():
        if _has_file(root, filename):
            found.add(manager)
    return sorted(found)


# ---------------------------------------------------------------------------
# Database detection
# ---------------------------------------------------------------------------

def detect_databases(root: Path) -> list[str]:
    found: set[str] = set()
    keywords = {
        "postgresql": "PostgreSQL",
        "postgres": "PostgreSQL",
        "psycopg": "PostgreSQL",
        "mysql": "MySQL",
        "mariadb": "MariaDB",
        "sqlite": "SQLite",
        "mongodb": "MongoDB",
        "pymongo": "MongoDB",
        "redis": "Redis",
        "elasticsearch": "Elasticsearch",
        "cassandra": "Cassandra",
        "dynamodb": "DynamoDB",
        "firestore": "Firestore",
        "supabase": "Supabase (PostgreSQL)",
        "prisma": "Prisma ORM",
        "typeorm": "TypeORM",
        "sequelize": "Sequelize",
    }
    scan_files = {
        "requirements.txt", "pyproject.toml", "package.json",
        "docker-compose.yml", "docker-compose.yaml", ".env.example",
        ".env", "go.mod", "Gemfile", "pom.xml",
    }
    for rel, fname in _iter_files(root):
        if fname in scan_files:
            content = _read_file(root / rel).lower()
            for kw, db in keywords.items():
                if kw in content:
                    found.add(db)
    return sorted(found)


# ---------------------------------------------------------------------------
# Docker detection
# ---------------------------------------------------------------------------

def detect_docker(root: Path) -> list[str]:
    found: set[str] = set()
    if _has_file(root, "Dockerfile"):
        found.add("Dockerfile")
    if _has_file(root, "docker-compose.yml", "docker-compose.yaml"):
        found.add("Docker Compose")
    if _has_file(root, ".dockerignore"):
        found.add(".dockerignore")
    # Multi-stage or service Dockerfiles
    for rel, fname in _iter_files(root):
        if fname.startswith("Dockerfile"):
            found.add("Dockerfile")
    return sorted(found)


# ---------------------------------------------------------------------------
# CI/CD detection
# ---------------------------------------------------------------------------

def detect_cicd(root: Path) -> list[str]:
    found: set[str] = set()
    checks = {
        ".github/workflows": "GitHub Actions",
        ".gitlab-ci.yml": "GitLab CI",
        "Jenkinsfile": "Jenkins",
        ".circleci/config.yml": "CircleCI",
        ".travis.yml": "Travis CI",
        "bitbucket-pipelines.yml": "Bitbucket Pipelines",
        "azure-pipelines.yml": "Azure Pipelines",
        ".drone.yml": "Drone CI",
        "buildkite.yml": ".buildkite/pipeline.yml",
        "vercel.json": "Vercel",
        "netlify.toml": "Netlify",
        "railway.json": "Railway",
        "render.yaml": "Render",
        "fly.toml": "Fly.io",
        "heroku.yml": "Heroku",
        "Procfile": "Heroku",
    }
    for path_check, label in checks.items():
        target = root / path_check
        if target.exists():
            found.add(label)
    return sorted(found)


# ---------------------------------------------------------------------------
# AI framework detection
# ---------------------------------------------------------------------------

def detect_ai_frameworks(root: Path) -> list[str]:
    found: set[str] = set()
    keywords = {
        "anthropic": "Anthropic SDK",
        "openai": "OpenAI SDK",
        "langchain": "LangChain",
        "langgraph": "LangGraph",
        "llama_index": "LlamaIndex",
        "llama-index": "LlamaIndex",
        "llamaindex": "LlamaIndex",
        "transformers": "HuggingFace Transformers",
        "huggingface": "HuggingFace",
        "sentence_transformers": "Sentence Transformers",
        "cohere": "Cohere SDK",
        "mistralai": "Mistral SDK",
        "google-generativeai": "Google Generative AI",
        "vertexai": "Google Vertex AI",
        "tiktoken": "tiktoken (OpenAI)",
        "pinecone": "Pinecone",
        "chromadb": "ChromaDB",
        "weaviate": "Weaviate",
        "qdrant": "Qdrant",
        "faiss": "FAISS",
        "torch": "PyTorch",
        "tensorflow": "TensorFlow",
        "keras": "Keras",
        "sklearn": "scikit-learn",
        "scikit-learn": "scikit-learn",
        "xgboost": "XGBoost",
        "lightgbm": "LightGBM",
        "autogen": "AutoGen",
        "crewai": "CrewAI",
        "pydantic_ai": "Pydantic AI",
    }
    scan_files = {"requirements.txt", "pyproject.toml", "package.json", "go.mod"}
    for rel, fname in _iter_files(root):
        if fname in scan_files:
            content = _read_file(root / rel).lower()
            for kw, label in keywords.items():
                if kw in content:
                    found.add(label)
    return sorted(found)
