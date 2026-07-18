# AGENTS.md — Contexto do projeto Jira Dashboard MBC

Este arquivo é a **fonte única de verdade** para qualquer assistente de codificação (Claude Code, Antigravity, ou outro) trabalhando neste repositório.

**Antes de começar a trabalhar:** leia este arquivo inteiro, depois a seção "Estado Atual" de `PROGRESS.md`, depois `TASKS.md`.
**Ao terminar uma sessão de trabalho:** atualize `PROGRESS.md` (nova entrada no log) e `TASKS.md` (marque o que avançou).

## O que é este projeto

Dashboard web para visualizar dados do Jira (projetos, sprints, pessoas) da Minha Biblioteca Católica (MBC). Cobre dois projetos Jira em dois sites Atlassian diferentes:

- **TEC** — Sistema MBC, site principal.
- **CAP** — Capela, site `biblioteca-capela.atlassian.net`.

Ambos são boards Scrum, com sprints.

Métricas da v1: (1) atuações/movimentações durante a sprint (planejado vs entregue, burndown, histórico de velocity); (2) por pessoa (carga de trabalho atual, destaques de entrega). O schema foi desenhado para suportar novas métricas sem redesenho — ver `docs/data-model.md`.

## Arquitetura

- **Backend:** FastAPI (Python), em `backend/`.
- **Frontend:** React + Vite (TypeScript), em `frontend/`.
- **Banco de dados:** PostgreSQL, via Docker Compose local (serviço `db`).
- **Sincronização com Jira:** client HTTP próprio (`backend/app/integrations/jira/client.py`), **não usa MCP** — a app roda de forma independente/agendada, sem assistente de IA no loop.

Ver `docs/data-model.md` para o schema completo e `docs/jira-integration.md` para detalhes da integração com a API do Jira.

## Regras fáceis de esquecer

- O endpoint `GET/POST /rest/api/3/search` do Jira Cloud está **desativado (410)** desde ago/2025. Usar sempre `POST /rest/api/3/search/jql` (paginação por `nextPageToken`, não `startAt`).
- Changelog em lote: `POST /rest/api/3/changelog/bulkfetch` — preferir a buscar changelog issue a issue.
- Sprints e boards vêm da **Agile API** (`/rest/agile/1.0/...`), não da Platform API.
- Credenciais do Jira ficam **só em `.env`** (nunca no banco, nunca commitadas). Um par de credenciais por site: `JIRA_TEC_*` e `JIRA_CAP_*`.
- `accountId` do Jira é por instância Atlassian — a mesma pessoa em TEC e CAP tem dois `accountId` diferentes. Por isso existe `people` (canônica) + `person_identities` (por site).
- O nome do customfield de Story Points varia por instância Atlassian — resolvido em runtime via `JiraClient.get_fields()`, não hardcoded.
- `issue_field_changes` é uma tabela genérica de changelog (qualquer campo, não só `status`). Métricas novas sobre o histórico devem ser queries sobre essa tabela, não uma tabela nova.
- O CLI de sync **não tem subcomando `run`**: é `python -m app.cli.sync --site TEC|CAP` ou `--all` (comportamento padrão do Typer quando só há um comando registrado).
- O `backend/Dockerfile` **não instala o Poetry** dentro da imagem — usa `pip install .` direto sobre o `pyproject.toml`. Instalar Poetry no Dockerfile causou crash (`Illegal instruction`) neste ambiente por causa de dependências transitivas do Poetry (cryptography/keyring). Ver `docs/decisions/0002-sem-poetry-no-dockerfile.md` antes de mudar isso.

## Comandos de desenvolvimento

```bash
# Subir Postgres local
docker compose up db

# Backend (dentro de backend/, com Poetry)
poetry install
poetry run uvicorn app.main:app --reload

# Migrations
poetry run alembic upgrade head
poetry run alembic revision --autogenerate -m "descrição"

# Sync manual com o Jira
poetry run python -m app.cli.sync --site TEC
poetry run python -m app.cli.sync --site CAP
poetry run python -m app.cli.sync --all

# Frontend (dentro de frontend/)
npm install
npm run dev
```

## Convenções de código

- Python: type hints em tudo, Pydantic para schemas de API, SQLAlchemy ORM para models.
- Lógica de negócio (agregações de métricas, pipeline de sync) vive em `backend/app/services/`, nunca direto nas rotas — rotas só validam parâmetros e delegam.
- Toda tabela sincronizada do Jira guarda `raw_payload` (JSONB) do payload original — é o mecanismo de extensibilidade: campo novo vira coluna via migration depois, sem precisar re-sincronizar.
- Frontend: componentes de gráfico reutilizáveis em `src/components/charts/`; chamadas de API tipadas em `src/api/`, uma por recurso.

## Decisões arquiteturais

Decisões com custo real de reversão ficam registradas em `docs/decisions/` (formato ADR-lite: Contexto / Decisão / Consequências). Mudanças de rotina não precisam de ADR — só uma entrada em `PROGRESS.md`.
