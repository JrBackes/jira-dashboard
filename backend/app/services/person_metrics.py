"""Agregações de métricas por pessoa: carga de trabalho e destaques de entrega."""

from collections import Counter

from sqlalchemy.orm import Session

from app.models import Issue, IssueSprint, Person, Project
from app.services.status_order import sort_statuses


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


def person_workload(db: Session, person_id: int, project_key: str | None = None) -> dict[str, int]:
    """Agrupa por status real (Backlog, To Do, In Progress, Is Blocked, To Test...), não pela
    categoria genérica do Jira — o time tem um fluxo mais granular que 'new/indeterminate/done'."""
    query = db.query(Issue).filter(Issue.assignee_person_id == person_id, Issue.status_category != "done")
    if project_key:
        query = query.join(Project, Project.id == Issue.project_id).filter(Project.jira_key == project_key)
    issues = query.all()
    return sort_statuses(dict(Counter(issue.status for issue in issues)))


def person_highlights(db: Session, person_id: int, sprint_id: int | None = None) -> list[Issue]:
    query = db.query(Issue).filter(Issue.assignee_person_id == person_id, Issue.status_category == "done")
    if sprint_id:
        query = query.join(IssueSprint, IssueSprint.issue_id == Issue.id).filter(IssueSprint.sprint_id == sprint_id)
    return query.order_by(Issue.resolved_at.desc()).limit(20).all()
