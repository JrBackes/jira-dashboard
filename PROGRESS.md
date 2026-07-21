# Progresso

## Estado Atual

- **Pronto:** setup completo de ponta a ponta, primeiro sync real bem-sucedido (TEC e CAP), fluxo de status do time totalmente registrado (`docs/workflow-do-time.md`), tabela **colaborador × status** com tempo na Sprint Atual, nova aba **Atualização** (`/atualizacao`) com botão "Atualizar agora" (`POST /api/sync/trigger`, roda em background) e status/última atualização por site (`GET /api/sync/status`), painel **"Itens em risco"**, seção **"Itens bloqueados"** (com motivo via vínculos do Jira, `blocked_since`/`days_blocked`) e seção **"Mapa de Tecnologia"** (issues da sprint agrupadas por Epic) na Sprint Atual; ranking semanal + diário de tempo trabalhado (com seletor de sprint) na Por Pessoa — tudo validado via curl com dados reais. Changelog do TEC corrigido de 470→9084/9088 issues com histórico real (bug de paginação do `changelog/bulkfetch`, ver `docs/decisions/0003`).
- **Em andamento:** `docs/problemas-dashboard.md` — problema 1 e 2 implementados; problema 3 (Mapa de Tecnologia) implementado e **validado com a planilha real** (50 linhas importadas, todas as colunas batendo, ver log de hoje) — só falta o usuário preencher a coluna "Epic Jira" (curadoria manual) pra os vínculos com Epics aparecerem.
- **Próximo passo:** usuário preencher "Epic Jira" na planilha (aos poucos, por iniciativa identificada) e reimportar. Validação visual no navegador das páginas com dados reais e decisão sobre agendamento automático do sync continuam pendentes.

## Log

### 2026-07-20 (cont. 8) — Claude Code
- Usuário colou a aba real do Mapa de Tecnologia na seção "Mapa de Tecnologia" da aba Atualização e clicou "Importar" — **50 linhas importadas com sucesso**.
- Conferido no banco: `Status`, `Frente`, `Tarefa`, `Atuantes`, `ICE` (Impacto/Confiança/Facilidade/Score) e `Entrega` bateram exatamente com o esperado (ex: linha do HTML — Status "Em andamento", Frente "Receita", Atuantes "PO,UX,BACK,FRONT", ICE 8/9/6/432, Entrega "W30"). Confirmado contra dado real: "Atuantes" é uma única coluna com texto já unido por vírgula (não múltiplas colunas como eu tinha especulado antes); "ICE" de fato são 4 colunas adjacentes. Comentários do parser atualizados pra refletir isso.
- `epic_jira_key` veio `null` em todas as 50 linhas — a princípio parecia bug, mas o usuário confirmou que ainda não preencheu nenhum valor na coluna "Epic Jira". Comportamento correto, não é bug.
- Documentação atualizada (`docs/problemas-dashboard.md`, `docs/data-model.md`, `TASKS.md`) refletindo a validação real — problema 3 fechado tecnicamente, só falta curadoria manual do usuário.

### 2026-07-20 (cont. 7) — Claude Code
- Usuário informou que a service account não pode ser usada — Google Cloud está fora de alcance neste ambiente (sem admin/projeto disponível), e a planilha não pode ficar acessível por link (dado sensível). Perguntei pra confirmar a extensão da restrição antes de redesenhar.
- Trocada a integração inteira: removida a dependência de `google-auth`/`requests`/`cryptography` (junto com ela, o bug de "Illegal Instruction" do `docs/decisions/0005` deixa de existir — marcado revertido). `backend/app/integrations/google_sheets/client.py` removido; `mappers.py` (parsing por nome de coluna) reaproveitado, já era formato-agnóstico.
- Novo fluxo: `tech_map_service.import_tech_map_from_tsv` recebe texto colado (TSV, formato nativo do clipboard do Google Sheets) e faz o mesmo replace completo de antes. Rota trocada de `POST /api/tech-map/sync` pra `POST /api/tech-map/import` (body `{tsv, sheet_name?}`).
- `apiPost` (frontend) ganhou suporte a body JSON (antes só disparava sem payload). Nova seção "Mapa de Tecnologia" na `SyncPage` (aba Atualização): instrução + caixa de texto + botão "Importar".
- Validado ponta-a-ponta com dados sintéticos reproduzindo a estrutura real (incluindo o Epic `TEC-9346` já confirmado): import → parse → grava em `tech_map_entries` → `GET /api/tech-map/sprints/141` retornou o vínculo completo (Frente=Receita, Status=Em andamento, ICE score=432, Entrega=W30). Dados de teste removidos depois de validar.
- `tsc --noEmit` limpo. `poetry.lock` confirmado sem `google-auth`/`requests`/`cryptography`.

