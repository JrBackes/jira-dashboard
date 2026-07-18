# 0001 — Tabela genérica de changelog em vez de tabelas por tipo de mudança

## Contexto

A dashboard precisa calcular métricas de "atuações na sprint" (itens que mudaram de status, entraram/saíram da sprint, planejado vs entregue) a partir do histórico de mudanças das issues do Jira. A primeira versão cobre apenas mudanças de `status`, mas o usuário já sinalizou que vai querer adicionar métricas novas ao longo do tempo (ex: reassignment, mudança de prioridade).

## Decisão

Modelar `issue_field_changes` como tabela genérica de changelog — um registro por mudança de campo (`field_name`, `from_value`, `to_value`), não limitada a `status`. Nenhuma tabela específica por tipo de mudança (ex: `status_transitions`, `reassignments`).

## Consequências

- Métricas novas sobre o histórico de qualquer campo são implementadas como queries sobre `issue_field_changes`, sem migration de schema.
- Queries de métricas de status precisam filtrar `field_name = 'status'` explicitamente (leve custo de verbosidade na query, aceitável).
- `jira_changelog_entry_id` como chave única garante idempotência em re-syncs, independente de quantos campos diferentes a tabela acabe armazenando.
