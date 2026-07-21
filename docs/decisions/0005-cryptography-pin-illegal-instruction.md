# 0005 — `cryptography` fixado em `<43.0` (Illegal Instruction no runtime)

**Status (2026-07-20): revertido.** A integração por service account que motivou esta dependência foi abandonada — Google Cloud está fora de alcance neste ambiente (sem admin/projeto disponível). `google-auth`/`requests`/`cryptography` foram removidos de `pyproject.toml`; o Mapa de Tecnologia agora é importado por colar/paste (TSV), sem nenhuma dependência de criptografia nova. Mantido este registro porque o achado técnico (incompatibilidade real de `cryptography` >=43 com este ambiente arm64) continua válido e vale a pena consultar se essa dependência for reintroduzida no futuro por qualquer outro motivo.

## Contexto

Ao integrar o Mapa de Tecnologia (Google Sheets, autenticação via service account), a dependência nova `google-auth` puxa `cryptography` (assinatura RSA do JWT de autenticação). Com `cryptography==49.0.0` (resolvido por padrão), o **container do backend crashava ao subir** com `Illegal Instruction` (exit code 132) — mesma família do bug já documentado em `docs/decisions/0002-sem-poetry-no-dockerfile.md` (lá era o Poetry puxando `cryptography` como dependência transitiva do keyring; aqui é a aplicação usando `cryptography` diretamente).

Isolado via `docker compose run --rm --entrypoint python backend -c "..."`: `import cryptography` sozinho funciona; o crash específico é em `cryptography.hazmat.primitives.asymmetric.rsa` (usado por qualquer assinatura/verificação RSA, incluindo o fluxo de service account do Google). Ambiente: `python:3.12-slim` nativo `arm64` (Docker Desktop, macOS Apple Silicon) — o wheel compilado (Rust) do `cryptography` 49.x tem alguma incompatibilidade de instrução de CPU nesse ambiente especificamente.

## Decisão

`backend/pyproject.toml` fixa `cryptography (>=42.0,<43.0)` explicitamente nas dependências (mesmo sendo transitiva de `google-auth`) — testado e confirmado que `42.0.8` importa e assina RSA sem crash no mesmo ambiente.

## Consequências

- Se `google-auth` (ou qualquer outra lib) exigir uma versão mais nova de `cryptography` no futuro, o `poetry lock` vai falhar por conflito de constraint — não subir essa fixação sem antes testar `cryptography.hazmat.primitives.asymmetric.rsa` no ambiente real (`docker compose run --rm --entrypoint python backend -c "import cryptography.hazmat.primitives.asymmetric.rsa"`).
- Mudança de dependência exige **rebuild da imagem** (`docker compose build backend`) — só reiniciar o container (`restart`) não reinstala pacotes Python, e só `up -d --force-recreate` sem rebuild usa a imagem antiga em cache.
- Registrar aqui em vez de só no `docs/decisions/0002` porque a causa raiz é a mesma (incompatibilidade da wheel `cryptography` com este ambiente arm64), mas o ponto de entrada é diferente (dependência direta da aplicação agora, não só do Poetry) — vale a pena ambos os documentos existirem pra quem for debugar um crash parecido no futuro.
