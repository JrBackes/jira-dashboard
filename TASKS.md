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
- [ ] `[Docs]` `docs/data-model.md` preenchido
- [ ] `[Docs]` `docs/jira-integration.md` preenchido (incluindo nome real do customfield de Story Points por site, assim que descoberto)

## Pendências (aguardando o usuário)

- [ ] Confirmar escopo dos tokens de API Jira gerados para TEC e CAP (`read:jira-work`, `read:jira-user`, changelog)
- [ ] Configurar `.env` local com credenciais reais (TEC e CAP) — nunca commitar
- [ ] Rodar primeiro sync real (`poetry run python -m app.cli.sync --all`, dentro de `backend/`) e validar dados reais nas telas
- [ ] Confirmar visualmente no navegador (http://localhost:5173) que as 3 páginas renderizam corretamente

## Notas técnicas relevantes

- CLI de sync não tem subcomando `run` — é `python -m app.cli.sync --site TEC|CAP` ou `--all` (comportamento padrão do Typer com um único comando registrado).
- Ver `docs/decisions/0002-sem-poetry-no-dockerfile.md`: o Dockerfile do backend usa `pip install .` direto, não instala Poetry (causava crash `Illegal instruction` neste ambiente).
