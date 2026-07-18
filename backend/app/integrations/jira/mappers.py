"""Conversão de payloads da API do Jira para dicts prontos para upsert nos models."""

from datetime import datetime, timezone
from typing import Any


def parse_jira_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def parse_jira_changelog_timestamp(value: int | None) -> datetime | None:
    """O campo `created` do changelog/bulkfetch vem como epoch em milissegundos (int), não ISO string."""
    if not value:
        return None
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc)


def map_board(board: dict) -> dict:
    return {
        "jira_board_id": str(board["id"]),
        "name": board["name"],
        "type": board.get("type", "scrum"),
    }


def map_sprint(sprint: dict) -> dict:
    return {
        "jira_sprint_id": str(sprint["id"]),
        "name": sprint["name"],
        "state": sprint["state"],
        "start_date": parse_jira_datetime(sprint.get("startDate")),
        "end_date": parse_jira_datetime(sprint.get("endDate")),
        "complete_date": parse_jira_datetime(sprint.get("completeDate")),
        "goal": sprint.get("goal"),
    }


def _status_category(status_field: dict | None) -> str:
    """Usa `statusCategory.key` (estável: new|indeterminate|done), não `.name` (localizado — ex: 'Itens concluídos' em instâncias em português)."""
    if not status_field:
        return "unknown"
    return status_field.get("statusCategory", {}).get("key", "unknown")


def map_issue(issue: dict, story_points_field: str | None, sprint_field: str | None) -> dict:
    fields = issue["fields"]
    status = fields.get("status") or {}

    # O campo "Sprint" (customfield_XXXXX, descoberto via get_fields()) retorna a lista de
    # TODAS as sprints por onde a issue já passou, cada uma com seu próprio "state". Não existem
    # campos literais "sprint"/"closedSprints" no Platform Search API — isso é da Agile API.
    sprint_history: list[dict] = (fields.get(sprint_field) if sprint_field else None) or []
    sprint_jira_ids = {str(s["id"]) for s in sprint_history}
    current_sprint_jira_id = next(
        (str(s["id"]) for s in sprint_history if s.get("state") in ("active", "future")), None
    )

    return {
        "jira_issue_id": str(issue["id"]),
        "jira_key": issue["key"],
        "issue_type": (fields.get("issuetype") or {}).get("name", "Unknown"),
        "summary": fields.get("summary") or "",
        "status": status.get("name", "Unknown"),
        "status_category": _status_category(status),
        "priority": (fields.get("priority") or {}).get("name"),
        "assignee": fields.get("assignee"),
        "reporter": fields.get("reporter"),
        "story_points": fields.get(story_points_field) if story_points_field else None,
        "created_at": parse_jira_datetime(fields.get("created")),
        "updated_at": parse_jira_datetime(fields.get("updated")),
        "resolved_at": parse_jira_datetime(fields.get("resolutiondate")),
        "raw_payload": issue,
        "sprint_jira_ids": sprint_jira_ids,
        "current_sprint_jira_id": current_sprint_jira_id,
    }


def map_changelog_entries(issue_changelog: dict) -> list[dict]:
    """Achata os histories[].items[] do changelog de uma issue em uma linha por mudança de campo."""
    entries: list[dict] = []
    for history in issue_changelog.get("changeHistories", []):
        changed_at = parse_jira_changelog_timestamp(history["created"])
        author = history.get("author")
        for idx, item in enumerate(history.get("items", [])):
            entries.append(
                {
                    "jira_changelog_entry_id": f"{history['id']}:{idx}",
                    "field_name": item.get("field", "unknown"),
                    "from_value": item.get("fromString"),
                    "to_value": item.get("toString"),
                    "changed_at": changed_at,
                    "author": author,
                }
            )
    return entries


def find_story_points_field(fields: list[dict[str, Any]]) -> str | None:
    """Descobre o customfield de Story Points (nome varia por instância Atlassian)."""
    for field in fields:
        name = field.get("name", "").strip().lower()
        if name == "story points" or name == "story point estimate":
            return field["id"]
    return None


def find_sprint_field(fields: list[dict[str, Any]]) -> str | None:
    """Descobre o customfield de Sprint (tipicamente customfield_10020, mas varia por instância)."""
    for field in fields:
        schema = field.get("schema", {})
        if schema.get("custom") == "com.pyxis.greenhopper.jira:gh-sprint":
            return field["id"]
    return None
