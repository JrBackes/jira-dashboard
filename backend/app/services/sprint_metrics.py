"""Agregações de métricas de sprint. Rotas só validam parâmetros e delegam para cá."""

from collections import Counter
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Board, Issue, IssueFieldChange, IssueSprint, Person, Project, Sprint
from app.services.status_order import sort_status_list, sort_statuses, status_rank

_TO_TEST_RANK = status_rank("to test")


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
    """Agrupa por status real (Backlog, To Do, In Progress, Is Blocked, To Test...), não pela
    categoria genérica do Jira — o time tem um fluxo mais granular que 'new/indeterminate/done'."""
    issues = (
        db.query(Issue)
        .join(IssueSprint, IssueSprint.issue_id == Issue.id)
        .filter(IssueSprint.sprint_id == sprint_id, IssueSprint.is_current.is_(True))
        .all()
    )
    return sort_statuses(dict(Counter(issue.status for issue in issues)))


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


def sprint_workload_by_status_and_person(db: Session, sprint_id: int) -> dict:
    """Matriz colaborador x status na sprint atual, com tempo por célula.

    Tempo = "Estimativa original" (timeoriginalestimate) enquanto a issue nunca chegou em
    "To Test"; "Tempo gasto" (timespent, apontamento manual) depois que já chegou — decidido
    pelo maior rank de status já atingido no HISTÓRICO da issue (issue_field_changes), não só
    o status atual (uma issue pode estar bloqueada em "Is Blocked" hoje mas já ter passado
    por Testing antes de travar).
    """
    issues = (
        db.query(Issue)
        .join(IssueSprint, IssueSprint.issue_id == Issue.id)
        .filter(
            IssueSprint.sprint_id == sprint_id,
            IssueSprint.is_current.is_(True),
            Issue.assignee_person_id.isnot(None),
        )
        .all()
    )
    if not issues:
        return {"statuses": [], "rows": []}

    issue_ids = [issue.id for issue in issues]
    status_changes = (
        db.query(IssueFieldChange.issue_id, IssueFieldChange.to_value)
        .filter(IssueFieldChange.issue_id.in_(issue_ids), IssueFieldChange.field_name == "status")
        .all()
    )
    max_rank_reached: dict[int, int] = {}
    for issue_id, to_value in status_changes:
        rank = status_rank(to_value or "")
        if rank > max_rank_reached.get(issue_id, -1):
            max_rank_reached[issue_id] = rank

    people_by_id = {
        person.id: person
        for person in db.query(Person).filter(Person.id.in_({issue.assignee_person_id for issue in issues}))
    }

    matrix: dict[str, dict[str, dict[str, int]]] = {}
    all_statuses: set[str] = set()
    for issue in issues:
        person = people_by_id.get(issue.assignee_person_id)
        if person is None:
            continue
        reached_rank = max(max_rank_reached.get(issue.id, -1), status_rank(issue.status))
        has_reached_to_test = reached_rank >= _TO_TEST_RANK
        seconds = (issue.time_spent_seconds if has_reached_to_test else issue.original_estimate_seconds) or 0

        all_statuses.add(issue.status)
        row = matrix.setdefault(person.display_name, {})
        cell = row.setdefault(issue.status, {"count": 0, "seconds": 0})
        cell["count"] += 1
        cell["seconds"] += seconds

    ordered_statuses = sort_status_list(all_statuses)
    rows = [
        {"person": person_name, "cells": cells}
        for person_name, cells in sorted(matrix.items(), key=lambda item: item[0])
    ]
    return {"statuses": ordered_statuses, "rows": rows}
