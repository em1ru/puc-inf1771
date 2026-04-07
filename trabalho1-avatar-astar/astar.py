# =============================================================================
# astar.py — Algoritmo A* para pathfinding no grid do mapa Avatar
# =============================================================================

from __future__ import annotations

import heapq
from typing import Optional

from config import TERRAIN_COSTS, CHECKPOINT_SYMBOLS
from map_loader import load_map

# Direções: apenas 4 (sem diagonais)
_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


# -----------------------------------------------------------------------------
# Heurística
# -----------------------------------------------------------------------------

def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Distância de Manhattan entre dois pontos do grid.

    Admissível pois o menor custo de terreno é 1 e não há movimentos diagonais,
    portanto h(n) nunca superestima o custo real.
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


# -----------------------------------------------------------------------------
# A*
# -----------------------------------------------------------------------------

def astar(
    grid: list[list[str]],
    start: tuple[int, int],
    goal: tuple[int, int],
    terrain_costs: dict[str, int] = TERRAIN_COSTS,
) -> tuple[list[tuple[int, int]], int]:
    """Encontra o caminho de custo mínimo de *start* a *goal* via A*.

    Parameters
    ----------
    grid:
        Matriz 82 × 300 de caracteres de terreno. Checkpoints já devem ter
        sido substituídos por '.' pelo map_loader.
    start:
        Coordenada de origem (row, col).
    goal:
        Coordenada de destino (row, col).
    terrain_costs:
        Dicionário {char: custo} importado de config.py.

    Returns
    -------
    (path, cost)
        path — lista de (row, col) do início ao fim, inclusive.
        cost — custo total acumulado (soma dos custos de cada célula visitada).

    Raises
    ------
    ValueError
        Se não existir caminho entre start e goal.
    """
    rows = len(grid)
    cols = len(grid[0])

    def in_bounds(r: int, c: int) -> bool:
        return 0 <= r < rows and 0 <= c < cols

    # ------------------------------------------------------------------
    # Estruturas de dados
    # ------------------------------------------------------------------
    # Open list: (f, counter, g, node)
    # O counter garante tie-breaking por ordem de inserção (FIFO entre
    # nós com mesmo f), evitando comparações entre tuplas de coordenadas.
    counter = 0
    open_heap: list[tuple[int, int, int, tuple[int, int]]] = []

    g_scores: dict[tuple[int, int], int] = {}   # custo real até cada nó
    came_from: dict[tuple[int, int], Optional[tuple[int, int]]] = {}

    g_start = 0
    g_scores[start] = g_start
    came_from[start] = None
    h_start = _manhattan(start, goal)
    heapq.heappush(open_heap, (g_start + h_start, counter, g_start, start))

    closed: set[tuple[int, int]] = set()

    # ------------------------------------------------------------------
    # Loop principal
    # ------------------------------------------------------------------
    while open_heap:
        f, _, g, current = heapq.heappop(open_heap)

        if current in closed:
            continue
        closed.add(current)

        if current == goal:
            return _reconstruct(came_from, goal), g

        r, c = current
        for dr, dc in _DIRS:
            nr, nc = r + dr, c + dc
            if not in_bounds(nr, nc):
                continue
            neighbor = (nr, nc)
            if neighbor in closed:
                continue

            move_cost = terrain_costs[grid[nr][nc]]
            tentative_g = g + move_cost

            if tentative_g < g_scores.get(neighbor, 2**31):
                g_scores[neighbor] = tentative_g
                came_from[neighbor] = current
                h = _manhattan(neighbor, goal)
                counter += 1
                heapq.heappush(
                    open_heap,
                    (tentative_g + h, counter, tentative_g, neighbor),
                )

    raise ValueError(f"Sem caminho entre {start} e {goal}.")


def _reconstruct(
    came_from: dict[tuple[int, int], Optional[tuple[int, int]]],
    goal: tuple[int, int],
) -> list[tuple[int, int]]:
    """Reconstrói o caminho percorrendo came_from de trás para frente."""
    path: list[tuple[int, int]] = []
    node: Optional[tuple[int, int]] = goal
    while node is not None:
        path.append(node)
        node = came_from[node]
    path.reverse()
    return path


# -----------------------------------------------------------------------------
# Utilitário de alto nível
# -----------------------------------------------------------------------------

def compute_all_paths(
    grid: list[list[str]],
    checkpoints: dict[str, tuple[int, int]],
    terrain_costs: dict[str, int] = TERRAIN_COSTS,
) -> list[tuple[list[tuple[int, int]], int]]:
    """Calcula o A* entre cada par consecutivo de checkpoints (0→1→…→Z).

    Parameters
    ----------
    grid:
        Grid de terreno retornado por load_map.
    checkpoints:
        Dict {símbolo: (row, col)} retornado por load_map.
    terrain_costs:
        Dict de custos de terreno de config.py.

    Returns
    -------
    Lista de (path, cost) para cada um dos 31 segmentos,
    na ordem CHECKPOINT_SYMBOLS[0]→[1], [1]→[2], …, [30]→[31].
    """
    results: list[tuple[list[tuple[int, int]], int]] = []
    for i in range(len(CHECKPOINT_SYMBOLS) - 1):
        sym_a = CHECKPOINT_SYMBOLS[i]
        sym_b = CHECKPOINT_SYMBOLS[i + 1]
        start = checkpoints[sym_a]
        goal  = checkpoints[sym_b]
        path, cost = astar(grid, start, goal, terrain_costs)
        results.append((path, cost))
    return results


# -----------------------------------------------------------------------------
# Teste / execução direta
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import time
    import os

    MAP_PATH = os.path.join(os.path.dirname(__file__), "data", "mapa.txt")
    map_data = load_map(MAP_PATH)

    print("Calculando caminhos entre os 32 checkpoints...\n")
    t0 = time.perf_counter()
    segments = compute_all_paths(map_data.grid, map_data.checkpoints)
    elapsed = time.perf_counter() - t0

    total_cost = 0
    total_cells = 0
    for i, (path, cost) in enumerate(segments):
        sym_a = CHECKPOINT_SYMBOLS[i]
        sym_b = CHECKPOINT_SYMBOLS[i + 1]
        total_cost += cost
        total_cells += len(path)
        print(
            f"  Segmento {i+1:2d}: {sym_a} -> {sym_b}"
            f"  | celulas={len(path):4d}"
            f"  | custo={cost:6d}"
        )

    print(f"\n  Custo total do caminho   : {total_cost}")
    print(f"  Celulas totais no caminho: {total_cells}")
    print(f"  Tempo de execucao        : {elapsed:.3f}s")