### 2026-07-20 (cont. 6) — Claude Code
- Problema 3 (Mapa de Tecnologia) — planejado em modo plan (arquivo salvo em `.claude/plans/`) e implementado após aprovação. Investigação inicial: li a planilha real via Google Drive (link fornecido pelo usuário), identifiquei que "Tarefa" corresponde a um Epic do Jira, e que o Jira expõe esse vínculo via campo de sistema `parent` (confirmado real: `TEC-10014.parent.key == "TEC-9346"`).
- Testado e descartado casamento automático por texto (Tarefa ↔ summary do Epic) — não confiável (par certo pontuou 0.45, um errado pontuou mais alto). Usuário optou por curadoria manual: nova coluna "Epic Jira" na planilha.
- Implementado: `issues.parent_jira_key` (migration + sync), integração `google_sheets/` (client HTTP próprio, `google-auth` + `httpx`), model `TechMapEntry` + migration, `tech_map_service.py` (sync + agrupamento por Epic pra uma sprint), rotas `POST /api/tech-map/sync` e `GET /api/tech-map/sprints/{id}`, seção "Mapa de Tecnologia" na `CurrentSprintPage`.
- **Bug de ambiente encontrado durante o rebuild da imagem Docker:** `cryptography` 49.0.0 (puxado por `google-auth`) trava o container com "Illegal Instruction" nesta máquina (arm64) — especificamente em `cryptography.hazmat.primitives.asymmetric.rsa`, usado pra assinar o JWT do service account. Mesma família do bug já documentado em `docs/decisions/0002`. Fixado `cryptography<43.0` (`42.0.8` testado e funcionando) — ver `docs/decisions/0005-cryptography-pin-illegal-instruction.md`.
- Re-sync completo rodado pra popular `parent_jira_key`: 6828 de 9097 issues do TEC agora com Epic vinculado. Validado: `/api/tech-map/sprints/141` (sprint ativa W30) agrupou corretamente por Epic, incluindo `TEC-9346` com 11 issues.
- **Pendente do usuário:** service account do Google Cloud (compartilhar a planilha com o e-mail dela), preencher a coluna "Epic Jira", e passar o JSON da service account — sem isso, `/api/tech-map/sync` retorna 400 tratado (sem crash), mas não sincroniza. O parsing de colunas "largas" (Atuantes/ICE) foi implementado com base na melhor leitura possível da planilha via preview do Google Drive (não a API real) — precisa validação final assim que o sync rodar de verdade.
- `tsc --noEmit` limpo.

### 2026-07-20 (cont. 5) — Claude Code
- Usuário pediu pra ver quais tasks geravam as 10h do `diogo.bastos` no ranking diário de hoje. Conferido via query direta: 3 tasks em "To Test" (TEC-10022: 3h, TEC-10016: 4h, TEC-10014: 3h = 10h). Nenhuma delas foi excluída pela regra de "status na entrada da sprint" — não têm histórico de status antes de entrarem na W29, tratadas como "não sei" (não exclui por precaução).
- **Usuário confirmou que o filtro está correto.** Critério de exclusão (status avançado no momento de entrada na sprint) validado como pronto.

