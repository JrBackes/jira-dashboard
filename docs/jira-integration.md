# Integração com o Jira Cloud

## Sites

| Site | Chave | Domínio | Board |
|---|---|---|---|
| Sistema MBC | `TEC` | (definir em `.env`, `JIRA_TEC_BASE_URL`) | Scrum |
| Capela | `CAP` | `biblioteca-capela.atlassian.net` | Scrum |

## Autenticação

Basic Auth por site, com e-mail + API token (Jira Cloud). Variáveis de ambiente (`.env`, nunca commitado):

```
JIRA_TEC_BASE_URL=
JIRA_TEC_EMAIL=
JIRA_TEC_API_TOKEN=

JIRA_CAP_BASE_URL=https://biblioteca-capela.atlassian.net
JIRA_CAP_EMAIL=
JIRA_CAP_API_TOKEN=
```

Escopo necessário nos tokens: `read:jira-work`, `read:jira-user`, e acesso a changelog (verificar se o token clássico já cobre; caso use API token com escopos granulares/Connect, confirmar explicitamente).

## Endpoints usados

### Agile API (`/rest/agile/1.0`)
- `GET /board?projectKeyOrId={key}` — lista boards do projeto.
- `GET /board/{boardId}/sprint?state=active,future,closed` — lista sprints do board.
- `GET /sprint/{sprintId}/issue` — issues de uma sprint (já retorna `sprint`/`closedSprints` nos fields).

### Platform API v3 (`/rest/api/3`)
- `POST /search/jql` — busca de issues via JQL. **Não usar `/search` (GET ou POST)** — está desativado (410 Gone) desde ago/2025. Paginação por `nextPageToken` (não `startAt`/`total`); `fields` deve ser explícito.
- `POST /changelog/bulkfetch` — changelog de várias issues de uma vez. Preferir a `GET /issue/{key}/changelog` (issue a issue) para volume maior.
- `GET /field` — lista todos os campos, usada uma vez por site para descobrir o customfield real de Story Points (o nome/ID varia por instância Atlassian).

## Campos customizados por site

| Site | Story Points (customfield) |
|---|---|
| TEC | *(a preencher após primeiro `get_fields()`)* |
| CAP | *(a preencher após primeiro `get_fields()`)* |

## Estratégia de sync

Ver `AGENTS.md` (seção Regras fáceis de esquecer) e `services/sync_service.py`: bootstrap de metadata (projeto → boards → sprints) → issues via JQL incremental (`updated >= cursor`) → changelog em lote para issues tocadas no ciclo → atualização de `sync_cursors` e `sync_runs`.

Execução: CLI manual (`python -m app.cli.sync --site TEC|CAP|--all`) sempre disponível. Agendamento inicial via cron do host chamando `docker compose run --rm backend python -m app.cli.sync --all`.
