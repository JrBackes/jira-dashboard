from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Person(Base):
    """Pessoa canônica, pode ter identidades em múltiplos sites Atlassian."""

    __tablename__ = "people"

    id: Mapped[int] = mapped_column(primary_key=True)
    display_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)


class PersonIdentity(Base):
    """accountId do Jira é por instância Atlassian — uma identidade por (pessoa, site)."""

    __tablename__ = "person_identities"
    __table_args__ = (UniqueConstraint("site_id", "jira_account_id", name="uq_identity_site_account"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"), index=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), index=True)
    jira_account_id: Mapped[str] = mapped_column(String(128))
    display_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
