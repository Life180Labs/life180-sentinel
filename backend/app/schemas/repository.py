import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


class RepositoryCreate(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_github_url(cls, v: str) -> str:
        v = v.strip().rstrip("/")
        if v.endswith(".git"):
            v = v[:-4]
        import re

        pattern = r"^https://github\.com/[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+$"
        if not re.match(pattern, v):
            raise ValueError("Must be a valid GitHub repository URL (https://github.com/owner/repo)")
        return v


class RepositoryResponse(BaseModel):
    id: uuid.UUID
    url: str
    owner: str
    name: str
    default_branch: str | None
    description: str | None
    local_path: str | None
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
