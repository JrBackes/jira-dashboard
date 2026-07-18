from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class SyncCursor(Base):
    """Suporte a sync incremental: até onde cada (site, entidade) já foi sincronizado."""

    __tablename__ = "sync_cursors"
    __table_args__ = (UniqueConstraint("site_id", "entity_type", name="uq_cursor_site_entity"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), index=True)
    entity_type: Mapped[str] = mapped_column(String(32))  # issues | changelog
    last_synced_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_page_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
