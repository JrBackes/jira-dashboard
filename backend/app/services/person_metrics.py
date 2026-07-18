"""Agregações de métricas por pessoa: carga de trabalho e destaques de entrega."""

from collections import Counter

from sqlalchemy.orm import Session

from app.models import Issue, IssueSprint, Person, PersonIdentity, Project, Site


def list_people(db: Session, project_key: str | None = None) -> list[Person]:
    query = db.query(Person)
    if project_key:
        query = (
            query.join(PersonIdentity, PersonIdentity.person_id == Person.id)
            .join(Site, Site.id == PersonIdentity.site_id)
            .join(Project, Project.site_id == Site.id)
            .filter(Project.jira_key == project_key)
            .distinct()
        )
    return query.order_by(Person.display_name).all()


def get_person(db: Session, person_id: int) -> Person | None:
    return db.get(Person, person_id)


def person_workload(db: Session, person_id: int, project_key: str | None = None) -> dict[str, int]:
    query = db.query(Issue).filter(Issue.assignee_person_id == person_id, Issue.status_category != "done")
    if project_key:
        query = query.join(Project, Project.id == Issue.project_id).filter(Project.jira_key == project_key)
    issues = query.all()
    return dict(Counter(issue.status_category for issue in issues))


def person_highlights(db: Session, person_id: int, sprint_id: int | None = None) -> list[Issue]:
    query = db.query(Issue).filter(Issue.assignee_person_id == person_id, Issue.status_category == "done")
    if sprint_id:
        query = query.join(IssueSprint, IssueSprint.issue_id == Issue.id).filter(IssueSprint.sprint_id == sprint_id)
    return query.order_by(Issue.resolved_at.desc()).limit(20).all()
