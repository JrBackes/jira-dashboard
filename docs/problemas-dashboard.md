# Problemas que a dashboard deve resolver

Lista viva de problemas reais do time que motivam novas métricas/telas na dashboard. Cada item deve virar uma solução desenhada e implementada — ver `PROGRESS.md`/`TASKS.md` para o andamento.

## 1. Falta de acompanhamento da sprint em andamento

**Problema:** não há visibilidade suficiente durante a sprint, e ela costuma fechar com muitos itens migrando para a próxima (não concluídos no prazo).

**Objetivo:** dar sinais durante a sprint (não só no fechamento) que permitam agir a tempo — ex: identificar cedo o que está em risco de não fechar.

**Solução implementada (2026-07-18):** painel "Itens em risco" na Sprint Atual (`GET /api/sprints/{id}/risk`, `sprint_risk_items` em `sprint_metrics.py`, componente `SprintRiskPanel`). Em vez de um score único, cada issue acumula tags explicáveis:
- 🔁 **migrated** — já esteve em sprint(s) anteriores antes desta (derivado de `issue_sprints`, sem necessidade de nova coluna).
- ⏸️ **stalled** — sem mudança de status há ≥ 2 dias (limiar calibrado pra sprints de 1 semana, a pedido do usuário), a partir do último `issue_field_changes` de `field_name="status"`.
- 🚫 **blocked** — status atual é "Is Blocked" (`status_order.is_blocked`).
- ⚠️ **behind_schedule** — faltam ≤ 2 dias pro fim da sprint e a issue ainda não chegou em "To Test".

**Regra de negócio importante (2026-07-18):** status "Deploy para prod" significa que o item já está pronto, mas ainda aguarda a janela de deploy (roda até quinta à tarde, sexta só em emergência; o que sobra vai pra segunda de manhã da semana seguinte) — contado em `awaiting_deploy_count`. Status depois disso no fluxo (**"To Review"/"Review", "Waiting Store Approval", "Reviewed"**) **já estão em produção** (confirmado com o usuário) — sem relação com a janela de deploy, contados em `in_production_count`. Nenhum dos dois grupos gera tag de risco (nem "stalled", mesmo parados há dias — é esperado, não um problema). Isso explica boa parte da percepção de "muita coisa migrando": parte do que migra formalmente de sprint é só efeito da janela de deploy ou já está entregue, não trabalho incompleto de fato.

Validado contra a sprint ativa real do TEC (id 138) — sprint já com `end_date` no passado (não fechada ainda no Jira). Evolução dos números: 206/208 "em risco" (versão inicial) → 43 em risco + 165 "prontos" sem distinção → **43 em risco real, 125 aguardando deploy (próxima janela: 20/07, segunda-feira), 40 já em produção** (versão final, com a distinção correta) — soma bate com os 208 itens totais.

**Extensão (2026-07-18): monitorar itens bloqueados e o motivo.** As issues têm relações entre si no Jira (campo `issuelinks` — "Blocks", "Relates", etc.), até então não sincronizadas. Nova seção própria "Itens bloqueados" na Sprint Atual (`GET /api/sprints/{id}/blocked`, `sprint_blocked_items`, componente `BlockedItemsPanel`), separada do painel de risco por ter mais detalhe: para cada issue com status "Is Blocked" na sprint atual, mostra `blocked_since`/`days_blocked` (desde quando está bloqueada, via `issue_field_changes` — última transição de status **para** "Is Blocked") e a(s) issue(s) que a bloqueiam (vínculo Jira "Blocks"/inward = "is blocked by") junto com o status atual de cada uma. Nova tabela `issue_links` (genérica, todos os tipos de vínculo — ver `docs/data-model.md`), novo campo requisitado do Jira (`issuelinks`), re-sync completo de TEC/CAP feito pra popular retroativamente (3138 vínculos importados no total).

