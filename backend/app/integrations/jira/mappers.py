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
        # Campos nativos de time tracking do Jira (system fields, não customfield — nome fixo).
        # O time não usa Story Points; usa "Estimativa original" e apontamento manual de horas.
        "original_estimate_seconds": fields.get("timeoriginalestimate"),
        "time_spent_seconds": fields.get("timespent"),
        # Campo de sistema "parent" — pra issues de nível 0 é o Epic; usado pra vincular ao
        # Mapa de Tecnologia (ver TechMapEntry.epic_jira_key).
        "parent_jira_key": (fields.get("parent") or {}).get("key"),
        "created_at": parse_jira_datetime(fields.get("created")),
        "updated_at": parse_jira_datetime(fields.get("updated")),
        "resolved_at": parse_jira_datetime(fields.get("resolutiondate")),
        "raw_payload": issue,
        "sprint_jira_ids": sprint_jira_ids,
        "current_sprint_jira_id": current_sprint_jira_id,
    }


def map_issue_links(issue: dict) -> list[dict]:
    """Achata `fields.issuelinks[]` — cada entrada tem `inwardIssue` OU `outwardIssue`, nunca os dois.

    `type.inward`/`type.outward` são o texto legível da relação a partir desta issue (ex: para
    o tipo "Blocks", inward = "is blocked by", outward = "blocks"). "Motivo de bloqueio" é
    filtrar por `link_type_name == "Blocks"` e `direction == "inward"` sobre o resultado disto.
    """
    links: list[dict] = []
    for link in issue["fields"].get("issuelinks") or []:
        link_type = link.get("type") or {}
        if "inwardIssue" in link:
            direction, label, target = "inward", link_type.get("inward", ""), link["inwardIssue"]
        elif "outwardIssue" in link:
            direction, label, target = "outward", link_type.get("outward", ""), link["outwardIssue"]
        else:
            continue
        target_fields = target.get("fields") or {}
        links.append(
            {
                "jira_link_id": link["id"],
                "link_type_name": link_type.get("name", "Unknown"),
                "direction": direction,
                "label": label,
                "linked_jira_key": target["key"],
                "linked_summary": target_fields.get("summary") or "",
                "linked_status": (target_fields.get("status") or {}).get("name"),
            }
        )
    return links


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
