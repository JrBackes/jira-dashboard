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
`id`, `site_id` (FK), `project_id` (FK), `jira_issue_id`, `jira_key`, `issue_type`, `summary`, `status`, `status_category`, `priority`, `assignee_person_id` (FK, nullable), `reporter_person_id` (FK, nullable), `story_points` (nullable, **não usado pelo time** — ver abaixo), `original_estimate_seconds` (nullable), `time_spent_seconds` (nullable), `created_at`, `updated_at`, `resolved_at`, `raw_payload` (JSONB).

`original_estimate_seconds`/`time_spent_seconds` vêm dos campos nativos de time tracking do Jira (`timeoriginalestimate`/`timespent`, em segundos) — o time não estima em Story Points, estima em tempo. Usados na tabela colaborador×status da Sprint Atual: estimativa original enquanto a issue não chegou em "To Test" (ver `docs/workflow-do-time.md`), tempo gasto (apontamento manual) depois disso — decidido pelo maior status já atingido no **histórico** da issue (`issue_field_changes`), não só o status atual.

`parent_jira_key` (nullable, sem FK) vem do campo de sistema `parent` do Jira — para issues de nível 0 (Tarefa/História/Bug) é o Epic; para Subtarefas é o item pai (não necessariamente um Epic). Usado para vincular issues ao Mapa de Tecnologia (ver `tech_map_entries`).

Unique constraint: `(site_id, jira_issue_id)`. Índice em `updated_at` (crítico para sync incremental).

### `issue_sprints`
Relação issue↔sprint. `issue_id` (FK), `sprint_id` (FK), `is_current` (bool). Populada a partir dos campos `sprint`/`closedSprints` que a Agile API já retorna nativamente — não depende de parsear changelog.

### `issue_links`
Vínculos entre issues, a partir do campo `issuelinks` do Jira — tabela **genérica**, guarda todos os tipos de vínculo (`Blocks`, `Relates`, `Duplicate`, `Cloners`, etc.), não só bloqueio. `id`, `issue_id` (FK), `jira_link_id`, `link_type_name` (ex: "Blocks"), `direction` (`inward`/`outward` — o sentido do vínculo a partir desta issue), `label` (texto legível, ex: "is blocked by"/"blocks"), `linked_jira_key`, `linked_summary`, `linked_status` (snapshot do status da issue vinculada no momento do sync — usado como fallback quando essa issue não é sincronizada por nós, ex: outro projeto/site).

"Motivo de bloqueio" (`sprint_blocked_items` em `sprint_metrics.py`) é uma query filtrando `link_type_name = 'Blocks'` e `direction = 'inward'` sobre esta tabela — sem tabela nova, mesmo padrão de extensibilidade de `issue_field_changes`. Unique constraint: `(issue_id, jira_link_id)`. Sync substitui o conjunto de vínculos por issue a cada ciclo (adiciona novos, atualiza existentes, remove os que saíram do Jira).

### `issue_field_changes`
Tabela **genérica** de changelog — não limitada a mudanças de `status`. `id`, `issue_id` (FK), `jira_changelog_entry_id` (unique, garante idempotência em re-syncs), `field_name`, `from_value`, `to_value`, `from_status_category`/`to_status_category` (nullable, preenchidos só quando `field_name = 'status'`), `changed_at`, `changed_by_person_id` (FK), `sync_run_id` (FK).

Este é o ponto-chave de extensibilidade: métricas de "atuações na sprint" (itens que mudaram de status, entraram/saíram, planned vs delivered) são **queries** sobre esta tabela cruzando com `issue_sprints` e as datas da sprint. Uma métrica nova sobre reassignment ou mudança de prioridade não exige nova tabela, só nova query sobre dado já sincronizado.

### `sync_runs`
Auditoria de execuções de sync. `id`, `site_id` (FK), `entity_type`, `started_at`, `finished_at`, `status`, `records_processed`, `error_message`.

### `sync_cursors`
Suporte a sync incremental. `site_id` (FK), `entity_type` (`issues`, `changelog`), `last_synced_at` ou `last_page_token`.

### `tech_map_entries`
Linhas do **Mapa de Tecnologia** — planilha Google Sheets externa (fora do Jira), aba "[Desenvolvimento] Planejamento Q3", uma linha por iniciativa de produto. `id`, `sheet_name`, `row_index`, `status`, `frente`, `tarefa`, `atuantes`, `ice_impacto`/`ice_confianca`/`ice_facilidade`/`ice_score`, `entrega`, `tamanho_projeto`, `motivo`, `lancamento`, `epic_jira_key` (nullable), `raw_row` (JSONB, linha inteira incluindo os marcadores semanais P/E/R não promovidos a coluna), `synced_at`.

Sem FK pra `issues` — o vínculo é textual (`epic_jira_key` ↔ `issues.jira_key` de um Epic), mesmo padrão de `issue_links.linked_jira_key`. **Vínculo é curado manualmente** na própria planilha (coluna "Epic Jira") — casamento automático por texto entre `tarefa` e o summary do Epic foi testado e descartado por não confiável (ver `docs/problemas-dashboard.md`, problema 3).

**Importação sem credencial do Google:** Google Cloud está fora de alcance neste ambiente (sem admin/projeto disponível) e a planilha não pode ficar acessível por link (dado sensível) — descartada a integração via service account/API. Importação é manual: alguém abre a planilha, copia a aba (Ctrl+C, formato TSV nativo do clipboard do Sheets) e cola numa caixa de texto na aba Atualização (`POST /api/tech-map/import`, `tech_map_service.import_tech_map_from_tsv`). Faz replace completo por `sheet_name` a cada importação — a planilha não tem ID estável de linha e o volume é baixo (~dezenas de linhas), sem necessidade de diff incremental. Parsing (`app/integrations/google_sheets/mappers.py`) é por nome de coluna no cabeçalho, não posição fixa.

**Validado com a planilha real** (2026-07-20, 50 linhas importadas): "Atuantes" é uma única coluna com texto já unido por vírgula (ex: "PO,UX,BACK,FRONT"); "ICE" de fato são 4 colunas adjacentes (Impacto/Confiança/Facilidade/Score) — o parsing lida com os dois casos igual, sem precisar saber a largura de antemão (lê da âncora até a próxima âncora conhecida no cabeçalho).

## Índices relevantes

- `issues(updated_at)`
- `issue_field_changes(changed_at, field_name)`
- `issue_field_changes(issue_id)`
- `issue_sprints(sprint_id)`

## Extensibilidade

`raw_payload` (JSONB) em `issues` (e futuramente `sprints`) é a ferramenta principal: campos ainda não modelados como coluna ficam acessíveis via JSON, promovíveis a coluna real depois via migration, sem precisar re-sincronizar dados já baixados.
