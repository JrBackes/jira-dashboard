# Tasks

Checklist vivo. Ao pegar uma tarefa, marque em andamento (comentário ou mova para "Em andamento"); ao terminar, marque `[x]` com data.

## Infra

- [x] `[Infra]` 2026-07-18 — git init + estrutura de docs compartilhadas
- [x] `[Infra]` 2026-07-18 — docker-compose.yml com serviço `db` (Postgres) + `.env.example` — validado (`docker compose up db` saudável)
- [x] `[Infra]` 2026-07-18 — Dockerfile do backend, serviço `backend` no docker-compose

## Backend

- [x] `[Back]` 2026-07-18 — Skeleton FastAPI (`main.py`, `core/config.py`, `core/db.py`, `/api/health`, `/api/health/db`) — validado via curl
- [x] `[Back]` 2026-07-18 — Models SQLAlchemy (sites, projects, boards, sprints, people, person_identities, issues, issue_sprints, issue_field_changes, sync_runs, sync_cursors)
- [x] `[Back]` 2026-07-18 — Alembic configurado + migration inicial — validado (`alembic upgrade head`, 12 tabelas criadas)
- [x] `[Back]` 2026-07-18 — `JiraClient` (integrations/jira/client.py) — boards, sprints, search/jql, changelog bulkfetch, fields
- [x] `[Back]` 2026-07-18 — `sync_service.py` — pipeline de bootstrap + issues + changelog
- [x] `[Back]` 2026-07-18 — CLI de sync (`cli/sync.py`) — `python -m app.cli.sync --site TEC|CAP|--all` (sem subcomando `run` — comportamento padrão do Typer com um único comando)
- [x] `[Back]` 2026-07-18 — `sprint_metrics.py` + rotas de sprint (summary, scope-changes, burndown, velocity-history) — validado com dados sintéticos (rollback ao final, banco limpo)
- [x] `[Back]` 2026-07-18 — `person_metrics.py` + rotas de pessoa (workload, highlights) — validado com dados sintéticos
- [x] `[Back]` 2026-07-18 — `original_estimate_seconds`/`time_spent_seconds` em `issues` (campos nativos `timeoriginalestimate`/`timespent`) + migration + re-sync (6224/6504 issues preenchidas no TEC)
- [x] `[Back]` 2026-07-18 — `sprint_workload_by_status_and_person` + rota `/api/sprints/{id}/workload-by-status` — matriz colaborador×status com tempo (estimativa antes de "To Test", tempo gasto depois) — validado com dados reais da sprint ativa
- [ ] `[Back]` (conhecido, não bloqueante) `from_status_category`/`to_status_category` em `issue_field_changes` não são preenchidos ainda no sync — hoje só `from_value`/`to_value` (nome do status). Resolver quando alguma métrica precisar filtrar por categoria de status na mudança.
- [x] `[Back]` 2026-07-18 — `POST /api/sync/trigger` (dispara sync em background, guard contra duplicado) + `GET /api/sync/status` (último `SyncRun` por site) — `api/routes/sync.py` — validado end-to-end via curl
- [x] `[Back]` 2026-07-18 — `sprint_risk_items` + rota `/api/sprints/{id}/risk` (painel "Itens em risco", problema 1 de `docs/problemas-dashboard.md`) — tags `migrated`/`stalled`/`blocked`/`behind_schedule` — validado com dados reais da sprint ativa (TEC)
- [x] `[Back]` 2026-07-18 — Model `IssueLink` + migration `98aa33c46478` (tabela genérica de vínculos entre issues, campo `issuelinks` do Jira) + `map_issue_links` + `_upsert_issue_links` no sync + `sprint_blocked_items`/rota `/api/sprints/{id}/blocked` (motivo de bloqueio via vínculo "Blocks", `blocked_since`/`days_blocked` via `issue_field_changes`) — re-sync completo rodado pra popular retroativamente (3138 vínculos)
- [x] `[Back]` 2026-07-18 — **Bug corrigido:** `changelog/bulkfetch` ignorava paginação (`nextPageToken`) dentro de cada lote de 1000 issueIds — só 470/9088 issues do TEC tinham changelog real. Corrigido em `JiraClient.fetch_changelogs_bulk` + dedup por `set()` em `_sync_changelog_for_issues` (2º bug: registro duplicado entre páginas + `autoflush=False` causava `UniqueViolation` desfazendo o sync). Re-sync completo: 9084/9088 issues do TEC agora com changelog real (194959 linhas). Ver `docs/decisions/0003-bugs-primeiro-sync-real.md` (itens 6 e 7).
- [x] `[Back]` 2026-07-18 — `weekly_time_ranking` + rota `/api/people/ranking/weekly` (ranking da semana, problema 2 de `docs/problemas-dashboard.md`) — soma deltas positivos de `field_name="timespent"` em `issue_field_changes` por pessoa, contra esperado de 5 dias × 6h — validado com dados reais (TEC e CAP)
- [x] `[Back]` 2026-07-18 — **Bug corrigido:** `accountId` do Jira compartilhado entre TEC e CAP pra 2 pessoas (robert.bonfada, Victor Amaral) criava pessoas canônicas duplicadas em `people` (regra em `AGENTS.md` sobre accountId ser único por site estava errada). Mesclados os duplicados, `_resolve_person` corrigido pra checar `jira_account_id` em qualquer site antes de criar pessoa nova. Ver `docs/decisions/0004-pessoas-duplicadas-accountid-compartilhado.md`.
- [x] `[Back]` 2026-07-18 — `weekly_time_ranking` restrito a issues da sprint atualmente ativa (`IssueSprint.is_current` + `Sprint.state == "active"`) — apontamento fora da sprint em questão não conta mais
- [x] `[Back]` 2026-07-20 — `weekly_time_ranking` ganhou parâmetro `sprint_id` opcional (None = todas as sprints, valor específico = filtra por essa sprint) — rota `/api/people/ranking/weekly?sprint_id=`
- [x] `[Back]` 2026-07-20 — `person_workload` também ganhou `sprint_id` opcional (mesmo padrão) — rota `/api/people/{id}/workload?sprint_id=`, pra "Carga de trabalho atual" respeitar o seletor de sprint da `PeoplePage`
- [x] `[Back]` 2026-07-20 — `daily_time_breakdown` + rota `/api/people/ranking/daily` (matriz pessoa×dia, ritmo diário vs 6h/dia esperado) — helper `_positive_timespent_deltas` compartilhado com `weekly_time_ranking` — validado com dados reais (hoje + `reference=2026-07-16`)
- [x] `[Back]` 2026-07-20 — `_sprint_entry_at` + ajuste em `_positive_timespent_deltas`: não conta apontamento de tempo feito antes da issue entrar na sprint selecionada — aplicado nos rankings semanal e diário
- [x] `[Back]` 2026-07-20 — **Correção do critério acima:** `_status_at` + `_ADVANCED_ENTRY_RANK` — exclui TODO apontamento de issues cujo status, no momento em que entraram na sprint atual, já era Under PR Review ou mais avançado (a checagem só por hora de entrada não bastava, rollover do Jira move issues novas e migradas no mesmo instante). Validado: `diogo.bastos` caiu de 96300s pra 92700s no TEC/sprint 138, ~29 issues dele confirmadas entrando já em "To Test"/"Deploy para prod".
- [x] `[Back]` 2026-07-20 — `issues.parent_jira_key` (campo de sistema `parent` do Jira) sincronizado + migration — re-sync completo: 6828/9097 issues do TEC agora com Epic vinculado
- [x] `[Back]` 2026-07-20 — ~~Integração Google Sheets via service account~~ — implementada e depois **descartada**: usuário não pode usar Google Cloud (fora de alcance). `google-auth`/`requests`/`cryptography` removidos do `pyproject.toml`.
- [x] `[Back]` 2026-07-20 — Model `TechMapEntry` + migration + `tech_map_service.import_tech_map_from_tsv` (importação por colar/paste, TSV) + rotas `POST /api/tech-map/import` e `GET /api/tech-map/sprints/{id}` — validado com dados sintéticos e **depois com a planilha real (50 linhas, 2026-07-20)**: Status/Frente/Tarefa/Atuantes/ICE/Entrega todos corretos; "Epic Jira" ainda vazia (usuário não preencheu ainda, comportamento esperado)
- [x] `[Back]` 2026-07-20 — `backend/app/integrations/google_sheets/mappers.py` (parser por nome de coluna, robusto a colunas "largas" tipo Atuantes/ICE) reaproveitado da tentativa com service account — formato-agnóstico, funciona igual com TSV colado
- [x] `[Back]` 2026-07-20 — Bug de ambiente (`cryptography`/"Illegal Instruction", `docs/decisions/0005`) **revertido junto com a remoção da dependência** — não é mais um risco pro projeto

