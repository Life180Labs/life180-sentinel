import uuid
from datetime import datetime

from pydantic import BaseModel


class IntelligenceResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    languages: list[str]
    frameworks: list[str]
    package_managers: list[str]
    databases: list[str]
    docker: list[str]
    cicd: list[str]
    ai_frameworks: list[str]
    file_count: int
    folder_count: int
    tree: dict
    tree_text: str | None
    summary: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