### 2026-07-20 (cont. 4) — Claude Code
- Usuário apontou que não entendeu a explicação anterior — o filtro por "hora de entrada na sprint" não resolvia o problema real, porque o rollover de sprint do Jira move issues novas e migradas no mesmo evento em lote (mesmo instante), então a hora sozinha não distinguia as duas.
- Critério corrigido e confirmado com o usuário: olhar o **status da issue no momento em que ela entrou na sprint atual**. Se já era Under PR Review ou mais avançado no fluxo (To Test, Testing, Deploy pra prod, To Review, Reviewed), todo apontamento dela fica de fora do ranking desta semana — mesmo o logado depois de entrar na sprint. Novo helper `_status_at` (`person_metrics.py`) + `_ADVANCED_ENTRY_RANK = status_rank("under pr review")`.
- Validado: agora os números mudam de verdade — `diogo.bastos` caiu de 96300s pra 92700s no TEC (sprint 138). Achadas ~29 issues do diogo que entraram na W29 já em "To Test" ou "Deploy para prod" — bate exatamente com o cenário relatado pelo usuário. Diário e semanal consistentes entre si (92700s incluindo sexta nos dois).
- `tsc --noEmit` limpo (sem mudança de contrato de API).

### 2026-07-20 (cont. 3) — Claude Code
- Usuário relatou dificuldade real: issues migram já avançadas da sprint anterior (Under PR Review, To Test, Testing, Deploy pra prod, To Review, Reviewed) — apontamento residual nelas não deveria contar como "trabalho desta semana" no ranking diário. Perguntei o critério exato e o escopo antes de implementar (várias interpretações possíveis).
- Critério escolhido: só contar tempo logado **depois** que a issue formalmente entrou na sprint selecionada, aplicado nos rankings semanal e diário. Novo helper `_sprint_entry_at` (`person_metrics.py`, mesma lógica de detecção de `sprint_scope_changes` via changelog do campo "Sprint") + `_positive_timespent_deltas` descarta deltas anteriores a esse momento.
- Validado contra a sprint 138 (W29): números da semana de 13-17/07 não mudaram — investigado e confirmado que é esperado (eventos de entrada na sprint concentrados no rollover em lote do início da sprint, todo apontamento existente é posterior). Achei 4 issues que entraram no meio da semana, nenhuma com apontamento anterior à entrada — mecanismo ativo e correto, só sem casos reais pra excluir nesta semana específica.
- `tsc --noEmit` limpo (sem mudança de contrato de API, sem necessidade de alteração no frontend).

### 2026-07-20 (cont. 2) — Claude Code
- Usuário pediu um "ranking diário" abaixo do ranking da semana, pra comparar tempo decorrido da sprint com entregas dia a dia (ex: "passou 1 dia = 6h, entregou mais ou menos que isso"). Perguntei formato (matriz pessoa×dia vs ritmo acumulado) e base de tempo (datas reais da sprint vs semana civil) — escolhido: matriz pessoa×dia, semana civil (mesma base do ranking semanal).
- `daily_time_breakdown` (`person_metrics.py`) + rota `GET /api/people/ranking/daily` + componente `DailyRankingTable`: matriz pessoa × dia útil já decorrido (segunda até hoje), cada célula com ↑/↓ contra 6h/dia esperado, coluna "Acumulado" (total logado de total esperado). Refatorei a query compartilhada com `weekly_time_ranking` num helper `_positive_timespent_deltas` pra não duplicar a lógica de deltas positivos de `timespent`.
- Validado com dados reais: hoje (única segunda, 1 coluna) e com `reference=2026-07-16` (quinta, 4 colunas) via chamada direta da função — valores por dia batendo com o total da semana já validado antes.
- `tsc --noEmit` limpo.

### 2026-07-20 (cont.) — Claude Code
- Usuário pediu pra "Carga de trabalho atual" também respeitar o seletor de sprint da `PeoplePage` (só ranking da semana e destaques respeitavam antes).
- `person_workload` (`person_metrics.py`) ganhou parâmetro `sprint_id` (mesmo padrão de `person_highlights`/`weekly_time_ranking`: None = todas as sprints, valor específico = filtra por qualquer vínculo em `issue_sprints`). Rota `/api/people/{id}/workload` ganhou query param `sprint_id`. `PeoplePage.tsx` passa o mesmo `sprintIdParam` já usado nas outras duas seções.
- Validado: `diogo.bastos` (id 17) no TEC — "todas as sprints" mostra Backlog:16/TO DO:1/Is blocked:1 junto com o resto; filtrando pra sprint 138 (W29), cai pra Backlog:6 e os itens de fora da sprint (TO DO, Is blocked) somem — confirma que o filtro está excluindo issues de fora da sprint escolhida.
- `tsc --noEmit` limpo.

