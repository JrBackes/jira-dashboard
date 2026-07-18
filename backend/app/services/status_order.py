"""Ordem lógica do fluxo de trabalho do time, para exibir status agrupados de forma legível.

Os nomes reais de status no Jira variam (histórico/nomenclatura, não workflows
diferentes por tipo de issue — confirmado com o usuário) — por isso o match é
case-insensitive e agrupa variantes conhecidas do mesmo passo do fluxo.

Significado de cada passo e por que a ordem é essa: ver `docs/workflow-do-time.md`.
"""

_WORKFLOW_ORDER: list[list[str]] = [
    ["backlog"],
    ["to do"],
    ["in progress", "em andamento"],
    ["under pr review"],
    ["is blocked"],
    ["to test"],
    ["testing", "teste"],
    ["deploy para prod"],
    ["to review", "review"],
    ["waiting store approval"],
    ["reviewed"],
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
