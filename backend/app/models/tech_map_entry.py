from datetime import datetime

from sqlalchemy import JSON, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TechMapEntry(Base):
    """Linha da planilha "Mapa de Tecnologia" (Google Sheets, fora do Jira) — uma iniciativa
    ("Tarefa") de planejamento de produto. Vínculo com Jira é textual via `epic_jira_key`
    (coluna "Epic Jira" da planilha, preenchida manualmente — casamento automático por nome
    entre "Tarefa" e o summary do Epic não é confiável o suficiente, testado nesta sessão).

    Sem FK pra `issues`: mesmo padrão de `issue_links.linked_jira_key` — resolvido em query.
    Sync faz replace completo por `sheet_name` a cada rodada (planilha não tem ID estável de
    linha, volume baixo o suficiente pra não precisar de diff incremental).
    """

    __tablename__ = "tech_map_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    sheet_name: Mapped[str] = mapped_column(String(255), index=True)
    row_index: Mapped[int] = mapped_column()

    status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    frente: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tarefa: Mapped[str] = mapped_column(Text)
    atuantes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    ice_impacto: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    ice_confianca: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    ice_facilidade: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    ice_score: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    entrega: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tamanho_projeto: Mapped[str | None] = mapped_column(String(64), nullable=True)
    motivo: Mapped[str | None] = mapped_column(Text, nullable=True)
    lancamento: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Curadoria manual na planilha (coluna "Epic Jira") — não preenchido em toda linha.
    epic_jira_key: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)

    # Linha inteira, incluindo os marcadores semanais (P/E/R) — extensibilidade, mesmo padrão
    # de `raw_payload` em `issues`.
    raw_row: Mapped[dict] = mapped_column(JSONB().with_variant(JSON(), "sqlite"))

    synced_at: Mapped[datetime] = mapped_column()