Achado real ao validar contra a sprint ativa do TEC: os 5 itens bloqueados na sprint não tinham **nenhum vínculo formal registrado no Jira** — aparecem no painel com "sem vínculo registrado", o que já é um sinal de processo (bloqueio sem rastro do motivo). Vínculos reais existem no banco (ex: CAP-20 bloqueado por CAP-33), só não em issues da sprint atual.

**Status:** implementado. Próximo: usuário validar visualmente no navegador; considerar se vale reforçar como prática do time sempre registrar o vínculo "Blocks" no Jira ao marcar algo como "Is Blocked", já que hoje nem sempre acontece.

## 2. Tempo decorrido da sprint vs. tempo registrado pelos colaboradores

**Problema:** não dá pra saber se o tempo que já passou da sprint é compatível com o tempo efetivamente trabalhado/registrado pelos colaboradores (risco de subregistro ou descompasso entre prazo e esforço real).

**Objetivo:** comparar tempo decorrido (calendário) com tempo registrado (apontamentos/estimativas) para sinalizar descompasso.

**Solução implementada, 1ª parte (2026-07-18): Ranking da semana.** Ranking de tempo trabalhado por colaborador na semana civil (segunda a sexta), contra o esperado de uma semana cheia (5 dias × 6h = 30h) — `GET /api/people/ranking/weekly`, `weekly_time_ranking` em `person_metrics.py`, componente `WeeklyRankingTable` na página Por Pessoa.

**Achado técnico importante:** o time não usa o worklog formal do Jira (com descrição por apontamento), só atualiza o campo agregado "Tempo gasto" (`timespent`) direto na issue — achávamos que isso não teria granularidade por dia. Mas cada atualização desse campo já gera uma entrada no changelog (`issue_field_changes`, `field_name="timespent"`) com o valor antes/depois, quem mudou e quando (habilitado pela correção do bug de paginação do changelog, ver `docs/decisions/0003`, itens 6-7 — sem aquela correção, a maioria das issues não tinha esse histórico). Ranking soma os deltas positivos (`to_value - from_value`) por `changed_by_person_id` dentro da janela da semana; deltas negativos (correção de apontamento pra baixo) não contam como trabalho.

Validado com dados reais: semana de 13/07 a 17/07 (última semana útil completa), 9 pessoas no TEC (de 96.7% a 0.8% do esperado), 1 pessoa no CAP (106.7%).

**Refinamento (2026-07-18): só considerar issues da sprint ativa.** A pedido do usuário, o ranking só soma tempo logado em issues que estão **na sprint atualmente ativa** (`IssueSprint.is_current` + `Sprint.state == "active"`) — apontamento em issue de backlog, sprint futura, ou que já saiu da sprint atual (ex: W29) não conta. Validado: `leonardo.krindges` caiu de 60600s pra 57000s e `robert.bonfada` de 1500s pra 600s no TEC, refletindo tempo logado fora da sprint ativa sendo corretamente excluído.

**Refinamento 2 (2026-07-20): seletor de sprint na página Por Pessoa.** O filtro por sprint ativa passou a ser **escolhível pelo usuário**, não fixo: novo seletor "Sprint" na `PeoplePage`, com opções "Todas as sprints" + cada sprint do projeto, **padrão = sprint atualmente ativa**. `weekly_time_ranking` ganhou parâmetro `sprint_id` (None = "tudo", sem filtro de sprint; valor específico = filtra por qualquer vínculo em `issue_sprints`, não só `is_current` — o usuário escolheu essa sprint explicitamente). O mesmo seletor também alimenta `person_highlights` (que já aceitava `sprint_id` opcional, mas não tinha controle de UI). Validado: sprint 138 (W29) e "tudo" retornam os mesmos 9 nomes pra semana de 13-17/07, já que a sprint cobria o período inteiro.

