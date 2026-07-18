from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Sprint(Base):
    __tablename__ = "sprints"
    __table_args__ = (UniqueConstraint("board_id", "jira_sprint_id", name="uq_sprint_board_jira_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    board_id: Mapped[int] = mapped_column(ForeignKey("boards.id"), index=True)
    jira_sprint_id: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255))
    state: Mapped[str] = mapped_column(String(16))  # future | active | closed
    start_date: Mapped[datetime | None] = mapped_column(nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(nullable=True)
    complete_date: Mapped[datetime | None] = mapped_column(nullable=True)
    goal: Mapped[str | None] = mapped_column(String(2000), nullable=True)
