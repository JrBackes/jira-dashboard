# 0003 — Bugs encontrados e corrigidos no primeiro sync real

## Contexto

O `JiraClient` e o pipeline de sync foram implementados com base na documentação pública da API do Jira Cloud, mas nunca tinham rodado contra um site real. Ao rodar o primeiro sync de verdade (site TEC, ~9000 issues), três bugs surgiram — nenhum visível nos testes com dados sintéticos, porque dependiam do formato exato dos payloads reais do Jira.

## Bugs e correções

1. **Limite de lote do `changelog/bulkfetch`**: enviar todos os ~9000 `issueIds` de uma vez num único POST retorna `400 Bad Request`. `JiraClient.fetch_changelogs_bulk` agora pagina em lotes de 1000 (confirmado como aceito pela API) e concatena os resultados.

2. **Formato real do payload do changelog**: a documentação pública sugere uma estrutura aninhada, mas a resposta real de `POST /rest/api/3/changelog/bulkfetch` tem os históricos direto em `issueChangeLogs[].changeHistories[]` (não `changeLog.histories[]`). Além disso, `changeHistories[].created` vem como **epoch em milissegundos (int)**, não string ISO — `datetime.fromisoformat` não lida com isso. Corrigido em `mappers.py` (`parse_jira_changelog_timestamp`) e o parsing agora lê a chave certa. Esse bug era silencioso: como o `.get("changeLog", {})` não existia, retornava `{}`, e o sync completava com "success" processando 0 mudanças de changelog — sem nenhum erro.

3. **Colunas `from_value`/`to_value` pequenas demais**: `String(1000)` estourava em campos como `description`, cujo texto muda com milhares de caracteres. Migradas para `Text` (ver migration `b71d46295ef3`).

4. **Campo Sprint não existe como `sprint`/`closedSprints` no Platform Search API**: esses nomes literais só funcionam na Agile API. No `/rest/api/3/search/jql`, sprint é um customfield (`customfield_10020` neste caso, descoberto via `get_fields()` com `schema.custom == "com.pyxis.greenhopper.jira:gh-sprint"`) que retorna a **lista completa** de sprints por onde a issue já passou (cada uma com seu `state`), não um par `sprint`/`closedSprints` separado. Sem pedir esse customfield explicitamente no `fields` da busca, `issue_sprints` ficava **completamente vazia** — nenhuma métrica de sprint funcionava (contagens, burndown, scope-changes todos retornavam vazio, sem erro nenhum).

5. **`statusCategory.name` é localizado, `statusCategory.key` não é**: o mapper usava `.name` (retorna "Itens concluídos" em instâncias em português) para popular `status_category`, mas todo o resto do código compara contra as chaves estáveis do Jira (`new`/`indeterminate`/`done`, em inglês, sempre). Resultado: todo filtro `status_category == "done"` (workload, highlights, velocity) nunca batia — carga de trabalho de qualquer pessoa aparecia inflada (contando issues concluídas como "em aberto"). Corrigido para usar `.key`.

## Consequência prática

Depois de cada correção, foi necessário resetar `sync_cursors` (deletar as linhas de `entity_type='issues'`) para forçar o pipeline a reprocessar todas as issues do zero — sem isso, o sync incremental só buscaria issues atualizadas após o cursor já salvo, e o changelog (que só roda sobre issues tocadas no ciclo) ficaria incompleto para o histórico de dados já sincronizado antes da correção.

## Consequências

- Os bugs nº 2, 4 e 5 são os mais perigosos de reintroduzir: todos falham **silenciosamente** (sem exception, sync marca "success", mas dados ficam vazios ou errados). Qualquer mudança futura no parsing de issues/changelog deve ser testada contra uma resposta real da API, não só a documentação — dados sintéticos não pegam esse tipo de bug porque o desenvolvedor já monta o payload "do jeito certo".
- `docs/jira-integration.md` foi atualizado com o formato real confirmado do payload (changelog e campo Sprint).
- Regra geral registrada em `AGENTS.md`: sempre usar `statusCategory.key` (estável, en-US) em vez de `.name` (localizado) para qualquer lógica de negócio.
