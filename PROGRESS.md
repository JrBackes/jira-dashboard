# Progresso

## Estado Atual

- **Pronto:** setup completo de ponta a ponta — docs compartilhadas, docker-compose (Postgres + backend), schema PostgreSQL (12 tabelas, migration inicial via Alembic), `JiraClient` + pipeline de sync + CLI, rotas de métricas de sprint e de pessoa, frontend React+Vite com as 3 páginas (Visão Geral, Sprint Atual, Por Pessoa) consumindo a API real. Todas as camadas validadas rodando (Postgres saudável, `/api/health` e `/api/health/db` respondendo via container Docker, métricas testadas com dados sintéticos com rollback, frontend compilando limpo via `tsc` e Vite).
- **Em andamento:** nada em execução — ponto de partida limpo para o próximo passo.
- **Próximo passo:** preencher `.env` com credenciais reais do Jira (TEC e CAP) e rodar o primeiro sync real (`poetry run python -m app.cli.sync --all` dentro de `backend/`), depois abrir http://localhost:5173 para validar visualmente as telas com dados reais.

## Log

### 2026-07-18 — Claude Code
- Repositório criado em `~/Projects/jira-dashboard-mbc`, `git init` feito.
- Criada estrutura de documentação compartilhada entre Claude Code e Antigravity (`AGENTS.md`, `CLAUDE.md` stub, `PROGRESS.md`, `TASKS.md`, `docs/data-model.md`, `docs/jira-integration.md`, `docs/decisions/`).
- Ambiente local preparado: Homebrew (`python@3.12`, `pipx`), Poetry via pipx. Docker Desktop iniciado.
- `docker-compose.yml` com serviço `db` (Postgres 16) — validado saudável.
- Skeleton do backend FastAPI (`core/config.py`, `core/db.py`, `/api/health`, `/api/health/db`) — validado localmente via `poetry run uvicorn`.
- Schema PostgreSQL completo (sites, projects, boards, sprints, people/person_identities, issues, issue_sprints, issue_field_changes, sync_runs, sync_cursors) + migration inicial via Alembic — aplicada, 12 tabelas confirmadas.
- `JiraClient` (Agile API + `/search/jql` + `changelog/bulkfetch` + `/field`), mappers, `sync_service.py` (pipeline bootstrap → issues → changelog) e CLI (`app.cli.sync`) — smoke-testado (falha esperada por falta de credenciais reais no `.env`, confirmando que a validação de config funciona).
- `sprint_metrics.py` e `person_metrics.py` + rotas (`/api/sites`, `/api/sprints/...`, `/api/people/...`) — testados com dados sintéticos inseridos em transação com rollback (banco ficou limpo).
- Frontend Vite+React+TS com React Query, Recharts, React Router: `OverviewPage`, `CurrentSprintPage`, `PeoplePage`, componentes de gráfico reutilizáveis. `tsc --noEmit` limpo; todos os módulos transpilam via Vite dev server. **Não foi possível tirar screenshot/validar visualmente no navegador** — este ambiente não tem ferramenta de browser/screenshot; recomendo abrir http://localhost:5173 manualmente para conferir.
- Corrigido `backend/Dockerfile`: a primeira versão instalava Poetry dentro da imagem, o que causava crash (`Illegal instruction`) por causa de dependências transitivas do Poetry. Troquado para `pip install .` direto — build e `docker compose up` validados de ponta a ponta (health check respondendo via container). Decisão registrada em `docs/decisions/0002-sem-poetry-no-dockerfile.md`.
- Pendências para o usuário: gerar tokens de API do Jira para TEC e CAP, preencher `.env`, rodar o primeiro sync real.
