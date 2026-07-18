# Modelo de dados

Schema PostgreSQL, gerenciado via Alembic (`backend/alembic/`). Descrição narrativa — a fonte de verdade estrutural são as migrations.

## Visão geral

O modelo é relativamente normalizado (não é um cache raso da resposta da API do Jira), para suportar métricas de sprint e de pessoa hoje, e permitir novas métricas no futuro via query, sem redesenho de schema.

## Tabelas

### `sites`
Um site Atlassian (`TEC`, `CAP`). Campos: `id`, `key`, `name`, `base_url`, `jira_cloud_id`. **Sem credenciais** — ficam só em `.env`.

### `projects`
Projeto Jira dentro de um site. `id`, `site_id` (FK), `jira_project_id`, `jira_key`, `name`.

### `boards`
Board Jira (Scrum) de um projeto. `id`, `project_id` (FK), `jira_board_id`, `name`, `type`.

### `sprints`
Sprint de um board. `id`, `board_id` (FK), `jira_sprint_id`, `name`, `state` (`future`/`active`/`closed`), `start_date`, `end_date`, `complete_date`, `goal`.

### `people` + `person_identities`
Pessoa canônica (`people`: `id`, `display_name`, `email`) separada de identidade por site (`person_identities`: `id`, `person_id` FK, `site_id` FK, `jira_account_id`, `display_name`, `email`, `active`), porque o `accountId` do Jira é por instância Atlassian — a mesma pessoa em TEC e CAP tem dois `accountId` diferentes. O vínculo entre identidades é resolvido manualmente (tipicamente por e-mail), não por lógica automática.

### `issues`
`id`, `site_id` (FK), `project_id` (FK), `jira_issue_id`, `jira_key`, `issue_type`, `summary`, `status`, `status_category`, `priority`, `assignee_person_id` (FK, nullable), `reporter_person_id` (FK, nullable), `story_points` (nullable), `created_at`, `updated_at`, `resolved_at`, `raw_payload` (JSONB).

Unique constraint: `(site_id, jira_issue_id)`. Índice em `updated_at` (crítico para sync incremental).

### `issue_sprints`
Relação issue↔sprint. `issue_id` (FK), `sprint_id` (FK), `is_current` (bool). Populada a partir dos campos `sprint`/`closedSprints` que a Agile API já retorna nativamente — não depende de parsear changelog.

### `issue_field_changes`
Tabela **genérica** de changelog — não limitada a mudanças de `status`. `id`, `issue_id` (FK), `jira_changelog_entry_id` (unique, garante idempotência em re-syncs), `field_name`, `from_value`, `to_value`, `from_status_category`/`to_status_category` (nullable, preenchidos só quando `field_name = 'status'`), `changed_at`, `changed_by_person_id` (FK), `sync_run_id` (FK).

Este é o ponto-chave de extensibilidade: métricas de "atuações na sprint" (itens que mudaram de status, entraram/saíram, planned vs delivered) são **queries** sobre esta tabela cruzando com `issue_sprints` e as datas da sprint. Uma métrica nova sobre reassignment ou mudança de prioridade não exige nova tabela, só nova query sobre dado já sincronizado.

### `sync_runs`
Auditoria de execuções de sync. `id`, `site_id` (FK), `entity_type`, `started_at`, `finished_at`, `status`, `records_processed`, `error_message`.

### `sync_cursors`
Suporte a sync incremental. `site_id` (FK), `entity_type` (`issues`, `changelog`), `last_synced_at` ou `last_page_token`.

## Índices relevantes

- `issues(updated_at)`
- `issue_field_changes(changed_at, field_name)`
- `issue_field_changes(issue_id)`
- `issue_sprints(sprint_id)`

## Extensibilidade

`raw_payload` (JSONB) em `issues` (e futuramente `sprints`) é a ferramenta principal: campos ainda não modelados como coluna ficam acessíveis via JSON, promovíveis a coluna real depois via migration, sem precisar re-sincronizar dados já baixados.
