# Progresso

## Estado Atual

- **Pronto:** setup completo de ponta a ponta, e **primeiro sync real bem-sucedido** contra os dois sites Jira de produção (TEC e CAP), após encontrar e corrigir 5 bugs que só apareciam com dados reais (ver `docs/decisions/0003-bugs-primeiro-sync-real.md`). Dados reais no banco: TEC (9054 issues, 142 sprints, 50 pessoas, 10000 mudanças de changelog, 16525 vínculos issue↔sprint), CAP (34 issues, 3 sprints, 4 pessoas, 70 mudanças, 28 vínculos). Rotas de métricas validadas com dados reais (sprint ativa "[2026] W29", carga de trabalho por pessoa).
- **Em andamento:** nada em execução — ponto de partida limpo.
- **Próximo passo:** abrir http://localhost:5173 (rodando) e conferir visualmente as 3 páginas com os dados reais sincronizados. Depois, decidir se/quando configurar o agendamento automático do sync (cron do host, ver `docs/jira-integration.md`).

## Log

### 2026-07-18 (cont.) — Claude Code
- Usuário explicou 1 a 1, ao vivo, o significado de cada status que eu não sabia (`Em andamento`, `Teste`, `UNDER PR REVIEW`, `Reviewed`, `Waiting Store Approval`). Corrigiu duas suposições erradas que eu tinha feito no ajuste anterior: `Under PR Review` **não é** sinônimo de `To Review` (é revisão de código/PR, etapa própria, antes de ir pra homologação); `Reviewed` **não é** sinônimo de `Review` (é o estado final, pós-produção, revisado por todos inclusive PO). Também corrigiu a ordem: `Deploy para prod` vem **antes** de `To Review`, não depois.
- Fluxo completo (11 etapas) registrado em `docs/workflow-do-time.md`, com tipos de issue (Bug/História/Tarefa) e significado de cada status. `AGENTS.md` atualizado pra apontar pra esse arquivo em vez de duplicar o conteúdo. `status_order.py` corrigido e revalidado contra a sprint ativa real.
- Lição: ao inferir significado/ordem de dados de negócio a partir de nomenclatura (ex: "Reviewed" parece óbvio, mas não é), perguntar 1 a 1 em vez de assumir — já errei duas vezes nesse mapeamento antes de perguntar.

### 2026-07-18 — Claude Code
- Repositório criado em `~/Projects/jira-dashboard-mbc`, `git init` feito, commit inicial (`cc3ffab`) e push para `https://github.com/JrBackes/jira-dashboard` (merge com README stub que o GitHub criou ao inicializar o repo).
- Criada estrutura de documentação compartilhada entre Claude Code e Antigravity (`AGENTS.md`, `CLAUDE.md` stub, `PROGRESS.md`, `TASKS.md`, `docs/data-model.md`, `docs/jira-integration.md`, `docs/decisions/`).
- Ambiente local preparado: Homebrew (`python@3.12`, `pipx`), Poetry via pipx. Docker Desktop iniciado.
- Setup completo de backend (FastAPI + Postgres + Alembic), sync (JiraClient + pipeline), rotas de métricas e frontend (React + Vite) — todas as camadas validadas rodando (ver commit inicial para detalhes).
- **Preenchido `.env`** com credenciais reais do Jira para TEC e CAP (tokens gerados pelo usuário, nunca vistos/colados na conversa).
- **Primeiro sync real rodado** — encontrou e corrigiu, nesta ordem, 5 bugs que só apareciam com dados reais de produção (todos documentados em `docs/decisions/0003-bugs-primeiro-sync-real.md`):
  1. `changelog/bulkfetch` rejeita lote com todos os ~9000 issueIds de uma vez (400) — paginado em lotes de 1000.
  2. Formato real do changelog é `issueChangeLogs[].changeHistories[]` (não `changeLog.histories[]`), e `created` é epoch em milissegundos (int), não ISO string — bug **silencioso** (sync completava com "success" processando 0 mudanças).
  3. Colunas `from_value`/`to_value` (`String(1000)`) estouravam em campos como `description` — migradas para `Text` (migration `b71d46295ef3`).
  4. Campo Sprint não existe como `sprint`/`closedSprints` literal no Platform Search API — é um customfield (`customfield_10020`, resolvido via `get_fields()`) que retorna a lista completa do histórico de sprints da issue. Sem isso, `issue_sprints` ficava **completamente vazia** — bug silencioso, nenhuma métrica de sprint funcionava.
  5. `statusCategory.name` é localizado (retornava "Itens concluídos" em vez de "done" nesta instância PT-BR) — todo filtro `status_category == "done"` (workload, highlights, velocity) nunca batia. Corrigido para usar `statusCategory.key` (estável: `new`/`indeterminate`/`done`).
- Dados reais confirmados corretos após as correções: sprint ativa real "[2026] W29" com burndown e contagem por status coerentes; carga de trabalho por pessoa validada contra query SQL direta.
- Observação de negócio (não é bug): o time do TEC não usa Story Points — métricas em pontos (burndown/velocity por pontos) retornam 0 até o time passar a estimar; métricas por contagem de itens funcionam normalmente.
- Pendência: validar visualmente no navegador (sem ferramenta de screenshot neste ambiente).
- Restringido `list_people` a quem já foi assignee de alguma issue (exclui reporters/bots) — TEC caiu de 50 para 20 pessoas, CAP para 2.
- Usuário passou a taxonomia real do time (3 tipos de issue: Bug/História/Tarefa; fluxo de status Backlog→To Do→In Progress→Is Blocked→To Test→Testing→To Review→Review→Deploy para prod — ver `AGENTS.md`). Carga de trabalho e contagem por status da sprint passaram a agrupar pelo `status` granular (ordenado pelo fluxo, `app/services/status_order.py`), em vez das 3 categorias genéricas do Jira (`new`/`indeterminate`/`done`) — removida a camada de tradução `statusCategory.ts` do frontend, que ficou sem uso.