### 2026-07-20 — Claude Code
- Usuário pediu um seletor na aba Por Pessoa pra escolher se os dados vêm de uma sprint específica ou de tudo, com a sprint atual marcada como padrão.
- `weekly_time_ranking` (`person_metrics.py`) trocou o filtro fixo (sprint ativa) por um parâmetro `sprint_id` opcional: `None` = sem filtro de sprint ("tudo"), valor específico = filtra por qualquer vínculo em `issue_sprints` (não só `is_current`, já que o usuário escolheu essa sprint no seletor). Rota `GET /api/people/ranking/weekly` ganhou query param `sprint_id`.
- `PeoplePage.tsx`: novo `<select>` de sprint (busca sprints via `fetchSprints`, já existente), padrão = sprint com `state === "active"`, opção "Todas as sprints". Mesmo filtro passado pro ranking da semana e pros destaques (`person_highlights`, que já aceitava `sprint_id` mas não tinha controle de UI).
- Validado: sprint 138 (W29) e "tudo" retornam os mesmos 9 nomes pra semana de 13-17/07 (a sprint cobria o período inteiro). `tsc --noEmit` limpo.

### 2026-07-18 (cont. 12) — Claude Code
- Usuário pediu pra restringir o "Ranking da semana" a issues que estão na sprint em questão (ex: W29) — apontamento fora da sprint atual não deve contar.
- `weekly_time_ranking` (`person_metrics.py`) agora filtra por `IssueSprint.is_current` + `Sprint.state == "active"`. Validado: `leonardo.krindges` caiu de 60600s pra 57000s e `robert.bonfada` de 1500s pra 600s no TEC — tempo fora da sprint ativa corretamente excluído. CAP sem mudança (issue já estava na sprint ativa).
- Nota adicionada no `WeeklyRankingTable` explicando esse escopo. `tsc --noEmit` limpo.

### 2026-07-18 (cont. 11) — Claude Code
- Usuário pediu pra explicar o número baixo (0.4h) do `robert.bonfada` no ranking da semana. Ao investigar, achei que ele só logou 2 vezes na segunda-feira (15min + 10min, nada de terça a sexta) — explicação direta.
- Achado à parte, mais importante: **`accountId` do Jira pode ser compartilhado entre TEC e CAP** (contrariando a regra documentada em `AGENTS.md`) — `robert.bonfada` e `Victor Amaral` tinham o mesmo `accountId` nos dois sites, e como o e-mail deles não vem exposto pela API, cada um tinha virado **duas pessoas canônicas** em `people` (uma por site) em vez de uma.
- Corrigido: mesclados os dois pares de duplicatas (repontuando `issues.assignee_person_id`/`reporter_person_id`, `issue_field_changes.changed_by_person_id`, `person_identities.person_id` pro sobrevivente, removendo a linha duplicada de `people`). `_resolve_person` (`sync_service.py`) agora verifica `jira_account_id` em qualquer site antes de cair no fallback de e-mail ou criar pessoa nova — não deve duplicar de novo em syncs futuros.
- Registrado em `docs/decisions/0004-pessoas-duplicadas-accountid-compartilhado.md` e corrigida a regra errada em `AGENTS.md`. Ranking da semana revalidado — sem mudança pro Robert nesta semana específica (o lado CAP dele não tinha apontamento no período).