**Refinamento 3 (2026-07-20): Ranking diário — ritmo de entrega.** Abaixo do ranking da semana, matriz pessoa × dia (`GET /api/people/ranking/daily`, `daily_time_breakdown` em `person_metrics.py`, componente `DailyRankingTable`): cada coluna é um dia útil já decorrido na semana (segunda até hoje, ou até sexta se a semana já passou), mostrando quanto a pessoa logou naquele dia específico com indicação ↑/↓ contra o esperado de 6h/dia, mais uma coluna "Acumulado" (total logado de total esperado até agora). Resolve o pedido do usuário de comparar tempo decorrido da sprint com entregas dia a dia, não só no fechamento da semana. Reaproveita a mesma base de dados do ranking semanal (deltas positivos de `timespent` no changelog) e o mesmo seletor de sprint da página — refatorado num helper comum `_positive_timespent_deltas`.

Validado com dados reais (referência 16/07, quinta-feira, sprint 138): matriz de 4 dias (13-16/07), valores por dia batendo com o total da semana, esperado acumulado = 4 dias × 6h = 24h.

**Refinamento 4 (2026-07-20): não contar apontamento em issues que migraram já avançadas.** Usuário relatou dificuldade real: issues migram já avançadas da sprint anterior (Under PR Review, To Test, Testing, Deploy pra prod, To Review, Reviewed), e apontamento nelas não deveria contar como "trabalho desta semana" — o desenvolvimento de verdade já aconteceu numa sprint passada.

Primeira tentativa (só olhar a **hora** em que a issue entrou na sprint, sem olhar o status) não funcionou — validado contra dados reais, os números não mudaram. Investigando o porquê: o rollover de sprint do Jira move issues novas e migradas **no mesmo evento em lote**, no mesmo instante — então a hora de entrada sozinha não distinguia "trabalho novo" de "sobra de sprint anterior".

Critério corrigido, confirmado com o usuário: olhar o **status da issue no momento em que ela entrou na sprint atual** (via changelog, mesma lógica de `sprint_scope_changes`). Se já era Under PR Review ou mais avançado no fluxo, **todo** apontamento dela fica de fora do ranking desta semana — mesmo o que foi logado depois de entrar na sprint. Novo helper `_status_at` (`person_metrics.py`) + `_ADVANCED_ENTRY_RANK`; issues sem histórico de status até o momento de entrada não são excluídas por precaução (dado incompleto não deve apagar apontamento real). Aplicado nos rankings semanal e diário (mesma base `_positive_timespent_deltas`).

Validado contra a sprint 138 (W29): agora sim os números mudam — `diogo.bastos` caiu de 96300s pra 92700s (1h excluída, de uma issue que entrou na sprint já em "Deploy para prod"). Encontradas ~29 issues do diogo que entraram na W29 já em "To Test" ou "Deploy para prod" — confirma exatamente o cenário relatado. Diário e semanal batem entre si (92700s incluindo sexta-feira nos dois).

**Status:** 1ª, 2ª e 3ª camadas (semanal + diária + exclusão de issues migradas já avançadas) implementadas e **confirmadas pelo usuário** (2026-07-20) como corretas, após conferir manualmente as 10h do `diogo.bastos` no dia — 3 tasks em "To Test" (TEC-10022, TEC-10016, TEC-10014), nenhuma excluída pela regra nova (sem histórico de status antes da entrada na sprint, tratado como "não sei" por precaução). Falta decidir se cabe também comparar contra o tempo *decorrido da sprint* usando as datas reais da sprint (hoje usa semana civil) — a definir com o usuário.

## 3. Vincular itens da sprint ao Mapa de Tecnologia

**Problema:** hoje não há vínculo entre o que está na sprint (issues do Jira) e o "Mapa de Tecnologia" — uma planilha Google Sheets externa (`MAPA 2026 - Tecnologia`, aba "[Desenvolvimento] Planejamento Q3") onde o time de produto planeja iniciativas por trimestre.

**Estrutura real da planilha** (lida diretamente via Google Drive nesta sessão): uma linha por iniciativa ("Tarefa"), colunas `Status, Frente, Tarefa, Atuantes, ICE (Impacto/Confiança/Facilidade/Score), Entrega, Tamanho do Projeto, Motivo, Lançamento` + marcadores semanais (P/E/R) de 2026-2027.

