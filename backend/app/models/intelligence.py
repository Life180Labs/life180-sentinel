import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RepositoryIntelligence(Base):
    __tablename__ = "repository_intelligence"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    languages: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    frameworks: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    package_managers: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    databases: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    docker: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    cicd: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    ai_frameworks: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    file_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    folder_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tree: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    tree_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
