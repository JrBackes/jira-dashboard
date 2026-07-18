from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Site(Base):
    """Um site Atlassian (ex: TEC, CAP). Credenciais ficam só em .env, nunca aqui."""

    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    base_url: Mapped[str] = mapped_column(String(255))
    jira_cloud_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
