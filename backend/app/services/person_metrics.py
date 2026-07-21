"""Agregações de métricas por pessoa: carga de trabalho e destaques de entrega."""

from collections import Counter
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Issue, IssueFieldChange, IssueSprint, Person, Project, Sprint
from app.services.status_order import sort_statuses, status_rank

_WORKDAYS_PER_WEEK = 5
_HOURS_PER_WORKDAY = 6
_EXPECTED_WEEK_SECONDS = _WORKDAYS_PER_WEEK * _HOURS_PER_WORKDAY * 3600
_ADVANCED_ENTRY_RANK = status_rank("under pr review")


def list_people(db: Session, project_key: str | None = None) -> list[Person]:
    """Só pessoas que já foram assignee de alguma issue — exclui reporters/autores de
    changelog que nunca pegaram uma issue pra si (ex: gente de outras áreas que só abriu
    um chamado, bots como "Automation for Jira")."""
    query = db.query(Person).join(Issue, Issue.assignee_person_id == Person.id).distinct()
    if project_key:
        query = query.join(Project, Project.id == Issue.project_id).filter(Project.jira_key == project_key)
    return query.order_by(Person.display_name).all()


def get_person(db: Session, person_id: int) -> Person | None:
    return db.get(Person, person_id)


def person_workload(
    db: Session, person_id: int, project_key: str | None = None, sprint_id: int | None = None
) -> dict[str, int]:
    """Agrupa por status real (Backlog, To Do, In Progress, Is Blocked, To Test...), não pela
    categoria genérica do Jira — o time tem um fluxo mais granular que 'new/indeterminate/done'.

    `sprint_id` restringe a issues vinculadas a essa sprint (qualquer vínculo em `issue_sprints`,
    não só `is_current` — mesmo comportamento do filtro de sprint em `weekly_time_ranking`/
    `person_highlights`); `sprint_id=None` ("todas as sprints") não filtra por sprint.
    """
    query = db.query(Issue).filter(Issue.assignee_person_id == person_id, Issue.status_category != "done")
    if sprint_id is not None:
        query = query.join(IssueSprint, IssueSprint.issue_id == Issue.id).filter(IssueSprint.sprint_id == sprint_id)
    if project_key:
        query = query.join(Project, Project.id == Issue.project_id).filter(Project.jira_key == project_key)
    issues = query.all()
    return sort_statuses(dict(Counter(issue.status for issue in issues)))


def person_highlights(db: Session, person_id: int, sprint_id: int | None = None) -> list[Issue]:
    query = db.query(Issue).filter(Issue.assignee_person_id == person_id, Issue.status_category == "done")
    if sprint_id:
        query = query.join(IssueSprint, IssueSprint.issue_id == Issue.id).filter(IssueSprint.sprint_id == sprint_id)
    return query.order_by(Issue.resolved_at.desc()).limit(20).all()


def _workweek_bounds(reference: date) -> tuple[datetime, datetime]:
    """Segunda a sexta da semana civil de `reference` — janela de apontamento pro ranking
    (fim de semana não conta pro benchmark de "semana cheia", 5 dias)."""
    monday = reference - timedelta(days=reference.weekday())
    start = datetime.combine(monday, datetime.min.time())
    end = datetime.combine(monday + timedelta(days=4), datetime.max.time())
    return start, end


def _sprint_entry_at(db: Session, sprint_id: int, issue_ids: list[int]) -> dict[int, datetime]:
    """Pra cada issue, o momento mais recente em que ela entrou nesta sprint específica —
    via changelog do campo "Sprint" (nome da sprint aparecendo no `to_value` sem estar no
    `from_value`, mesma lógica de `sprint_scope_changes`). Issues sem esse evento registrado
    (ex: já nasceram nesta sprint, sem changelog de campo Sprint) não entram no dict — tratadas
    como "sempre estiveram aqui", sem restrição adicional.
    """
    if not issue_ids:
        return {}
    sprint = db.get(Sprint, sprint_id)
    if sprint is None:
        return {}
    changes = (
        db.query(
            IssueFieldChange.issue_id, IssueFieldChange.from_value, IssueFieldChange.to_value, IssueFieldChange.changed_at
        )
        .filter(IssueFieldChange.issue_id.in_(issue_ids), IssueFieldChange.field_name == "Sprint")
        .all()
    )
    entry_at: dict[int, datetime] = {}
    for issue_id, from_value, to_value, changed_at in changes:
        if sprint.name in (to_value or "") and sprint.name not in (from_value or ""):
            if entry_at.get(issue_id) is None or changed_at > entry_at[issue_id]:
                entry_at[issue_id] = changed_at
    return entry_at