**Casamento automático por texto testado e descartado:** cada "Tarefa" da planilha corresponde a um **Epic** do Jira, mas comparar o texto de "Tarefa" com o `summary` do Epic (`difflib.SequenceMatcher` normalizado) não é confiável — o par certo (HTML) pontuou só 0.45, e um Epic errado pontuou mais alto (0.46). **Decisão (confirmada com o usuário): curadoria manual** — nova coluna na planilha, **"Epic Jira"**, preenchida à mão com a chave do Epic (ex: `TEC-9346`).

**Tentativa 1 (service account) — descartada:** implementada, mas o usuário não pode usá-la — Google Cloud Console está **fora de alcance** neste ambiente (sem admin/projeto disponível), e a planilha **não pode** ficar acessível por link (dado sensível de roadmap). Removida a dependência `google-auth`/`requests`/`cryptography` inteira (junto com ela, some o bug de "Illegal Instruction" documentado em `docs/decisions/0005`, agora marcado revertido).

**Implementado (2026-07-20): importação por colar/paste, sem credencial nenhuma.**
- Jira: campo de sistema `parent` (não customfield) sincronizado (`issues.parent_jira_key`) — pra issues de nível 0 é o Epic. Confirmado real: `TEC-10014.parent.key == "TEC-9346"`.
- Nova tabela `tech_map_entries` (ver `docs/data-model.md`) + `backend/app/integrations/google_sheets/mappers.py` (parsing por nome de coluna, robusto a colunas "largas" tipo Atuantes/ICE sem depender de posição fixa — reaproveitado da tentativa 1, formato-agnóstico).
- `POST /api/tech-map/import` — recebe o texto colado (TSV, formato nativo do clipboard do Google Sheets), faz replace completo da aba. `GET /api/tech-map/sprints/{id}` — agrupa as issues da sprint por Epic e junta com o Mapa de Tecnologia.
- Nova seção "Mapa de Tecnologia" na `CurrentSprintPage` (mostra issues por Epic + Frente/Status/ICE/Entrega) e nova seção de importação (caixa de texto + botão) na aba Atualização — instrui: abrir a planilha, selecionar a aba inteira, copiar (Ctrl+C), colar e importar.
- Validado com dados sintéticos primeiro (import → parse → grava → agrupa por Epic), depois **com a planilha real** (2026-07-20): usuário colou a aba de verdade, **50 linhas importadas com sucesso**. Conferido no banco: `Status`, `Frente`, `Tarefa`, `Atuantes`, `ICE` (Impacto/Confiança/Facilidade/Score) e `Entrega` bateram exatamente com o esperado (ex: linha do HTML — Status "Em andamento", Frente "Receita", Atuantes "PO,UX,BACK,FRONT", ICE 8/9/6/432, Entrega "W30"). Estrutura real confirmada: "Atuantes" é uma única coluna com texto já unido por vírgula (não múltiplas colunas como eu tinha especulado antes de ver dado real); "ICE" de fato são 4 colunas adjacentes.
- **Coluna "Epic Jira" ainda não preenchida** pelo usuário — todas as 50 linhas importadas corretamente têm `epic_jira_key = null`, como esperado (não é bug: confirmado que o usuário ainda não colocou nenhum valor nela). Assim que preencher e reimportar, os vínculos devem aparecer na seção "Mapa de Tecnologia" da Sprint Atual.
- Comentários do parser (`google_sheets/mappers.py`) atualizados pra refletir a estrutura confirmada, em vez da hipótese original (célula de cabeçalho mesclada).

**Status:** implementado e validado com dados reais. Falta só o usuário preencher "Epic Jira" (curadoria manual, aos poucos) e reimportar pra os vínculos aparecerem.

**Status:** implementado, aguardando credenciais do usuário pra validar o sync end-to-end com dados reais da planilha.

---

*Mais pontos serão adicionados conforme o usuário os levantar.*
