from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class IssueLink(Base):
    """Vínculo entre issues, a partir do campo `issuelinks` do Jira (genérico — todos os tipos
    de vínculo, não só "Blocks"; motivo de bloqueio é uma query filtrada sobre esta tabela).

    `linked_summary`/`linked_status` são um snapshot do payload do Jira no momento do sync —
    servem de fallback quando a issue vinculada não é sincronizada por nós (outro projeto).
    Quando ela é sincronizada, `sprint_blocked_items` prefere o status ao vivo via `Issue.jira_key`.
    """

    __tablename__ = "issue_links"
    __table_args__ = (
        UniqueConstraint("issue_id", "jira_link_id", name="uq_issue_link_jira_id"),
        Index("ix_issue_links_issue_id", "issue_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id"), index=True)
    jira_link_id: Mapped[str] = mapped_column(String(64))
    link_type_name: Mapped[str] = mapped_column(String(128))  # ex: "Blocks", "Relates"
    direction: Mapped[str] = mapped_column(String(16))  # "inward" | "outward"
    label: Mapped[str] = mapped_column(String(128))  # ex: "is blocked by" / "blocks"
    linked_jira_key: Mapped[str] = mapped_column(String(32))
    linked_summary: Mapped[str] = mapped_column(String(2000))
    linked_status: Mapped[str | None] = mapped_column(String(128), nullable=True)