def _status_at(db: Session, issue_ids: list[int], as_of: dict[int, datetime]) -> dict[int, str]:
    """Pra cada issue em `as_of` (issue_id -> momento de referência), o status conhecido
    naquele momento — a mudança de status mais recente com `changed_at <= as_of[issue_id]`.
    Issues sem histórico de status até esse momento ficam de fora do resultado (tratadas como
    status desconhecido pelo chamador, não excluídas por precaução — dado incompleto não deve
    apagar apontamento real)."""
    if not issue_ids or not as_of:
        return {}
    changes = (
        db.query(IssueFieldChange.issue_id, IssueFieldChange.to_value, IssueFieldChange.changed_at)
        .filter(IssueFieldChange.issue_id.in_(issue_ids), IssueFieldChange.field_name == "status")
        .all()
    )
    latest: dict[int, tuple[datetime, str]] = {}
    for issue_id, to_value, changed_at in changes:
        reference = as_of.get(issue_id)
        if reference is None or changed_at > reference:
            continue
        current = latest.get(issue_id)
        if current is None or changed_at > current[0]:
            latest[issue_id] = (changed_at, to_value or "")
    return {issue_id: status for issue_id, (_when, status) in latest.items()}


def _positive_timespent_deltas(
    db: Session,
    window_start: datetime,
    window_end: datetime,
    project_key: str | None,
    sprint_id: int | None,
) -> list[tuple[int, int, datetime]]:
    """Deltas positivos de `timespent` (pessoa, segundos, quando) numa janela de tempo —
    base compartilhada entre `weekly_time_ranking` e `daily_time_breakdown`. Deltas negativos
    (edição pra baixo, correção de apontamento) não contam como trabalho, são descartados.

    `sprint_id` restringe a issues vinculadas a essa sprint específica (qualquer vínculo em
    `issue_sprints`, não só `is_current` — o usuário escolheu essa sprint explicitamente no
    seletor do frontend); `sprint_id=None` ("tudo") não filtra por sprint.

    Achado do usuário (2026-07-20): issues que migram já avançadas (Under PR Review, To Test,
    Testing, Deploy pra prod, To Review, Reviewed) da sprint anterior recebem apontamento
    residual nesta semana que não representa trabalho novo — o desenvolvimento de verdade já
    aconteceu numa sprint passada. Duas regras, quando `sprint_id` é informado:

    1. Se o status da issue **no momento em que ela entrou nesta sprint** já era Under PR
       Review ou mais avançado no fluxo (`_ADVANCED_ENTRY_RANK`), ela chegou "quase pronta" —
       TODO apontamento dela fica de fora desta semana, mesmo o que foi logado depois de
       entrar (não é trabalho novo desta sprint, é fechamento de algo já feito antes).
       Corrige uma tentativa anterior (só olhar a hora de entrada, sem o status): não
       funcionava porque o rollover de sprint do Jira move issues novas e migradas no mesmo
       evento em lote, então a hora de entrada sozinha não distinguia as duas.
    2. Pras demais issues (entrada "não avançada", ou sem histórico pra saber), continua
       descartando apontamento logado **antes** de a issue ter entrado nesta sprint
       (`_sprint_entry_at`) — ex: issue começou a semana em outra sprint/backlog e só entrou
       na sprint atual no meio da semana.
    """
    query = (
        db.query(
            IssueFieldChange.issue_id,
            IssueFieldChange.changed_by_person_id,
            IssueFieldChange.from_value,
            IssueFieldChange.to_value,
            IssueFieldChange.changed_at,
        )
        .join(Issue, Issue.id == IssueFieldChange.issue_id)
        .filter(
            IssueFieldChange.field_name == "timespent",
            IssueFieldChange.changed_by_person_id.isnot(None),
            IssueFieldChange.changed_at >= window_start,
            IssueFieldChange.changed_at <= window_end,
        )
    )
    if sprint_id is not None:
        query = query.join(IssueSprint, IssueSprint.issue_id == Issue.id).filter(IssueSprint.sprint_id == sprint_id)
    if project_key:
        query = query.join(Project, Project.id == Issue.project_id).filter(Project.jira_key == project_key)

    rows = query.all()

    entry_at: dict[int, datetime] = {}
    excluded_issue_ids: set[int] = set()
    if sprint_id is not None:
        issue_ids = list({issue_id for issue_id, *_ in rows})
        entry_at = _sprint_entry_at(db, sprint_id, issue_ids)
        status_at_entry = _status_at(db, issue_ids, entry_at)
        excluded_issue_ids = {
            issue_id for issue_id, status in status_at_entry.items() if status_rank(status) >= _ADVANCED_ENTRY_RANK
        }

    deltas: list[tuple[int, int, datetime]] = []
    for issue_id, person_id, from_value, to_value, changed_at in rows:
        if issue_id in excluded_issue_ids:
            continue
        before = int(from_value) if from_value else 0
        after = int(to_value) if to_value else 0
        delta = after - before
        if delta <= 0:
            continue
        entered_at = entry_at.get(issue_id)
        if entered_at is not None and changed_at < entered_at:
            continue
        deltas.append((person_id, delta, changed_at))
    return deltas


