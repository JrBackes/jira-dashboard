"""Agregações de métricas de sprint. Rotas só validam parâmetros e delegam para cá."""

from collections import Counter
from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Board, Issue, IssueFieldChange, IssueLink, IssueSprint, Person, Project, Sprint
from app.services.status_order import is_blocked, sort_status_list, sort_statuses, status_rank

_TO_TEST_RANK = status_rank("to test")
_READY_RANK = status_rank("deploy para prod")
_STALLED_DAYS_THRESHOLD = 2
_DEADLINE_DAYS_THRESHOLD = 2


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


def _next_deploy_date(reference: datetime) -> date | None:
    """Próxima janela de deploy, dado o calendário do time: deploy roda até quinta à tarde
    (sexta só em emergência); o que sobra vai pra segunda de manhã da semana seguinte.

    Retorna None se `reference` cai dentro da janela normal (segunda a quinta — deploy ainda
    pode acontecer nesta semana); retorna a data da próxima segunda-feira caso contrário.
    """
    weekday = reference.weekday()  # segunda=0 ... domingo=6
    if weekday <= 3:  # segunda a quinta
        return None
    days_until_monday = (7 - weekday) % 7 or 7
    return (reference + timedelta(days=days_until_monday)).date()


def sprint_risk_items(db: Session, sprint: Sprint) -> dict:
    """Itens da sprint atual com sinais de risco de não fechar a tempo (uma issue pode acumular mais de um):

    - "migrated": já esteve em sprint(s) anteriores antes desta (mais de uma linha em issue_sprints).
    - "stalled": sem mudança de status há >= STALLED_DAYS_THRESHOLD dias (último issue_field_changes
      de field_name="status", ou created_at se a issue nunca mudou de status).
    - "blocked": status atual é "Is Blocked".
    - "behind_schedule": faltam <= DEADLINE_DAYS_THRESHOLD dias pro fim da sprint e a issue ainda
      não chegou em "To Test" pelo status atual.

    Limiares (2 dias parado, 2 dias pro fim da sprint) calibrados pra sprints de 1 semana, a
    pedido do usuário — ver docs/problemas-dashboard.md.

    Itens em "Deploy para prod" já estão prontos, mas ainda aguardam a janela de deploy (até
    quinta à tarde; o resto vai pra segunda de manhã seguinte) — contados em
    `awaiting_deploy_count`. Itens depois disso no fluxo ("To Review"/"Review",
    "Waiting Store Approval", "Reviewed") **já estão em produção** — contados em
    `in_production_count`, sem relação com a janela de deploy. Nenhum dos dois grupos gera
    tag de risco, mesmo parados há dias: ficar parado ali é esperado, não um sinal de problema.
    """
    issues = (
        db.query(Issue)
        .join(IssueSprint, IssueSprint.issue_id == Issue.id)
        .filter(IssueSprint.sprint_id == sprint.id, IssueSprint.is_current.is_(True))
        .all()
    )
    if not issues:
        return {
            "days_remaining": None,
            "total_items": 0,
            "at_risk_count": 0,
            "awaiting_deploy_count": 0,
            "in_production_count": 0,
            "next_deploy_date": None,
            "items": [],
        }

    issue_ids = [issue.id for issue in issues]

    sprint_visit_counts = dict(
        db.query(IssueSprint.issue_id, func.count(IssueSprint.id))
        .filter(IssueSprint.issue_id.in_(issue_ids))
        .group_by(IssueSprint.issue_id)
        .all()
    )
    last_status_change = dict(
        db.query(IssueFieldChange.issue_id, func.max(IssueFieldChange.changed_at))
        .filter(IssueFieldChange.issue_id.in_(issue_ids), IssueFieldChange.field_name == "status")
        .group_by(IssueFieldChange.issue_id)
        .all()
    )
    people_by_id = {
        person.id: person
        for person in db.query(Person).filter(
            Person.id.in_({issue.assignee_person_id for issue in issues if issue.assignee_person_id})
        )
    }

    now = datetime.utcnow()
    days_remaining = (sprint.end_date - now).days if sprint.end_date else None

    items = []
    awaiting_deploy_count = 0
    in_production_count = 0
    for issue in issues:
        last_change = last_status_change.get(issue.id, issue.created_at)
        days_stalled = (now - last_change).days

        current_rank = status_rank(issue.status)
        if current_rank == _READY_RANK:
            awaiting_deploy_count += 1
            continue
        if current_rank > _READY_RANK:
            in_production_count += 1
            continue

        tags = []
        if sprint_visit_counts.get(issue.id, 1) > 1:
            tags.append("migrated")

        if days_stalled >= _STALLED_DAYS_THRESHOLD:
            tags.append("stalled")

        if is_blocked(issue.status):
            tags.append("blocked")

        if (
            days_remaining is not None
            and days_remaining <= _DEADLINE_DAYS_THRESHOLD
            and status_rank(issue.status) < _TO_TEST_RANK
        ):
            tags.append("behind_schedule")

        if not tags:
            continue

        person = people_by_id.get(issue.assignee_person_id)
        items.append(
            {
                "issue_key": issue.jira_key,
                "summary": issue.summary,
                "status": issue.status,
                "assignee": person.display_name if person else None,
                "tags": tags,
                "days_stalled": days_stalled,
            }
        )

    items.sort(key=lambda item: len(item["tags"]), reverse=True)
    return {
        "days_remaining": days_remaining,
        "total_items": len(issues),
        "at_risk_count": len(items),
        "awaiting_deploy_count": awaiting_deploy_count,
        "in_production_count": in_production_count,
        "next_deploy_date": _next_deploy_date(now) if awaiting_deploy_count > 0 else None,
        "items": items,
    }