### 2026-07-18 (cont. 10) — Claude Code
- Implementado "Ranking da semana" (problema 2 de `docs/problemas-dashboard.md`, 1ª parte): tempo trabalhado por colaborador na semana civil (segunda a sexta) contra o esperado de uma semana cheia (5 dias × 6h = 30h). `weekly_time_ranking` em `person_metrics.py` + rota `GET /api/people/ranking/weekly` + componente `WeeklyRankingTable` na página Por Pessoa.
- Achado técnico: mesmo o time só preenchendo o campo agregado "Tempo gasto" (sem worklog formal do Jira), cada atualização desse campo já vira uma entrada de changelog (`field_name="timespent"`) com valor antes/depois, autor e timestamp — dá granularidade por dia sem precisar sincronizar nada novo. Só ficou disponível de verdade depois da correção do bug de paginação do changelog desta sessão (senão a maioria das issues não teria esse histórico).
- Validado com dados reais: semana de 13/07 a 17/07, 9 pessoas no TEC, 1 no CAP.
- `tsc --noEmit` limpo.

### 2026-07-18 (cont. 9) — Claude Code
- Usuário apontou que a data de "bloqueado desde" da TEC-10020 estava errada (mostrava 29/06, deveria ser 16/07). Investigando, achei um **bug sério e pré-existente** (não relacionado à feature nova): `changelog/bulkfetch` pagina a resposta **dentro** de cada lote de 1000 issueIds — um lote retornava só ~50 issues com changelog na primeira página, e o `nextPageToken` era ignorado. Resultado real no banco: só **470 de 9088 issues do TEC tinham changelog** antes da correção (o resto, silenciosamente vazio, sync sempre "success"). Afetava toda lógica que depende de `issue_field_changes`: `blocked_since`/`days_blocked`, `stalled` do painel de risco, e "já passou por To Test" da tabela colaborador×status.
- Corrigido `JiraClient.fetch_changelogs_bulk` pra seguir `nextPageToken` em loop dentro de cada lote. Ao rodar o re-sync completo pra backfill, apareceu um **segundo bug**: seguir a paginação faz o mesmo registro de histórico aparecer duas vezes (overlap entre páginas); como a `Session` usa `autoflush=False`, a checagem de duplicado dentro do laço não via o `db.add()` da mesma execução ainda não commitado, e a segunda ocorrência virava `UniqueViolation` **desfazendo o sync inteiro** (rollback, 0 registros). Corrigido com um `set()` de IDs já vistos na própria execução (`_sync_changelog_for_issues`).
- Registrado como bugs 6 e 7 em `docs/decisions/0003-bugs-primeiro-sync-real.md` (mesma categoria dos bugs do primeiro sync real — só apareceram com volume de dados real).
- **Novo re-sync completo** (cursores resetados de novo, confirmado com o usuário antes, dado o volume bem maior desta vez): TEC foi de 470 pra **9084 de 9088 issues com changelog real** (194959 linhas, contra 10070 antes). TEC-10020 confirmado: `blocked_since` agora é 2026-07-16 (bate com o que o usuário apontou).
- Todos os `days_blocked`/`blocked_since` do painel de bloqueados recalculados com dados reais (antes, vários caíam no fallback de `created_at` por falta de changelog).

### 2026-07-18 (cont. 8) — Claude Code
- Usuário pediu pra adicionar quando o item foi colocado em "Is Blocked". `sprint_blocked_items` ganhou `blocked_since`/`days_blocked`: última transição de status **para** "Is Blocked" em `issue_field_changes` (fallback pra última mudança de status de qualquer tipo, depois `created_at`, se a issue nunca teve essa transição registrada). Exibido em nova coluna na `BlockedItemsPanel`.
- Validado contra a sprint ativa do TEC: os dias batem exatamente com o `days_stalled` já visto no painel de risco pros mesmos itens (43/54/19 dias) — consistência entre os dois painéis confirmada.
- `tsc --noEmit` limpo.

