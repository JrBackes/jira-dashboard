"""Sync e consulta do Mapa de Tecnologia (planilha externa) — vínculo com issues do Jira via Epic.

O vínculo real (linha da planilha -> Epic do Jira) é curado manualmente na própria planilha,
coluna "Epic Jira" (casamento automático por texto testado e descartado — ver
docs/problemas-dashboard.md, problema 3). O vínculo issue -> Epic vem do campo `parent` do
Jira, sincronizado em `issues.parent_jira_key`.

Sem credencial nenhuma do Google: Cloud Console fora de alcance (sem admin/projeto) e a
planilha não pode ficar acessível por link — a importação é manual, por colar/paste (o
usuário seleciona a aba inteira no Google Sheets, copia, e cola como TSV — formato nativo do
clipboard do Sheets, tab-separated).
"""

import csv
import io

from sqlalchemy.orm import Session

from app.integrations.google_sheets.mappers import parse_tech_map_rows
from app.models import Issue, IssueSprint, TechMapEntry


def import_tech_map_from_tsv(db: Session, sheet_name: str, tsv_text: str) -> int:
    """Substitui todas as entradas de `sheet_name` pelo conteúdo colado — replace completo,
    não incremental (sem ID estável de linha, volume baixo o suficiente pra não precisar de
    diff). `tsv_text` é o que sai ao colar células copiadas do Google Sheets (tab-separated)."""
    reader = csv.reader(io.StringIO(tsv_text), delimiter="\t")
    values = list(reader)

    entries = parse_tech_map_rows(values, sheet_name)
    if not entries:
        raise ValueError('Nenhuma linha com "Tarefa" preenchida encontrada no texto colado — confira se copiou a linha de cabeçalho junto.')

    db.query(TechMapEntry).filter_by(sheet_name=sheet_name).delete()
    for entry in entries:
        db.add(TechMapEntry(**entry))
    db.commit()
    return len(entries)


def get_tech_map_for_sprint(db: Session, sprint_id: int) -> list[dict]:
    """Pras issues da sprint atual, agrupa por Epic (via `Issue.parent_jira_key`) e junta com
    o Mapa de Tecnologia (`TechMapEntry.epic_jira_key`) — issues sem Epic ou Epics sem vínculo
    curado na planilha aparecem com os campos da planilha em branco (`None`), não excluídos."""
    issues = (
        db.query(Issue)
        .join(IssueSprint, IssueSprint.issue_id == Issue.id)
        .filter(IssueSprint.sprint_id == sprint_id, IssueSprint.is_current.is_(True))
        .all()
    )
    if not issues:
        return []

    epic_keys = {issue.parent_jira_key for issue in issues if issue.parent_jira_key}
    epics_by_key = (
        {e.jira_key: e for e in db.query(Issue).filter(Issue.jira_key.in_(epic_keys), Issue.issue_type == "Epic")}
        if epic_keys
        else {}
    )
    tech_map_by_epic_key = (
        {t.epic_jira_key: t for t in db.query(TechMapEntry).filter(TechMapEntry.epic_jira_key.in_(epic_keys))}
        if epic_keys
        else {}
    )

    groups: dict[str, dict] = {}
    for issue in issues:
        epic_key = issue.parent_jira_key if issue.parent_jira_key in epics_by_key else None
        group = groups.setdefault(
            epic_key or "__sem_epic__",
            {"epic_key": epic_key, "epic_summary": None, "issue_count": 0, "tech_map": None},
        )
        group["issue_count"] += 1
        if epic_key and group["epic_summary"] is None:
            group["epic_summary"] = epics_by_key[epic_key].summary
            tech_map_entry = tech_map_by_epic_key.get(epic_key)
            if tech_map_entry:
                group["tech_map"] = {
                    "tarefa": tech_map_entry.tarefa,
                    "status": tech_map_entry.status,
                    "frente": tech_map_entry.frente,
                    "ice_score": tech_map_entry.ice_score,
                    "entrega": tech_map_entry.entrega,
                }

    return sorted(groups.values(), key=lambda g: g["issue_count"], reverse=True)
