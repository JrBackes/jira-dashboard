# Jira Dashboard MBC

Dashboard interna para métricas de sprint e de pessoas a partir dos projetos Jira **TEC** (Sistema MBC) e **CAP** (Capela).

Contexto completo do projeto, arquitetura e convenções: ver [`AGENTS.md`](./AGENTS.md).

## Setup rápido

```bash
cp .env.example .env   # preencher credenciais do Jira (TEC e CAP) e do Postgres

docker compose up db -d
cd backend && poetry install && poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload   # http://localhost:8000/api/health

poetry run python -m app.cli.sync --all   # popula o banco

cd ../frontend && npm install && npm run dev   # http://localhost:5173
```

Progresso e estado atual do projeto: [`PROGRESS.md`](./PROGRESS.md). Tarefas pendentes: [`TASKS.md`](./TASKS.md).