### 2026-07-18 (cont. 7) — Claude Code
- Usuário pediu pra monitorar itens bloqueados e entender os motivos, usando as relações entre issues do Jira (não só o status "Is Blocked"). Nova seção própria "Itens bloqueados" na Sprint Atual (separada do painel de risco, a pedido do usuário — mais detalhe do que cabe numa linha de tabela).
- Jira nunca buscava o campo `issuelinks` (vínculos entre issues: "Blocks", "Relates", etc.) — adicionado a `DEFAULT_SEARCH_FIELDS` (`client.py`). Novo mapper `map_issue_links`, nova tabela genérica `issue_links` (migration `98aa33c46478`, model `IssueLink`) — guarda todos os tipos de vínculo, não só bloqueio, mesmo padrão de extensibilidade de `issue_field_changes`. Sync substitui o conjunto de vínculos por issue a cada ciclo (`_upsert_issue_links` em `sync_service.py`), removendo os que saíram do Jira.
- `sprint_blocked_items` (`sprint_metrics.py`) + rota `GET /api/sprints/{id}/blocked` + componente `BlockedItemsPanel`: pra cada issue "Is Blocked" na sprint atual, mostra a(s) issue(s) bloqueadora(s) (vínculo "Blocks"/inward) com status ao vivo (prioriza `Issue.jira_key` se sincronizada por nós, senão usa o snapshot salvo no momento do sync).
- **Re-sync completo disparado** (confirmado com o usuário antes, dado o custo de chamadas à API do Jira) pra popular `issuelinks` retroativamente: reset dos `sync_cursors` de TEC/CAP + `POST /api/sync/trigger` pros dois sites. TEC: 9054 issues reprocessadas em ~82s. Total de 3138 vínculos importados (472 "Blocks"/inward, resto majoritariamente "Relates"/"Cloners").
- Achado real: os 5 itens bloqueados na sprint ativa do TEC não tinham nenhum vínculo "Blocks" registrado no Jira — aparecem como "sem vínculo registrado", sinal de que o time nem sempre formaliza o motivo do bloqueio no Jira.
- `tsc --noEmit` limpo; validado via curl.

### 2026-07-18 (cont. 6) — Claude Code
- Usuário corrigiu mais uma regra de negócio no painel de risco: "To Review"/"Review", "Waiting Store Approval" e "Reviewed" **já estão em produção** — não têm relação com a janela de deploy (diferente de "Deploy para prod", que aguarda a janela).
- `sprint_risk_items` ajustado pra distinguir `awaiting_deploy_count` (só "Deploy para prod", rank == _READY_RANK) de `in_production_count` (rank > _READY_RANK — já entregue). `next_deploy_date` só é retornado quando `awaiting_deploy_count > 0`.
- Números finais na sprint ativa do TEC (id 138): 43 em risco real, 125 aguardando deploy (próxima janela 20/07), 40 já em produção — soma bate com os 208 itens da sprint. `docs/workflow-do-time.md` atualizado com a distinção.
- `tsc --noEmit` limpo; validado via curl após `docker compose restart backend`.

### 2026-07-18 (cont. 5) — Claude Code
- Usuário corrigiu regra de negócio importante no painel de risco: status "Deploy para prod" (e depois, no fluxo) significa que o item **já está pronto** — não deveria gerar tag de risco/parado. Calendário de deploy do time: roda até quinta à tarde (sexta só em emergência), o que sobra vai pra segunda de manhã da semana seguinte.
- `sprint_risk_items` corrigido: itens com rank de status >= "deploy para prod" não geram mais nenhuma tag (nem "stalled") — contados à parte em `ready_count`. Novo campo `next_deploy_date` (`_next_deploy_date` em `sprint_metrics.py`) calcula a próxima janela real de deploy dado o calendário do time.
- Impacto real na sprint ativa do TEC (id 138): de 206/208 itens "em risco" caiu pra **43 em risco real + 165 prontos aguardando deploy**. Mostra que boa parte da percepção de "muita coisa migrando" (problema 1 de `docs/problemas-dashboard.md`) é efeito normal do calendário de deploy, não trabalho incompleto.
- `tsc --noEmit` limpo; validado via curl após `docker compose restart backend`.

