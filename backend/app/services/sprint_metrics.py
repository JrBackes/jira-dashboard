"""Agregações de métricas de sprint. Rotas só validam parâmetros e delegam para cá."""

from collections import Counter
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Board, Issue, IssueFieldChange, IssueSprint, Project, Sprint


def list_sprints(db: Session, project_key: str | None = None, state: str | None = None) -> list[Sprint]:
    query = db.query(Sprint).join(Board).join(Project)
    if project_key:
        query = query.filter(Project.jira_key == project_key)
    if state:
        query = query.filter(Sprint.state == state)
    return query.order_by(Sprint.start_date.desc()).all()


def get_sprint(db: Session, sprint_id: int) -> Sprint | None:
    return db.get(Sprint, sprint_id)


def sprint_status_counts(db: Session, sprint_id: int) -> dict[str, int]:
    issues = (
        db.query(Issue)
        .join(IssueSprint, IssueSprint.issue_id == Issue.id)
        .filter(IssueSprint.sprint_id == sprint_id, IssueSprint.is_current.is_(True))
        .all()
    )
    return dict(Counter(issue.status_category for issue in issues))


def sprint_scope_changes(db: Session, sprint: Sprint) -> dict[str, list[dict]]:
    """Entradas/saídas de escopo durante a sprint, a partir do changelog do campo 'Sprint'.

    O changelog do Jira registra mudanças no campo Sprint com fromString/toString contendo
    o(s) nome(s) da(s) sprint(s) — usamos o nome da sprint para detectar entrada/saída.
    """
    if not sprint.start_date:
        return {"added": [], "removed": []}
    window_end = sprint.end_date or datetime.utcnow()

    changes = (
        db.query(IssueFieldChange, Issue)
        .join(Issue, Issue.id == IssueFieldChange.issue_id)
        .join(IssueSprint, IssueSprint.issue_id == Issue.id)
        .filter(
            IssueSprint.sprint_id == sprint.id,
            IssueFieldChange.field_name == "Sprint",
            IssueFieldChange.changed_at >= sprint.start_date,
            IssueFieldChange.changed_at <= window_end,
        )
        .all()
    )

    added, removed = [], []
    for change, issue in changes:
        entry = {"issue_key": issue.jira_key, "summary": issue.summary, "changed_at": change.changed_at}
        to_has_sprint = sprint.name in (change.to_value or "")
        from_has_sprint = sprint.name in (change.from_value or "")
        if to_has_sprint and not from_has_sprint:
            added.append(entry)
        elif from_has_sprint and not to_has_sprint:
            removed.append(entry)
    return {"added": added, "removed": removed}


def sprint_burndown(db: Session, sprint: Sprint) -> list[dict]:
    """Burndown diário simplificado: usa `resolved_at` como marco de conclusão.

    Não reconstrói a categoria de status histórica via changelog (from/to_status_category
    ainda não são preenchidos no sync — ver TASKS.md) — é uma aproximação aceitável para v1,
    já que a maioria dos itens não reabre depois de resolvida.
    """
    if not sprint.start_date:
        return []
    end_day = (sprint.end_date or datetime.utcnow()).date()
    start_day = sprint.start_date.date()

    issues = (
        db.query(Issue)
        .join(IssueSprint, IssueSprint.issue_id == Issue.id)
        .filter(IssueSprint.sprint_id == sprint.id)
        .all()
    )

    points: list[dict] = []
    day = start_day
    while day <= end_day:
        day_end = datetime.combine(day, datetime.max.time())
        remaining = [
            issue
            for issue in issues
            if issue.created_at.date() <= day and (issue.resolved_at is None or issue.resolved_at > day_end)
        ]
        points.append(
            {
                "day": day,
                "remaining_issues": len(remaining),
                "remaining_points": float(sum(i.story_points or 0 for i in remaining)),
            }
        )
        day += timedelta(days=1)
    return points


def velocity_history(db: Session, board_id: int, limit: int = 6) -> list[dict]:
    sprints = (
        db.query(Sprint)
        .filter(Sprint.board_id == board_id, Sprint.state == "closed")
        .order_by(Sprint.end_date.desc())
        .limit(limit)
        .all()
    )

    history = []
    for sprint in reversed(sprints):
        issues = (
            db.query(Issue)
            .join(IssueSprint, IssueSprint.issue_id == Issue.id)
            .filter(IssueSprint.sprint_id == sprint.id)
            .all()
        )
        planned = sum(i.story_points or 0 for i in issues)
        delivered = sum(i.story_points or 0 for i in issues if i.status_category == "done")
        history.append(
            {
                "sprint_id": sprint.id,
                "sprint_name": sprint.name,
                "planned_points": float(planned),
                "delivered_points": float(delivered),
            }
        )
    return history
