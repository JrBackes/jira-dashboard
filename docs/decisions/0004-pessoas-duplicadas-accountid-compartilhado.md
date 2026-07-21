# 0004 — Pessoas duplicadas: mesmo accountId do Jira compartilhado entre TEC e CAP

## Contexto

`AGENTS.md` documentava como regra: "`accountId` do Jira é por instância Atlassian — a mesma pessoa em TEC e CAP tem dois `accountId` diferentes". `_resolve_person` (`sync_service.py`) dependia disso: só deduplicava entre sites por e-mail: quando o e-mail não vem visível pela API (privacidade da conta Atlassian), uma pessoa que existe nos dois sites virava duas linhas em `people`, uma por site.

Ao investigar por que o "Ranking da semana" mostrava um número baixo pra `robert.bonfada`, descobri que essa regra está **errada** pelo menos para duas pessoas do time: `robert.bonfada` e `Victor Amaral` tinham o **mesmo accountId** (`712020:a280ad5f-...` e `63e40053c3eb74ad8e999503`, respectivamente) em `person_identities` para os sites TEC e CAP. Como o e-mail de ambos não é exposto pela API, `_resolve_person` nunca conseguia unificar, e cada um virava duas pessoas canônicas em `people`.

Provavelmente TEC e CAP estão na mesma organização Atlassian (mesmo diretório de usuários), o que faz o `accountId` ser compartilhado entre os dois sites para pelo menos parte do time — contrariando a suposição original.

## Correção

1. **Dados existentes (2026-07-18):** mesclados os dois pares de pessoas duplicadas — sobrevivente = menor `person_id` (TEC). Repontuados `issues.assignee_person_id`, `issues.reporter_person_id`, `issue_field_changes.changed_by_person_id` e `person_identities.person_id` pro sobrevivente; linha duplicada removida de `people`.
2. **`_resolve_person` (`sync_service.py`):** antes de cair no fallback de e-mail (ou criar pessoa nova), agora checa se já existe alguma `PersonIdentity` com o mesmo `jira_account_id` **em qualquer site** (não só no site atual) e reaproveita o `person_id` dela.

## Consequências

- Impacto real nos números encontrados: nenhum nesta semana específica (o lado CAP de `robert.bonfada` não tinha apontamento de tempo no período), mas métricas futuras que cruzem TEC+CAP por pessoa (ex: ranking combinado, workload) ficariam erradas sem essa correção se a pessoa passar a atuar nos dois sites.
- Regra em `AGENTS.md` ("accountId é sempre diferente entre sites") precisa ser tratada como **não confiável universalmente** — o código agora não depende dela pra deduplicar corretamente.
- Se o e-mail nunca é exposto pela API do Jira pra este workspace (parece ser o caso geral, não só desses dois), o accountId-cross-site é hoje o único mecanismo de dedupe entre sites — vale monitorar se aparecem novas duplicatas após syncs futuros (query: `SELECT jira_account_id, count(DISTINCT person_id) FROM person_identities GROUP BY jira_account_id HAVING count(DISTINCT person_id) > 1`, deve sempre retornar 0 linhas).
