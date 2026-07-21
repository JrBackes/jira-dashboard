"""Parsing da aba "[Desenvolvimento] Planejamento Q3" do Mapa de Tecnologia.

A aba tem cabeçalho por NOME de coluna, não posição fixa. Confirmado contra uma importação
real (2026-07-20, 50 linhas): "Atuantes" é uma única coluna com texto já unido por vírgula
(ex: "PO,UX,BACK,FRONT"); "ICE" na prática são 4 colunas adjacentes (Impacto, Confiança,
Facilidade, Score). O parsing localiza cada coluna conhecida pelo nome no cabeçalho e lê o
intervalo até a próxima âncora conhecida — funciona igual pra coluna única ou múltipla, sem
precisar assumir a largura de antemão.
"""

from datetime import datetime, timezone

_TARGET_HEADER = "tarefa"
_ANCHOR_COLUMNS = ["status", "frente", "tarefa", "atuantes", "ice", "entrega", "tamanho do projeto", "motivo", "lançamento"]


def _normalize_header(cell: str) -> str:
    return (cell or "").strip().lower()


def _find_header_row(values: list[list[str]]) -> int | None:
    for idx, row in enumerate(values):
        if any(_normalize_header(cell) == _TARGET_HEADER for cell in row):
            return idx
    return None


def _header_index(header_row: list[str]) -> dict[str, int]:
    """Índice de cada célula do cabeçalho pelo nome normalizado -> posição. Em caso de nomes
    repetidos, mantém a primeira ocorrência (colunas de semana não colidem com os nomes
    esperados aqui)."""
    index: dict[str, int] = {}
    for i, cell in enumerate(header_row):
        key = _normalize_header(cell)
        if key and key not in index:
            index[key] = i
    return index


def _cell(row: list[str], idx: int | None) -> str:
    if idx is None or idx >= len(row):
        return ""
    return (row[idx] or "").strip()


def _cells_between(row: list[str], start: int | None, end: int | None) -> list[str]:
    """Valores não vazios a partir de uma coluna-âncora até a próxima âncora conhecida
    (inclusive no início, exclusive no fim) — cobre tanto coluna única ("Atuantes", já vem
    como texto único) quanto múltiplas colunas adjacentes ("ICE" = Impacto/Confiança/
    Facilidade/Score), sem precisar saber a largura de cada uma de antemão."""
    if start is None or end is None:
        return []
    return [v.strip() for v in row[start:end] if (v or "").strip()]


def _to_float(value: str) -> float | None:
    try:
        return float(value.replace(",", "."))
    except (ValueError, AttributeError):
        return None


def parse_tech_map_rows(values: list[list[str]], sheet_name: str) -> list[dict]:
    """Converte a matriz bruta de valores da aba em uma lista de dicts prontos pra
    `TechMapEntry`. Ignora linhas sem "Tarefa" preenchida (linhas de grupo/legenda/em branco)."""
    header_row_idx = _find_header_row(values)
    if header_row_idx is None:
        return []

    header = _header_index(values[header_row_idx])
    anchors = {name: header.get(name) for name in _ANCHOR_COLUMNS}
    epic_col = header.get("epic jira")

    entries: list[dict] = []
    now = datetime.now(timezone.utc)

    for row_idx, row in enumerate(values[header_row_idx + 1 :], start=header_row_idx + 1):
        tarefa = _cell(row, anchors["tarefa"])
        if not tarefa:
            continue

        atuantes_values = _cells_between(row, anchors["atuantes"], anchors["ice"])
        ice_values = _cells_between(row, anchors["ice"], anchors["entrega"])
        ice_floats = [_to_float(v) for v in ice_values]

        entries.append(
            {
                "sheet_name": sheet_name,
                "row_index": row_idx,
                "status": _cell(row, anchors["status"]) or None,
                "frente": _cell(row, anchors["frente"]) or None,
                "tarefa": tarefa,
                "atuantes": ", ".join(atuantes_values) or None,
                "ice_impacto": ice_floats[0] if len(ice_floats) > 0 else None,
                "ice_confianca": ice_floats[1] if len(ice_floats) > 1 else None,
                "ice_facilidade": ice_floats[2] if len(ice_floats) > 2 else None,
                "ice_score": ice_floats[3] if len(ice_floats) > 3 else None,
                "entrega": _cell(row, anchors["entrega"]) or None,
                "tamanho_projeto": _cell(row, anchors["tamanho do projeto"]) or None,
                "motivo": _cell(row, anchors["motivo"]) or None,
                "lancamento": _cell(row, anchors["lançamento"]) or None,
                "epic_jira_key": (_cell(row, epic_col) or None) if epic_col is not None else None,
                "raw_row": row,
                "synced_at": now,
            }
        )
    return entries
