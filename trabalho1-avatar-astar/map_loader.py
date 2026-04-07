# =============================================================================
# map_loader.py — Leitura e parsing do mapa Avatar A*
# =============================================================================

from __future__ import annotations

import os
from typing import NamedTuple

from config import (
    CHECKPOINT_SET,
    CHECKPOINT_SYMBOLS,
    MAP_COLS,
    MAP_ROWS,
    TERRAIN_COSTS,
)

# Célula de terreno plano (usada nos tiles de checkpoint)
_PLAIN = "."


class MapData(NamedTuple):
    """Resultado de load_map."""

    grid: list[list[str]]
    """grid[row][col] = caractere de terreno (nunca um símbolo de checkpoint)."""

    checkpoints: dict[str, tuple[int, int]]
    """Mapeamento símbolo → (row, col) de cada checkpoint encontrado."""


def load_map(filepath: str) -> MapData:
    """Carrega o mapa a partir de um arquivo .txt.

    Cada caractere do arquivo representa uma célula do grid 82 × 300.
    Checkpoints (símbolos especiais) são registrados e substituídos por
    terreno plano ('.') para que o pathfinding os trate como custo 1.

    Parameters
    ----------
    filepath:
        Caminho para o arquivo de mapa (absoluto ou relativo ao CWD).

    Returns
    -------
    MapData
        ``grid``        — lista de listas de caracteres de terreno.
        ``checkpoints`` — dict {símbolo: (row, col)}.

    Raises
    ------
    FileNotFoundError
        Se ``filepath`` não existir.
    ValueError
        Se o mapa não tiver exatamente MAP_ROWS × MAP_COLS células, ou se
        algum caractere desconhecido for encontrado.
    """
    filepath = os.path.abspath(filepath)
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Arquivo de mapa não encontrado: {filepath}")

    with open(filepath, encoding="utf-8") as fh:
        raw_lines = fh.read().splitlines()

    # ------------------------------------------------------------------
    # Validação de dimensões
    # ------------------------------------------------------------------
    actual_rows = len(raw_lines)
    if actual_rows != MAP_ROWS:
        raise ValueError(
            f"O mapa deve ter {MAP_ROWS} linhas, mas tem {actual_rows}."
        )

    col_lengths = {len(line) for line in raw_lines}
    if col_lengths != {MAP_COLS}:
        bad = {n for n in col_lengths if n != MAP_COLS}
        raise ValueError(
            f"Todas as linhas devem ter {MAP_COLS} colunas. "
            f"Tamanhos inválidos encontrados: {sorted(bad)}"
        )

    # ------------------------------------------------------------------
    # Parsing célula a célula
    # ------------------------------------------------------------------
    known_chars = set(TERRAIN_COSTS.keys()) | CHECKPOINT_SET

    grid: list[list[str]] = []
    checkpoints: dict[str, tuple[int, int]] = {}

    for row, line in enumerate(raw_lines):
        grid_row: list[str] = []
        for col, ch in enumerate(line):
            if ch in CHECKPOINT_SET:
                checkpoints[ch] = (row, col)
                grid_row.append(_PLAIN)        # trata como plano no pathfinding
            elif ch in TERRAIN_COSTS:
                grid_row.append(ch)
            else:
                raise ValueError(
                    f"Caractere desconhecido '{ch}' em ({row}, {col})."
                )
        grid.append(grid_row)

    # ------------------------------------------------------------------
    # Verificar se todos os checkpoints esperados foram encontrados
    # ------------------------------------------------------------------
    missing = [s for s in CHECKPOINT_SYMBOLS if s not in checkpoints]
    if missing:
        raise ValueError(
            f"Checkpoints ausentes no mapa: {missing}"
        )

    return MapData(grid=grid, checkpoints=checkpoints)


def terrain_cost(grid: list[list[str]], row: int, col: int) -> int:
    """Retorna o custo de terreno da célula (row, col)."""
    return TERRAIN_COSTS[grid[row][col]]


def in_bounds(grid: list[list[str]], row: int, col: int) -> bool:
    """Verifica se (row, col) está dentro dos limites do grid."""
    return 0 <= row < len(grid) and 0 <= col < len(grid[0])
