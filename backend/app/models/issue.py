from datetime import datetime

from sqlalchemy import JSON, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Issue(Base):
    __tablename__ = "issues"
    __table_args__ = (
        UniqueConstraint("site_id", "jira_issue_id", name="uq_issue_site_jira_id"),
        Index("ix_issues_updated_at", "updated_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    jira_issue_id: Mapped[str] = mapped_column(String(64))
    jira_key: Mapped[str] = mapped_column(String(32), index=True)

    issue_type: Mapped[str] = mapped_column(String(64))
    summary: Mapped[str] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(String(128))
    status_category: Mapped[str] = mapped_column(String(32))  # new | indeterminate | done (statusCategory.key, não .name — .name é localizado)
    priority: Mapped[str | None] = mapped_column(String(64), nullable=True)

    assignee_person_id: Mapped[int | None] = mapped_column(ForeignKey("people.id"), nullable=True, index=True)
    reporter_person_id: Mapped[int | None] = mapped_column(ForeignKey("people.id"), nullable=True, index=True)

    story_points: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column()
    updated_at: Mapped[datetime] = mapped_column()
    resolved_at: Mapped[datetime | None] = mapped_column(nullable=True)

    raw_payload: Mapped[dict] = mapped_column(JSONB().with_variant(JSON(), "sqlite"))