def sprint_blocked_items(db: Session, sprint_id: int) -> list[dict]:
    """Itens com status "Is Blocked" na sprint atual, com o motivo do bloqueio a partir do
    vínculo nativo do Jira (`issuelinks`, tipo "Blocks", direção "inward" == "is blocked by").

    Uma issue pode estar bloqueada sem vínculo formal registrado (combinado verbalmente, ou o
    vínculo não foi criado no Jira) — nesse caso aparece com `blockers: []`, só sinalizando que
    está bloqueada sem motivo rastreável.

    Prioriza o status ao vivo da issue bloqueadora (via `Issue.jira_key`) quando ela também é
    sincronizada por nós; cai pro snapshot salvo em `IssueLink.linked_status` quando não é
    (ex: vínculo pra issue de outro projeto/site que não sincronizamos).

    `blocked_since` é o momento da mudança de status mais recente **para** "Is Blocked"
    (`issue_field_changes`, `field_name="status"`) — se a issue nunca teve essa transição
    registrada (ex: já nasceu bloqueada, sem changelog prévio), cai para a última mudança de
    status de qualquer tipo e, na ausência de qualquer changelog, para `created_at`.
    """
    issues = (
        db.query(Issue)
        .join(IssueSprint, IssueSprint.issue_id == Issue.id)
        .filter(IssueSprint.sprint_id == sprint_id, IssueSprint.is_current.is_(True))
        .filter(Issue.status.ilike("is blocked"))
        .all()
    )
    if not issues:
        return []

    issue_ids = [issue.id for issue in issues]

    status_changes = (
        db.query(IssueFieldChange.issue_id, IssueFieldChange.to_value, IssueFieldChange.changed_at)
        .filter(IssueFieldChange.issue_id.in_(issue_ids), IssueFieldChange.field_name == "status")
        .all()
    )
    blocked_since: dict[int, datetime] = {}
    last_status_change: dict[int, datetime] = {}
    for issue_id, to_value, changed_at in status_changes:
        last_status_change[issue_id] = max(last_status_change.get(issue_id, changed_at), changed_at)
        if is_blocked(to_value or ""):
            blocked_since[issue_id] = max(blocked_since.get(issue_id, changed_at), changed_at)

    links = (
        db.query(IssueLink)
        .filter(
            IssueLink.issue_id.in_(issue_ids),
            IssueLink.direction == "inward",
            IssueLink.link_type_name == "Blocks",
        )
        .all()
    )
    links_by_issue: dict[int, list[IssueLink]] = {}
    for link in links:
        links_by_issue.setdefault(link.issue_id, []).append(link)

    linked_keys = {link.linked_jira_key for link in links}
    live_status_by_key = (
        {row.jira_key: row.status for row in db.query(Issue).filter(Issue.jira_key.in_(linked_keys))}
        if linked_keys
        else {}
    )

    people_by_id = {
        person.id: person
        for person in db.query(Person).filter(
            Person.id.in_({issue.assignee_person_id for issue in issues if issue.assignee_person_id})
        )
    }

    now = datetime.utcnow()
    result = []
    for issue in issues:
        person = people_by_id.get(issue.assignee_person_id)
        blockers = [
            {
                "issue_key": link.linked_jira_key,
                "summary": link.linked_summary,
                "status": live_status_by_key.get(link.linked_jira_key, link.linked_status),
            }
            for link in links_by_issue.get(issue.id, [])
        ]
        since = blocked_since.get(issue.id) or last_status_change.get(issue.id) or issue.created_at
        result.append(
            {
                "issue_key": issue.jira_key,
                "summary": issue.summary,
                "assignee": person.display_name if person else None,
                "blockers": blockers,
                "blocked_since": since,
                "days_blocked": (now - since).days,
            }
        )
    return result