def weekly_time_ranking(
    db: Session, project_key: str | None = None, sprint_id: int | None = None, reference: date | None = None
) -> dict:
    """Ranking de tempo trabalhado na semana (segunda a sexta), contra o esperado de uma
    semana cheia (5 dias x 6h = 30h).

    O time não usa o worklog formal do Jira (com descrição por apontamento) — só atualiza o
    campo agregado "Tempo gasto" (`timespent`) direto na issue. Mas cada atualização desse
    campo já gera uma entrada no changelog (`issue_field_changes`, `field_name="timespent"`)
    com o valor antes/depois, quem mudou e quando — dá pra reconstruir quanto cada pessoa
    logou **nesta semana** (ver `_positive_timespent_deltas`).
    """
    reference = reference or datetime.utcnow().date()
    week_start, week_end = _workweek_bounds(reference)
    deltas = _positive_timespent_deltas(db, week_start, week_end, project_key, sprint_id)

    totals: dict[int, int] = {}
    for person_id, delta, _changed_at in deltas:
        totals[person_id] = totals.get(person_id, 0) + delta

    people_by_id = {p.id: p for p in db.query(Person).filter(Person.id.in_(totals.keys()))} if totals else {}

    ranking = [
        {
            "person": people_by_id[person_id].display_name,
            "seconds": seconds,
            "percent_of_expected": round(seconds / _EXPECTED_WEEK_SECONDS * 100, 1),
        }
        for person_id, seconds in totals.items()
        if person_id in people_by_id
    ]
    ranking.sort(key=lambda row: row["seconds"], reverse=True)

    return {
        "week_start": week_start.date(),
        "week_end": week_end.date(),
        "expected_seconds": _EXPECTED_WEEK_SECONDS,
        "ranking": ranking,
    }


def daily_time_breakdown(
    db: Session, project_key: str | None = None, sprint_id: int | None = None, reference: date | None = None
) -> dict:
    """Matriz pessoa × dia: tempo logado por dia útil já decorrido na semana (segunda até hoje,
    ou até sexta se hoje já passou da semana), contra o esperado de 6h/dia — a pedido do
    usuário, pra comparar ritmo diário ("passou 1 dia = 6h, entregou mais ou menos que isso"),
    não só o total da semana inteira.
    """
    reference = reference or datetime.utcnow().date()
    week_start, week_end = _workweek_bounds(reference)
    last_day = min(reference, week_end.date())
    num_days = (last_day - week_start.date()).days + 1
    days = [week_start.date() + timedelta(days=i) for i in range(num_days)]

    window_end = datetime.combine(last_day, datetime.max.time())
    deltas = _positive_timespent_deltas(db, week_start, window_end, project_key, sprint_id)

    per_person_per_day: dict[int, dict[date, int]] = {}
    for person_id, delta, changed_at in deltas:
        per_day = per_person_per_day.setdefault(person_id, {})
        day = changed_at.date()
        per_day[day] = per_day.get(day, 0) + delta

    people_by_id = (
        {p.id: p for p in db.query(Person).filter(Person.id.in_(per_person_per_day.keys()))}
        if per_person_per_day
        else {}
    )

    expected_per_day_seconds = _EXPECTED_WEEK_SECONDS // _WORKDAYS_PER_WEEK
    rows = []
    for person_id, per_day in per_person_per_day.items():
        person = people_by_id.get(person_id)
        if person is None:
            continue
        total_seconds = sum(per_day.values())
        rows.append(
            {
                "person": person.display_name,
                "cells": {day.isoformat(): per_day.get(day, 0) for day in days},
                "total_seconds": total_seconds,
                "expected_total_seconds": expected_per_day_seconds * len(days),
            }
        )
    rows.sort(key=lambda row: row["total_seconds"], reverse=True)

    return {
        "days": [day.isoformat() for day in days],
        "expected_per_day_seconds": expected_per_day_seconds,
        "rows": rows,
    }
