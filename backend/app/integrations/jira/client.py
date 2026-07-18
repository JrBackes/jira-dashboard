from typing import Any

import httpx

from app.core.config import JiraSiteSettings
from app.integrations.jira.auth import basic_auth

DEFAULT_SEARCH_FIELDS = [
    "summary",
    "status",
    "issuetype",
    "priority",
    "assignee",
    "reporter",
    "created",
    "updated",
    "resolutiondate",
    "timeoriginalestimate",
    "timespent",
]
# Não existem campos literais "sprint"/"closedSprints" no Platform Search API v3 — isso é
# só da Agile API. Aqui o campo Sprint é um customfield (ver mappers.find_sprint_field),
# adicionado dinamicamente à lista de fields por quem monta a busca (sync_service).


class JiraClient:
    """Client HTTP próprio para o Jira Cloud REST API (Platform v3 + Agile 1.0).

    Não usa o MCP do Atlassian: esta app roda de forma independente/agendada.
    """

    def __init__(self, site_settings: JiraSiteSettings, story_points_field: str | None = None):
        self._story_points_field = story_points_field
        self._client = httpx.Client(
            base_url=site_settings.base_url.rstrip("/"),
            auth=basic_auth(site_settings),
            headers={"Accept": "application/json"},
            timeout=30.0,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "JiraClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # --- Agile API -----------------------------------------------------

    def list_boards(self, project_key: str) -> list[dict]:
        boards: list[dict] = []
        start_at = 0
        while True:
            resp = self._client.get(
                "/rest/agile/1.0/board",
                params={"projectKeyOrId": project_key, "startAt": start_at, "maxResults": 50},
            )
            resp.raise_for_status()
            data = resp.json()
            boards.extend(data["values"])
            if data.get("isLast", True):
                break
            start_at += len(data["values"])
        return boards

    def list_sprints(self, board_id: str, state: str | None = None) -> list[dict]:
        sprints: list[dict] = []
        start_at = 0
        params: dict[str, Any] = {"startAt": 0, "maxResults": 50}
        if state:
            params["state"] = state
        while True:
            params["startAt"] = start_at
            resp = self._client.get(f"/rest/agile/1.0/board/{board_id}/sprint", params=params)
            resp.raise_for_status()
            data = resp.json()
            sprints.extend(data["values"])
            if data.get("isLast", True):
                break
            start_at += len(data["values"])
        return sprints

    # --- Platform API v3 -------------------------------------------------

    def get_fields(self) -> list[dict]:
        resp = self._client.get("/rest/api/3/field")
        resp.raise_for_status()
        return resp.json()

    def search_issues(
        self,
        jql: str,
        fields: list[str] | None = None,
        next_page_token: str | None = None,
        max_results: int = 100,
    ) -> dict:
        """POST /rest/api/3/search/jql — o antigo /search está desativado (410) desde ago/2025."""
        body: dict[str, Any] = {
            "jql": jql,
            "fields": fields or DEFAULT_SEARCH_FIELDS,
            "maxResults": max_results,
        }
        if next_page_token:
            body["nextPageToken"] = next_page_token
        resp = self._client.post("/rest/api/3/search/jql", json=body)
        resp.raise_for_status()
        return resp.json()

    def iter_search_issues(self, jql: str, fields: list[str] | None = None):
        next_page_token: str | None = None
        while True:
            page = self.search_issues(jql, fields=fields, next_page_token=next_page_token)
            yield from page["issues"]
            next_page_token = page.get("nextPageToken")
            if not next_page_token:
                break

    def fetch_changelogs_bulk(self, issue_ids: list[str], batch_size: int = 1000) -> list[dict]:
        """POST /rest/api/3/changelog/bulkfetch — changelog de várias issues de uma vez.

        A API rejeita (400) lotes grandes demais num único request — paginamos em
        lotes de `batch_size` (1000 já confirmado como aceito) e concatenamos o resultado.
        """
        if not issue_ids:
            return []
        results: list[dict] = []
        for start in range(0, len(issue_ids), batch_size):
            batch = issue_ids[start : start + batch_size]
            resp = self._client.post("/rest/api/3/changelog/bulkfetch", json={"issueIdsOrKeys": batch})
            resp.raise_for_status()
            results.extend(resp.json()["issueChangeLogs"])
        return results