## Frontend

- [x] `[Front]` 2026-07-18 — Skeleton Vite + React + TS + React Query + Recharts + React Router — `tsc --noEmit` limpo, todos os módulos transpilam via Vite dev server
- [x] `[Front]` 2026-07-18 — `OverviewPage` (seletor de site/projeto TEC/CAP)
- [x] `[Front]` 2026-07-18 — `CurrentSprintPage` (burndown, scope changes, velocity)
- [x] `[Front]` 2026-07-18 — `PeoplePage` (carga de trabalho, destaques)
- [x] `[Front]` 2026-07-18 — `SprintWorkloadTable` (tabela colaborador×status com contagem + tempo) na `CurrentSprintPage` — `tsc --noEmit` limpo, módulos validados via Vite
- [x] `[Front]` 2026-07-18 — `SyncPage` (`/atualizacao`) — botão "Atualizar agora" + tabela de status/última atualização por site, polling automático enquanto algum site está `running`. Botão mostra "Atualizando..." (e fica desabilitado) imediatamente ao clicar.
- [x] `[Front]` 2026-07-18 — Corrigido: botão ficava preso em "Atualizando..." e outras páginas não atualizavam sem reload manual. `refetchInterval` trocado de função (inspecionando `query.state.data`) para valor reativo simples (`isTriggering || hasSeenRunning`); adicionado gate "só destrava depois de confirmar que viu `running` pelo menos uma vez"; timeout de segurança de 3min pra nunca travar pra sempre; e `queryClient.invalidateQueries()` (sem filtro) disparado quando uma atualização termina, pra sprints/pessoas virem atualizados na próxima navegação sem precisar dar reload na página.
- [x] `[Front]` 2026-07-18 — `SprintRiskPanel` (painel "Itens em risco") na `CurrentSprintPage` — `tsc --noEmit` limpo
- [x] `[Front]` 2026-07-18 — `BlockedItemsPanel` (seção "Itens bloqueados", com motivo via vínculos do Jira) na `CurrentSprintPage` — `tsc --noEmit` limpo
- [x] `[Front]` 2026-07-18 — `WeeklyRankingTable` (ranking da semana de tempo trabalhado) na `PeoplePage` — `tsc --noEmit` limpo
- [x] `[Front]` 2026-07-20 — Seletor de sprint na `PeoplePage` ("Todas as sprints" + lista, padrão = sprint ativa), alimentando ranking da semana e destaques — `tsc --noEmit` limpo
- [x] `[Front]` 2026-07-20 — `DailyRankingTable` (ranking diário, matriz pessoa×dia com ↑/↓ vs 6h esperado) abaixo do ranking da semana na `PeoplePage` — `tsc --noEmit` limpo
- [x] `[Front]` 2026-07-20 — `TechMapPanel` (seção "Mapa de Tecnologia", issues da sprint agrupadas por Epic + Frente/Status/ICE/Entrega) na `CurrentSprintPage` — `tsc --noEmit` limpo
- [x] `[Front]` 2026-07-20 — Seção de importação do Mapa de Tecnologia (caixa de texto + botão "Importar") na `SyncPage` (aba Atualização) — `apiPost` ganhou suporte a body JSON — `tsc --noEmit` limpo
- [ ] `[Front]` (pendente) Validação visual no navegador — Claude Code não tem ferramenta de screenshot/browser neste ambiente; abrir http://localhost:5173 manualmente para confirmar renderização

