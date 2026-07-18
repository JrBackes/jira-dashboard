"""Pipeline de sincronização com o Jira: bootstrap de metadata -> issues -> changelog.

Chamado tanto pelo CLI (app/cli/sync.py) quanto por um futuro scheduler — a lógica
fica aqui, desacoplada do mecanismo de disparo.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.integrations.jira.client import DEFAULT_SEARCH_FIELDS, JiraClient
from app.integrations.jira.mappers import (
    find_sprint_field,
    find_story_points_field,
    map_board,
    map_changelog_entries,
    map_issue,
    map_sprint,
)
from app.models import (
    Board,
    Issue,
    IssueFieldChange,
    IssueSprint,
    Person,
    PersonIdentity,
    Project,
    Site,
    Sprint,
    SyncCursor,
    SyncRun,
)

# Simplificação da v1: um projeto Jira por site, com jira_key == site_key.
# Se a MBC passar a ter múltiplos projetos por site, este mapeamento vira uma tabela de config.
PROJECT_KEY_BY_SITE = {"TEC": "TEC", "CAP": "CAP"}


def _get_or_create_site(db: Session, site_key: str) -> Site:
    site_settings = get_settings().jira_site_settings(site_key)
    site = db.query(Site).filter_by(key=site_key).one_or_none()
    if site is None:
        site = Site(key=site_key, name=site_key, base_url=site_settings.base_url)
        db.add(site)
        db.flush()
    return site


def _get_or_create_project(db: Session, site: Site, jira_project_key: str, jira_project_id: str, name: str) -> Project:
    project = db.query(Project).filter_by(site_id=site.id, jira_project_id=jira_project_id).one_or_none()
    if project is None:
        project = Project(site_id=site.id, jira_project_id=jira_project_id, jira_key=jira_project_key, name=name)
        db.add(project)
        db.flush()
    return project


def _upsert_board(db: Session, project: Project, board_payload: dict) -> Board:
    data = map_board(board_payload)
    board = db.query(Board).filter_by(project_id=project.id, jira_board_id=data["jira_board_id"]).one_or_none()
    if board is None:
        board = Board(project_id=project.id, **data)
        db.add(board)
    else:
        for key, value in data.items():
            setattr(board, key, value)
    db.flush()
    return board


def _upsert_sprint(db: Session, board: Board, sprint_payload: dict) -> Sprint:
    data = map_sprint(sprint_payload)
    sprint = db.query(Sprint).filter_by(board_id=board.id, jira_sprint_id=data["jira_sprint_id"]).one_or_none()
    if sprint is None:
        sprint = Sprint(board_id=board.id, **data)
        db.add(sprint)
    else:
        for key, value in data.items():
            setattr(sprint, key, value)
    db.flush()
    return sprint


def _resolve_person(db: Session, site: Site, account: dict | None) -> int | None:
    if not account:
        return None
    account_id = account.get("accountId")
    if not account_id:
        return None
    email = account.get("emailAddress")
    display_name = account.get("displayName", "Desconhecido")

    identity = db.query(PersonIdentity).filter_by(site_id=site.id, jira_account_id=account_id).one_or_none()
    if identity:
        identity.display_name = display_name
        identity.email = email
        db.flush()
        return identity.person_id

    person = None
    if email:
        person = db.query(Person).filter_by(email=email).one_or_none()
    if person is None:
        person = Person(display_name=display_name, email=email)
        db.add(person)
        db.flush()

    identity = PersonIdentity(
        person_id=person.id,
        site_id=site.id,
        jira_account_id=account_id,
        display_name=display_name,
        email=email,
        active=True,
    )
    db.add(identity)
    db.flush()
    return person.id


def _upsert_issue(
    db: Session,
    site: Site,
    project: Project,
    issue_payload: dict,
    story_points_field: str | None,
    sprint_field: str | None,
) -> Issue:
    data = map_issue(issue_payload, story_points_field, sprint_field)
    assignee_person_id = _resolve_person(db, site, data.pop("assignee"))
    reporter_person_id = _resolve_person(db, site, data.pop("reporter"))
    sprint_jira_ids = data.pop("sprint_jira_ids")
    current_sprint_jira_id = data.pop("current_sprint_jira_id")

    issue = db.query(Issue).filter_by(site_id=site.id, jira_issue_id=data["jira_issue_id"]).one_or_none()
    if issue is None:
        issue = Issue(
            site_id=site.id,
            project_id=project.id,
            assignee_person_id=assignee_person_id,
            reporter_person_id=reporter_person_id,
            **data,
        )
        db.add(issue)
    else:
        issue.assignee_person_id = assignee_person_id
        issue.reporter_person_id = reporter_person_id
        for key, value in data.items():
            setattr(issue, key, value)
    db.flush()

    if sprint_jira_ids:
        sprints = db.query(Sprint).filter(Sprint.jira_sprint_id.in_(sprint_jira_ids)).all()
        existing_links = {link.sprint_id: link for link in db.query(IssueSprint).filter_by(issue_id=issue.id)}
        for sprint in sprints:
            is_current = sprint.jira_sprint_id == current_sprint_jira_id
            link = existing_links.get(sprint.id)
            if link is None:
                db.add(IssueSprint(issue_id=issue.id, sprint_id=sprint.id, is_current=is_current))
            else:
                link.is_current = is_current
        db.flush()

    return issue


def _sync_changelog_for_issues(
    db: Session, client: JiraClient, site: Site, sync_run: SyncRun, issues: list[Issue]
) -> int:
    if not issues:
        return 0
    by_jira_id = {issue.jira_issue_id: issue for issue in issues}
    changelogs = client.fetch_changelogs_bulk(list(by_jira_id.keys()))
    count = 0
    for issue_changelog in changelogs:
        issue = by_jira_id.get(str(issue_changelog["issueId"]))
        if issue is None:
            continue
        for entry in map_changelog_entries(issue_changelog):
            existing = (
                db.query(IssueFieldChange)
                .filter_by(jira_changelog_entry_id=entry["jira_changelog_entry_id"])
                .one_or_none()
            )
            if existing:
                continue
            changed_by_person_id = _resolve_person(db, site, entry["author"])
            db.add(
                IssueFieldChange(
                    issue_id=issue.id,
                    jira_changelog_entry_id=entry["jira_changelog_entry_id"],
                    field_name=entry["field_name"],
                    from_value=entry["from_value"],
                    to_value=entry["to_value"],
                    changed_at=entry["changed_at"],
                    changed_by_person_id=changed_by_person_id,
                    sync_run_id=sync_run.id,
                )
            )
            count += 1
    db.flush()
    return count


def sync_site(db: Session, site_key: str) -> SyncRun:
    site = _get_or_create_site(db, site_key)
    site_settings = get_settings().jira_site_settings(site_key)
    project_key = PROJECT_KEY_BY_SITE.get(site_key, site_key)

    sync_run = SyncRun(site_id=site.id, entity_type="full", started_at=datetime.now(timezone.utc), status="running")
    db.add(sync_run)
    db.commit()  # commit já aqui (não só flush) — outras sessões precisam enxergar o "running" na hora, pro guard de disparo duplicado no endpoint de trigger funcionar

    try:
        with JiraClient(site_settings) as client:
            all_fields = client.get_fields()
            story_points_field = find_story_points_field(all_fields)
            sprint_field = find_sprint_field(all_fields)
            search_fields = [*DEFAULT_SEARCH_FIELDS, *(f for f in (story_points_field, sprint_field) if f)]

            # 1. Bootstrap: projeto (assumido == site) -> boards -> sprints
            project = _get_or_create_project(db, site, project_key, project_key, project_key)
            boards = client.list_boards(project_key)
            synced_boards = [_upsert_board(db, project, b) for b in boards]
            for board in synced_boards:
                for sprint_payload in client.list_sprints(board.jira_board_id):
                    _upsert_sprint(db, board, sprint_payload)
            db.commit()

            # 2. Issues (sync incremental via cursor de updated_at)
            cursor = db.query(SyncCursor).filter_by(site_id=site.id, entity_type="issues").one_or_none()
            jql = f"project = {project_key} ORDER BY updated ASC"
            if cursor and cursor.last_synced_at:
                jql = f'project = {project_key} AND updated >= "{cursor.last_synced_at:%Y-%m-%d %H:%M}" ORDER BY updated ASC'

            touched_issues: list[Issue] = []
            latest_updated: datetime | None = None
            for issue_payload in client.iter_search_issues(jql, fields=search_fields):
                issue = _upsert_issue(db, site, project, issue_payload, story_points_field, sprint_field)
                touched_issues.append(issue)
                if issue.updated_at and (latest_updated is None or issue.updated_at > latest_updated):
                    latest_updated = issue.updated_at
            db.commit()

            # 3. Changelog em lote para as issues tocadas neste ciclo
            changes_count = _sync_changelog_for_issues(db, client, site, sync_run, touched_issues)
            db.commit()

            if latest_updated:
                if cursor is None:
                    cursor = SyncCursor(site_id=site.id, entity_type="issues", last_synced_at=latest_updated)
                    db.add(cursor)
                else:
                    cursor.last_synced_at = latest_updated

            sync_run.status = "success"
            sync_run.finished_at = datetime.now(timezone.utc)
            sync_run.records_processed = len(touched_issues) + changes_count
            db.commit()
    except Exception as exc:  # noqa: BLE001 — precisa registrar qualquer falha no sync_run
        db.rollback()
        sync_run.status = "failed"
        sync_run.finished_at = datetime.now(timezone.utc)
        sync_run.error_message = str(exc)[:2000]
        db.add(sync_run)
        db.commit()
        raise

    return sync_run
