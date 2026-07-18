# Fluxo de trabalho do time (Sistema MBC / TEC)

Registrado a partir de explicação direta do usuário (2026-07-18). Fonte de verdade para qualquer lógica que agrupe/ordene status — ver `backend/app/services/status_order.py`.

## Tipos de issue

- **Bug** — algo ocorreu fora do previsto.
- **História** — melhoria ou desenvolvimento novo.
- **Tarefa** — tarefa específica que não se encaixa nos dois acima.

Também existem `Subtarefa` e `Epic` no Jira, fora dessa taxonomia de 3 (não fazem parte da classificação de tipo de trabalho do time).

## Status, em ordem do fluxo

| # | Status | Significado |
|---|---|---|
| 1 | **Backlog** | Programada para a sprint, mas não foi iniciada. |
| 2 | **To Do** | Está para iniciarmos logo mais. |
| 3 | **In Progress** (`Em andamento` é a mesma etapa — variação de nomenclatura) | Tarefa em progresso. |
| 4 | **Under PR Review** | Dev finalizou a tarefa e abriu o Pull Request, mas outro dev ainda não deu o aceite (aprovação de código) para ir para homologação. Etapa própria — **não é sinônimo de "To Review"/"Review"**. |
| 5 | **Is Blocked** | Bloqueada, aguardando desbloqueio de outra tarefa ou validação. Pode ocorrer a qualquer momento do fluxo (não é estritamente sequencial), mas é exibida nesta posição por padrão. |
| 6 | **To Test** | Está para teste. |
| 7 | **Testing** (`Teste` é a mesma etapa — variação de nomenclatura) | Em fase de teste pelo tester. |
| 8 | **Deploy para prod** | Pronta, aguardando submeter uma versão para produção. |
| 9 | **To Review** / **Review** | Já está em produção e está sendo revisada (mesmo conceito, "tarefa pronta" — vem depois do deploy, não antes). |
| 10 | **Waiting Store Approval** (só aparece no CAP) | Aguardando aprovação da loja (App Store/Play Store) — específico de app mobile. |
| 11 | **Reviewed** | Estado final: já foi para produção e foi revisada por todos, inclusive o PO. É o status "done" mais comum de longe no TEC. |

## Pontos de atenção

- Os nomes reais no Jira variam por nomenclatura histórica, **não por workflow diferente por tipo de issue** — confirmado com o usuário. Ex: `Em andamento` ≈ `In Progress`, `Teste` ≈ `Testing`, variações de maiúsculas/minúsculas (`TO DO`, `TO REVIEW`) são a mesma etapa.
- `status_category` do Jira (`new`/`indeterminate`/`done`) é **grosseiro demais** para este time — várias etapas distintas do fluxo (`To Review`, `Deploy para prod`, `Reviewed`) já caem todas em `done` na categorização do próprio Jira, mesmo sendo passos diferentes. Por isso as métricas usam o `status` granular (`app/services/status_order.py`), não a categoria.
- Se aparecer um status novo não listado aqui, ele cai no fim da ordenação (`sort_statuses`) até ser registrado nesta tabela — perguntar ao usuário o significado antes de posicioná-lo no fluxo.