## Docs

- [x] `[Docs]` 2026-07-18 — `AGENTS.md`, `CLAUDE.md`, `PROGRESS.md`, `TASKS.md`
- [x] `[Docs]` 2026-07-18 — `docs/data-model.md` preenchido
- [x] `[Docs]` 2026-07-18 — `docs/jira-integration.md` preenchido (customfields reais de Story Points e Sprint por site, formato real do changelog/bulkfetch, statusCategory.key)

## Pendências (aguardando o usuário)

- [x] 2026-07-18 — Tokens de API Jira gerados e `.env` preenchido para TEC e CAP
- [x] 2026-07-18 — Primeiro sync real rodado com sucesso, após corrigir 5 bugs encontrados no processo (ver notas abaixo): TEC (9054 issues, 142 sprints, 50 pessoas, 10000 mudanças de changelog, 16525 vínculos issue↔sprint), CAP (34 issues, 3 sprints, 4 pessoas, 70 mudanças, 28 vínculos)
- [ ] Confirmar visualmente no navegador (http://localhost:5173) que as 3 páginas renderizam corretamente com os dados reais
- [x] 2026-07-20 — Primeira importação real do Mapa de Tecnologia feita pelo usuário (50 linhas, colar/paste na aba Atualização) — validada, todas as colunas batendo
- [ ] Mapa de Tecnologia: preencher a coluna "Epic Jira" na aba "[Desenvolvimento] Planejamento Q3" (planilha `MAPA 2026 - Tecnologia`) com a chave do Epic nas linhas já identificadas, depois reimportar (colar de novo na seção "Mapa de Tecnologia" da aba Atualização) pros vínculos aparecerem

## Notas técnicas relevantes

- CLI de sync não tem subcomando `run` — é `python -m app.cli.sync --site TEC|CAP` ou `--all` (comportamento padrão do Typer com um único comando registrado).
- Ver `docs/decisions/0002-sem-poetry-no-dockerfile.md`: o Dockerfile do backend usa `pip install .` direto, não instala Poetry (causava crash `Illegal instruction` neste ambiente).
- Ver `docs/decisions/0003-bugs-primeiro-sync-real.md`: cinco bugs encontrados e corrigidos rodando o primeiro sync contra o Jira real — limite de lote do `changelog/bulkfetch` (max ~1000), chave `changeHistories`/timestamp epoch no payload, colunas `from_value`/`to_value` precisam ser `Text`, campo Sprint é customfield (não `sprint`/`closedSprints` literal) — sem isso `issue_sprints` ficava vazia, e `statusCategory.key` em vez de `.name` (localizado) — sem isso workload/highlights/velocity nunca batiam com "done".
- Time do TEC não usa Story Points — métricas em pontos sempre 0 até o time estimar; métricas por contagem de itens funcionam normalmente.
- `list_people` (Por Pessoa) só mostra quem já foi **assignee** de alguma issue — exclui reporters/autores de changelog que nunca pegaram uma issue pra si (gente de outras áreas, bots como "Automation for Jira"). TEC: 20 pessoas, CAP: 2 pessoas.
- Carga de trabalho (`person_workload`) e contagem por status da sprint (`sprint_status_counts`) agrupam pelo `status` granular do time, não mais pelas 3 categorias genéricas do Jira — ordenados pela ordem lógica do fluxo (`app/services/status_order.py`). Fluxo completo (11 etapas, Backlog → ... → Reviewed) com o significado de cada status registrado em `docs/workflow-do-time.md`, explicado 1 a 1 pelo usuário — inclui correções importantes sobre suposições erradas que eu tinha feito antes (`Under PR Review` não é sinônimo de `To Review`; `Reviewed` é o estado final pós-produção, não sinônimo de `Review`; `Deploy para prod` vem antes de `To Review`, não depois).
- Time do TEC estima em **tempo** (campos nativos `timeoriginalestimate`/`timespent`), não em Story Points — a tabela colaborador×status da Sprint Atual usa isso: estimativa original antes da issue chegar em "To Test" (checando o **histórico** de status, não só o status atual — uma issue pode estar "Is Blocked" hoje já tendo passado por Testing antes), tempo gasto (apontamento manual) depois.
- **`docker compose restart backend` não recarrega o `.env`** — precisa `docker compose up -d --force-recreate backend` (ou `down`+`up`) quando credenciais/variáveis mudam. Causou um bug real: o container ficou rodando com placeholders vazios de Jira por várias sessões de restart, falhando silenciosamente no sync via `/api/sync/trigger` (só visível nos logs do container). Ver `AGENTS.md`.
- Ainda não há agendamento automático (cron/scheduler) — o sync só roda quando alguém dispara manualmente (CLI ou botão "Atualizar agora" na aba `/atualizacao`).
- **Mudança de dependência Python exige rebuild da imagem Docker** (`docker compose build backend`) — `restart`/`up -d --force-recreate` sozinhos usam a imagem já construída em cache, sem os pacotes novos.
- Ver `docs/decisions/0005-cryptography-pin-illegal-instruction.md` (marcado **revertido**): `cryptography>=43` travava com `Illegal Instruction` neste ambiente arm64 ao usar RSA — só relevante se essa dependência for reintroduzida no futuro (a integração que a motivou, service account do Google, foi descartada).
- Mapa de Tecnologia não tem sync automático — Google Cloud está fora de alcance neste ambiente (sem admin/projeto disponível) e a planilha não pode ficar acessível por link. Importação é manual: colar o conteúdo copiado da aba na seção "Mapa de Tecnologia" da aba Atualização.
