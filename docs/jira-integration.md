# Integração com o Jira Cloud

## Sites

| Site | Chave | Domínio | Board |
|---|---|---|---|
| Sistema MBC | `TEC` | `tibibliotecacatolica.atlassian.net` | Scrum |
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
- Não usamos `/sprint/{sprintId}/issue` (a issue search inteira roda via Platform API v3, ver abaixo).

### Platform API v3 (`/rest/api/3`)
- `POST /search/jql` — busca de issues via JQL. **Não usar `/search` (GET ou POST)** — está desativado (410 Gone) desde ago/2025. Paginação por `nextPageToken` (não `startAt`/`total`); `fields` deve ser explícito.
  - **Sprint não é um field literal aqui** (isso só existe na Agile API). No Platform Search API, sprint é um **customfield** (`schema.custom == "com.pyxis.greenhopper.jira:gh-sprint"`, descoberto via `get_fields()` — `customfield_10020` nos dois sites atuais, mas resolvido dinamicamente, não hardcoded). O valor retornado é a **lista completa** de sprints por onde a issue já passou, cada uma com seu `state` (`active`/`future`/`closed`) — não existe um par separado `sprint` (atual) + `closedSprints` (histórico) como na Agile API.
  - **`statusCategory.name` é localizado** (ex: "Itens concluídos" em instância PT-BR) — sempre usar `statusCategory.key` (estável: `new`/`indeterminate`/`done`) para qualquer lógica de negócio.
- `POST /changelog/bulkfetch` — changelog de várias issues de uma vez. **Limite de ~1000 issueIds por request** (lotes maiores retornam 400) — `JiraClient.fetch_changelogs_bulk` já pagina isso internamente.
  - **Formato real da resposta** (diferente do que a documentação pública sugere): `{"issueChangeLogs": [{"issueId": "...", "changeHistories": [{"id": "...", "author": {...}, "created": 1683203510869, "items": [{"field": "status", "fromString": "...", "toString": "..."}]}]}]}`.
  - `changeHistories[].created` é **epoch em milissegundos (int)**, não string ISO8601 — precisa `datetime.fromtimestamp(ms/1000, tz=UTC)`, não `fromisoformat`. Ver `docs/decisions/0003-bugs-primeiro-sync-real.md`.
- `GET /field` — lista todos os campos, usada uma vez por site para descobrir os customfields reais de Story Points e Sprint (nome/ID variam por instância Atlassian).

## Campos customizados por site

| Site | Story Points (customfield) | Sprint (customfield) |
|---|---|---|
| TEC | `customfield_10034` (nenhuma issue usa este campo neste time — ver observação abaixo) | `customfield_10020` |
| CAP | `customfield_10016` | `customfield_10020` |

**Observação:** o time do TEC não usa Story Points (0 de 9054 issues têm o campo preenchido) — métricas em pontos (burndown/velocity por pontos) sempre retornam 0 até o time começar a estimar. As métricas por contagem de itens funcionam normalmente.

## Estratégia de sync

Ver `AGENTS.md` (seção Regras fáceis de esquecer) e `services/sync_service.py`: bootstrap de metadata (projeto → boards → sprints) → issues via JQL incremental (`updated >= cursor`) → changelog em lote para issues tocadas no ciclo → atualização de `sync_cursors` e `sync_runs`.

Primeiro sync real (2026-07-18): TEC — 9054 issues, 142 sprints, 50 pessoas, 10000 mudanças de changelog. CAP — 34 issues, 3 sprints, 4 pessoas, 70 mudanças.

Execução: CLI manual (`python -m app.cli.sync --site TEC|CAP|--all`) sempre disponível. Agendamento inicial via cron do host chamando `docker compose run --rm backend python -m app.cli.sync --all`.
