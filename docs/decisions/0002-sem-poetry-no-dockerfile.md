# 0002 — Dockerfile do backend não instala Poetry, usa pip direto

## Contexto

A primeira versão do `backend/Dockerfile` instalava o Poetry via `pip install poetry` dentro da imagem para rodar `poetry install`. No build local (Docker Desktop, macOS Apple Silicon, imagem `python:3.12-slim` nativa arm64), o passo `poetry install` falhava com `Illegal instruction` (exit code 132). A causa é uma dependência transitiva do próprio Poetry (`cryptography`/`keyring`/`SecretStorage`, usadas para armazenamento de credenciais que este projeto não usa) cujo wheel compilado é incompatível com o ambiente. Não é um problema do código da aplicação.

## Decisão

O `Dockerfile` do backend não instala o Poetry. Ele usa `pip install .` direto sobre o `pyproject.toml` (o backend de build é `poetry-core`, que o pip já sabe usar via PEP 517) para instalar a aplicação e suas dependências, sem precisar do CLI completo do Poetry dentro da imagem de runtime.

Poetry continua sendo a ferramenta de desenvolvimento local (gerencia `poetry.lock`, `poetry install`, `poetry run ...` fora do container) — só não entra na imagem Docker.

## Consequências

- Se alguém (humano ou IA) "consertar" o Dockerfile reintroduzindo `pip install poetry`, o build provavelmente volta a falhar neste tipo de ambiente. Antes de reverter esta decisão, confirmar que o crash de `Illegal instruction` não se repete.
- A imagem de runtime fica mais enxuta (sem Poetry/keyring/cryptography extras que a aplicação não usa).
- Effect colateral aceito: o Dockerfile perde parte do cache em camadas entre dependências e código (`COPY app ./app` acontece antes do `pip install .`, porque `poetry-core` precisa do pacote presente para buildar) — aceitável para o estágio atual do projeto.
