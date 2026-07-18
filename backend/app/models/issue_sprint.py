from sqlalchemy import Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class IssueSprint(Base):
    """Relação issue<->sprint, populada a partir dos campos sprint/closedSprints da Agile API."""

    __tablename__ = "issue_sprints"
    __table_args__ = (
        UniqueConstraint("issue_id", "sprint_id", name="uq_issue_sprint"),
        Index("ix_issue_sprints_sprint_id", "sprint_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id"), index=True)
    sprint_id: Mapped[int] = mapped_column(ForeignKey("sprints.id"))
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
