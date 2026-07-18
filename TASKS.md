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
- [ ] `[Back]` (conhecido, não bloqueante) `from_status_category`/`to_status_category` em `issue_field_changes` não são preenchidos ainda no sync — hoje só `from_value`/`to_value` (nome do status). Resolver quando alguma métrica precisar filtrar por categoria de status na mudança.

## Frontend

- [x] `[Front]` 2026-07-18 — Skeleton Vite + React + TS + React Query + Recharts + React Router — `tsc --noEmit` limpo, todos os módulos transpilam via Vite dev server
- [x] `[Front]` 2026-07-18 — `OverviewPage` (seletor de site/projeto TEC/CAP)
- [x] `[Front]` 2026-07-18 — `CurrentSprintPage` (burndown, scope changes, velocity)
- [x] `[Front]` 2026-07-18 — `PeoplePage` (carga de trabalho, destaques)
- [ ] `[Front]` (pendente) Validação visual no navegador — Claude Code não tem ferramenta de screenshot/browser neste ambiente; abrir http://localhost:5173 manualmente para confirmar renderização

## Docs

- [x] `[Docs]` 2026-07-18 — `AGENTS.md`, `CLAUDE.md`, `PROGRESS.md`, `TASKS.md`
- [x] `[Docs]` 2026-07-18 — `docs/data-model.md` preenchido
- [x] `[Docs]` 2026-07-18 — `docs/jira-integration.md` preenchido (customfields reais de Story Points e Sprint por site, formato real do changelog/bulkfetch, statusCategory.key)

## Pendências (aguardando o usuário)

- [x] 2026-07-18 — Tokens de API Jira gerados e `.env` preenchido para TEC e CAP
- [x] 2026-07-18 — Primeiro sync real rodado com sucesso, após corrigir 5 bugs encontrados no processo (ver notas abaixo): TEC (9054 issues, 142 sprints, 50 pessoas, 10000 mudanças de changelog, 16525 vínculos issue↔sprint), CAP (34 issues, 3 sprints, 4 pessoas, 70 mudanças, 28 vínculos)
- [ ] Confirmar visualmente no navegador (http://localhost:5173) que as 3 páginas renderizam corretamente com os dados reais

## Notas técnicas relevantes

- CLI de sync não tem subcomando `run` — é `python -m app.cli.sync --site TEC|CAP` ou `--all` (comportamento padrão do Typer com um único comando registrado).
- Ver `docs/decisions/0002-sem-poetry-no-dockerfile.md`: o Dockerfile do backend usa `pip install .` direto, não instala Poetry (causava crash `Illegal instruction` neste ambiente).
- Ver `docs/decisions/0003-bugs-primeiro-sync-real.md`: cinco bugs encontrados e corrigidos rodando o primeiro sync contra o Jira real — limite de lote do `changelog/bulkfetch` (max ~1000), chave `changeHistories`/timestamp epoch no payload, colunas `from_value`/`to_value` precisam ser `Text`, campo Sprint é customfield (não `sprint`/`closedSprints` literal) — sem isso `issue_sprints` ficava vazia, e `statusCategory.key` em vez de `.name` (localizado) — sem isso workload/highlights/velocity nunca batiam com "done".
- Time do TEC não usa Story Points — métricas em pontos sempre 0 até o time estimar; métricas por contagem de itens funcionam normalmente.
- `list_people` (Por Pessoa) só mostra quem já foi **assignee** de alguma issue — exclui reporters/autores de changelog que nunca pegaram uma issue pra si (gente de outras áreas, bots como "Automation for Jira"). TEC: 20 pessoas, CAP: 2 pessoas.
- Carga de trabalho (`person_workload`) e contagem por status da sprint (`sprint_status_counts`) agrupam pelo `status` granular do time, não mais pelas 3 categorias genéricas do Jira — ordenados pela ordem lógica do fluxo (`app/services/status_order.py`). Fluxo completo (11 etapas, Backlog → ... → Reviewed) com o significado de cada status registrado em `docs/workflow-do-time.md`, explicado 1 a 1 pelo usuário — inclui correções importantes sobre suposições erradas que eu tinha feito antes (`Under PR Review` não é sinônimo de `To Review`; `Reviewed` é o estado final pós-produção, não sinônimo de `Review`; `Deploy para prod` vem antes de `To Review`, não depois).
