"""Ordem lógica do fluxo de trabalho do time, para exibir status agrupados de forma legível.

Os nomes reais de status no Jira variam (histórico/nomenclatura, não workflows
diferentes por tipo de issue — confirmado com o usuário) — por isso o match é
case-insensitive e agrupa variantes conhecidas do mesmo passo do fluxo.
"""

_WORKFLOW_ORDER: list[list[str]] = [
    ["backlog"],
    ["to do"],
    ["in progress", "em andamento"],
    ["is blocked"],
    ["to test"],
    ["testing", "teste"],
    ["to review", "under pr review"],
    ["review", "reviewed"],
    ["deploy para prod"],
]


def _rank(status: str) -> tuple[int, str]:
    normalized = status.strip().lower()
    for index, variants in enumerate(_WORKFLOW_ORDER):
        if normalized in variants:
            return (index, status)
    return (len(_WORKFLOW_ORDER), status)


def sort_statuses(counts: dict[str, int]) -> dict[str, int]:
    """Reordena um dict {status: contagem} pela ordem lógica do fluxo de trabalho."""
    return dict(sorted(counts.items(), key=lambda item: _rank(item[0])))