### 2026-07-18 (cont. 4) — Claude Code
- Criado `docs/problemas-dashboard.md` a pedido do usuário: lista viva dos problemas reais de negócio que a dashboard deve resolver (1. acompanhamento da sprint/itens migrando, 2. tempo decorrido vs. registrado pelos colaboradores, 3. vínculo com "Mapa de Tecnologia" — planilha/doc externo, detalhes a levantar depois).
- Implementado o problema 1: painel **"Itens em risco"** na Sprint Atual. `sprint_risk_items` em `sprint_metrics.py` + rota `GET /api/sprints/{id}/risk` + componente `SprintRiskPanel.tsx`. Cada issue acumula tags explicáveis (não um score opaco): `migrated` (já esteve em sprint anterior, via `issue_sprints`), `stalled` (sem mudança de status há ≥2 dias, limiar confirmado com o usuário pra sprints de 1 semana), `blocked` (status "Is Blocked", novo helper `status_order.is_blocked`), `behind_schedule` (≤2 dias pro fim da sprint e ainda não chegou em "To Test").
- Validado end-to-end via curl contra a sprint ativa real do TEC (id 138): endpoint só apareceu depois de `docker compose restart backend` (backend não roda com `--reload`, diferente do frontend via Vite — mudança de código exige restart do container, não só do `.env`). Retornou 206/208 itens em risco — sprint já passou do `end_date` sem ter sido fechada no Jira, cenário coerente.
- `tsc --noEmit` limpo no frontend.

### 2026-07-18 (cont. 3) — Claude Code
- Nova aba "Atualização" no frontend, a pedido do usuário: botão "Atualizar agora" + última data de atualização por site.
- Backend: `POST /api/sync/trigger` (dispara `sync_site` em background via FastAPI `BackgroundTasks`, guard contra disparo duplicado enquanto um site já está `running`) e `GET /api/sync/status` (último `SyncRun` por site, usado como "última atualização"). `sync_service.py` ganhou um `db.commit()` logo ao criar o `SyncRun` (antes só tinha `flush()`) — sem isso, outras sessões não enxergavam o status "running" a tempo do guard funcionar.
- **Bug real encontrado e corrigido durante o teste**: o container do backend tinha sido criado (`docker compose up`) antes das credenciais reais do Jira serem preenchidas no `.env`. Todas as vezes que rodei `docker compose restart backend` depois disso, o container continuou com as variáveis de ambiente antigas (placeholders vazios) — `restart` não relê o `.env`, só `up --force-recreate` (ou `down`+`up`) faz isso. O sync via endpoint falhava silenciosamente (só nos logs do container, resposta HTTP continuava 200 porque roda em background) até eu descobrir isso adicionando prints de debug temporários e depois recriar o container. Registrado em `AGENTS.md` e `TASKS.md` — é um erro fácil de repetir.
- Frontend: `SyncPage.tsx` (`/atualizacao`), `api/sync.ts`, `apiPost` adicionado em `api/client.ts`. Polling automático (React Query `refetchInterval`) enquanto algum site está `running`.

### 2026-07-18 (cont. 2) — Claude Code
- Nova funcionalidade na Sprint Atual: tabela colaborador×status com contagem de issues + tempo por célula, a pedido do usuário.
- Descoberta ao investigar: o time não usa Story Points, mas usa os campos **nativos** de time tracking do Jira — "Estimativa original" (`timeoriginalestimate`, ~6200 issues preenchidas no TEC) e "Tempo gasto" (`timespent`, apontamento manual, ~6500 issues no TEC). Confirmado com o usuário via perguntas antes de implementar.
- Regra de negócio implementada: para cada issue, mostra a estimativa original **enquanto ela nunca chegou em "To Test"** no histórico de status (`issue_field_changes`, não só o status atual — uma issue "Is Blocked" hoje pode já ter passado por Testing antes); depois que chegou, mostra o tempo gasto (apontado manualmente, não tempo decorrido calculado).
- Adicionado `original_estimate_seconds`/`time_spent_seconds` em `issues` (migration `7dacb75f4e4d`), `sprint_workload_by_status_and_person` em `sprint_metrics.py`, rota `/api/sprints/{id}/workload-by-status`, componente `SprintWorkloadTable` no frontend. Re-sync completo pra popular os novos campos nas issues já existentes.
- `status_order.py` ganhou `status_rank`/`sort_status_list` públicos, reusados pra decidir se uma issue já passou por "To Test".

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
