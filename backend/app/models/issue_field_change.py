from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class IssueFieldChange(Base):
    """Changelog genérico (qualquer campo, não só status) — permite novas métricas via query, sem nova tabela."""

    __tablename__ = "issue_field_changes"
    __table_args__ = (Index("ix_issue_field_changes_changed_at_field", "changed_at", "field_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id"), index=True)
    jira_changelog_entry_id: Mapped[str] = mapped_column(String(64), unique=True)

    field_name: Mapped[str] = mapped_column(String(64), index=True)
    # Text (não String limitado): mudanças em campos como description/Epic Name podem ter milhares de caracteres.
    from_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    to_value: Mapped[str | None] = mapped_column(Text, nullable=True)

    from_status_category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status_category: Mapped[str | None] = mapped_column(String(32), nullable=True)

    changed_at: Mapped[datetime] = mapped_column()
    changed_by_person_id: Mapped[int | None] = mapped_column(ForeignKey("people.id"), nullable=True)
    sync_run_id: Mapped[int | None] = mapped_column(ForeignKey("sync_runs.id"), nullable=True)
