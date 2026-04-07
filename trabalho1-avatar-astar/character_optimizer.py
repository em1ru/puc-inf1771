# =============================================================================
# character_optimizer.py — Alocacao otima de personagens nas etapas
#
# Problema:
#   - 31 etapas com dificuldade (ids 1-31, dificuldades 10..310)
#   - 7 personagens, cada um com max_uses = 8  (total = 56 usos)
#   - 56 >= 31: invariante de viabilidade garantido
#   - tempo_etapa_i = dificuldade_i / soma(agilidades dos escolhidos)
#   - Objetivo: minimizar soma total dos tempos
#
# Abordagens:
#   1. Greedy proporcional — distribui usos proporcionalmente a dificuldade
#   2. Simulated Annealing — busca local com 4 movimentos de vizinhanca
# =============================================================================

from __future__ import annotations

import math
import random
from copy import deepcopy
from dataclasses import dataclass
from typing import Optional

from config import CHARACTERS, STAGES

# ---------------------------------------------------------------------------
# Tipos
# ---------------------------------------------------------------------------

Allocation = dict[int, frozenset[str]]   # stage_id -> frozenset de nomes


@dataclass
class StageResult:
    stage_id: int
    difficulty: int
    characters: list[str]
    agility_sum: float
    time: float


@dataclass
class OptimizationResult:
    stage_results: list[StageResult]
    total_time: float
    uses_remaining: dict[str, int]
    method: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _active_stages(stages: list[dict]) -> list[dict]:
    """Retorna etapas com dificuldade definida (ids 1-31)."""
    return [s for s in stages if s["difficulty"] is not None]


def _stage_time(difficulty: int, chosen: frozenset[str], characters: dict) -> float:
    return difficulty / sum(characters[c]["agility"] for c in chosen)


def _total_time(alloc: Allocation, stage_map: dict[int, int], characters: dict) -> float:
    return sum(_stage_time(stage_map[sid], ch, characters) for sid, ch in alloc.items())


def _uses(alloc: Allocation, characters: dict) -> dict[str, int]:
    """Conta usos de cada personagem na alocacao atual."""
    counts: dict[str, int] = {name: 0 for name in characters}
    for chosen in alloc.values():
        for c in chosen:
            counts[c] += 1
    return counts


def _remaining_uses(alloc: Allocation, characters: dict) -> dict[str, int]:
    used = _uses(alloc, characters)
    return {name: characters[name]["max_uses"] - used[name] for name in characters}


def validate_allocation(alloc: Allocation, characters: dict) -> list[str]:
    """Retorna lista de erros de constraint; vazio = valido."""
    errors = []
    used = _uses(alloc, characters)
    for name, u in used.items():
        if u > characters[name]["max_uses"]:
            errors.append(f"{name}: {u} usos > max {characters[name]['max_uses']}")
    for sid, chosen in alloc.items():
        if len(chosen) == 0:
            errors.append(f"Etapa {sid}: sem personagens")
    return errors


# ---------------------------------------------------------------------------
# 1. Solucao Gulosa Proporcional
# ---------------------------------------------------------------------------

def _proportional_counts(
    difficulties: list[int],
    total_uses: int,
) -> list[int]:
    """Distribui total_uses proporcionalmente as dificuldades (min 1 por etapa).

    Usa o metodo do maior resto (Largest Remainder Method):
    1. Garante minimo 1 em todas as etapas.
    2. Distribui os usos restantes (total_uses - n_stages) proporcionalmente.
    3. Aplica LRM para arredondar sem perder nem ganhar usos.
    """
    n = len(difficulties)
    extra = total_uses - n          # usos alem do minimo
    assert extra >= 0, "Usos insuficientes para cobrir todas as etapas"

    total_diff = sum(difficulties)
    # Parte proporcional de cada etapa nos usos extras
    ideals = [d / total_diff * extra for d in difficulties]
    floors = [int(f) for f in ideals]
    fracs  = [ideals[i] - floors[i] for i in range(n)]

    remainder = extra - sum(floors)
    # Distribui o resto pelos maiores restos fracionarios
    order = sorted(range(n), key=lambda i: fracs[i], reverse=True)
    for k in range(remainder):
        floors[order[k]] += 1

    return [1 + f for f in floors]   # +1 pelo minimo


def greedy_allocation(
    stages: list[dict],
    characters: dict = CHARACTERS,
) -> Allocation:
    """Alocacao gulosa proporcional a dificuldade com lookahead.

    Estrategia (processar da mais dificil para a mais facil):
      - Calcula quantos personagens cada etapa merece proporcionalmente
        a dificuldade, usando Largest Remainder Method sobre os usos extras.
      - Ao processar cada etapa, recalcula o ideal sobre os usos e dificuldades
        *restantes* (lookahead), evitando esgotar usos cedo demais.
      - Clamp garante que sobram usos suficientes para as etapas futuras.

    Invariante: antes da etapa i, sum(remaining) >= stages_left
    """
    active = sorted(_active_stages(stages), key=lambda s: s["difficulty"], reverse=True)
    n_active = len(active)
    total_uses = sum(c["max_uses"] for c in characters.values())

    # Pre-calcula contagens proporcional (para referencia inicial)
    diffs_sorted = [s["difficulty"] for s in active]
    target_counts = _proportional_counts(diffs_sorted, total_uses)

    remaining = {name: characters[name]["max_uses"] for name in characters}
    chars_by_agility = sorted(characters, key=lambda c: characters[c]["agility"], reverse=True)
    alloc: Allocation = {}

    for i, stage in enumerate(active):
        stages_left = n_active - i
        total_remaining = sum(remaining.values())

        # Recalcula ideal sobre dificuldades restantes (lookahead)
        future_diffs = [s["difficulty"] for s in active[i:]]
        future_total = sum(future_diffs)
        weight = stage["difficulty"] / future_total
        ideal = weight * total_remaining

        # Arredonda e aplica constraints
        n_chars = max(1, round(ideal))
        # Nao pode gastar mais do que sobra para as etapas futuras
        budget_cap = total_remaining - (stages_left - 1)
        n_chars = min(n_chars, budget_cap)
        n_chars = max(1, n_chars)    # garantia final

        available = [c for c in chars_by_agility if remaining[c] > 0]
        chosen = available[:n_chars]
        for c in chosen:
            remaining[c] -= 1
        alloc[stage["id"]] = frozenset(chosen)

    return alloc


# ---------------------------------------------------------------------------
# 2. Simulated Annealing
# ---------------------------------------------------------------------------

def _neighbor(
    alloc: Allocation,
    stage_map: dict[int, int],
    characters: dict,
    rng: random.Random,
) -> Optional[Allocation]:
    """Gera um estado vizinho valido.

    Movimentos (pesos iguais):
      SWAP         — troca um personagem exclusivo entre duas etapas
      ADD          — adiciona personagem com uso livre a uma etapa
      REMOVE       — remove um personagem de uma etapa com >= 2
      REDISTRIBUTE — move personagem de uma etapa grande para uma pequena
    """
    stage_ids = list(alloc.keys())
    remaining = _remaining_uses(alloc, characters)
    move = rng.choice(["swap", "add", "remove", "redistribute"])

    if move == "swap":
        if len(stage_ids) < 2:
            return None
        sid_a, sid_b = rng.sample(stage_ids, 2)
        set_a, set_b = alloc[sid_a], alloc[sid_b]
        only_a = [c for c in set_a if c not in set_b]
        only_b = [c for c in set_b if c not in set_a]
        if not only_a or not only_b:
            return None
        ca, cb = rng.choice(only_a), rng.choice(only_b)
        new = dict(alloc)
        new[sid_a] = (set_a - {ca}) | {cb}
        new[sid_b] = (set_b - {cb}) | {ca}
        return new

    elif move == "add":
        sid = rng.choice(stage_ids)
        candidates = [c for c in characters if remaining[c] > 0 and c not in alloc[sid]]
        if not candidates:
            return None
        ca = rng.choice(candidates)
        new = dict(alloc)
        new[sid] = alloc[sid] | {ca}
        return new

    elif move == "remove":
        big = [sid for sid in stage_ids if len(alloc[sid]) >= 2]
        if not big:
            return None
        sid = rng.choice(big)
        ca = rng.choice(list(alloc[sid]))
        new = dict(alloc)
        new[sid] = alloc[sid] - {ca}
        return new

    else:  # redistribute
        # Etapa "grande" (acima da mediana) -> etapa "pequena" (abaixo)
        sizes = {sid: len(alloc[sid]) for sid in stage_ids}
        med = sorted(sizes.values())[len(sizes) // 2]
        big  = [sid for sid, s in sizes.items() if s > med and s >= 2]
        small = [sid for sid, s in sizes.items() if s < med]
        if not big or not small:
            return None
        sid_from = rng.choice(big)
        sid_to   = rng.choice(small)
        # Escolhe personagem que esta em sid_from mas nao em sid_to
        movable = [c for c in alloc[sid_from] if c not in alloc[sid_to]]
        if not movable:
            return None
        ca = rng.choice(movable)
        new = dict(alloc)
        new[sid_from] = alloc[sid_from] - {ca}
        new[sid_to]   = alloc[sid_to]   | {ca}
        return new


def simulated_annealing(
    stages: list[dict],
    characters: dict = CHARACTERS,
    initial_alloc: Optional[Allocation] = None,
    T_start: float = 80.0,
    T_end: float = 0.01,
    alpha: float = 0.99995,
    max_iter: int = 500_000,
    seed: Optional[int] = 42,
) -> Allocation:
    """Simulated Annealing para minimizar tempo total das etapas.

    Parameters
    ----------
    T_start : temperatura inicial (aceita pioras com alta probabilidade)
    T_end   : temperatura minima (so aceita melhoras)
    alpha   : fator de resfriamento geometrico por iteracao
    max_iter: limite de iteracoes
    seed    : semente para reproducibilidade
    """
    rng = random.Random(seed)
    active = _active_stages(stages)
    stage_map = {s["id"]: s["difficulty"] for s in active}

    current = deepcopy(initial_alloc) if initial_alloc else greedy_allocation(stages, characters)
    current_cost = _total_time(current, stage_map, characters)
    best = deepcopy(current)
    best_cost = current_cost

    T = T_start
    for _ in range(max_iter):
        candidate = _neighbor(current, stage_map, characters, rng)
        if candidate is None:
            T = max(T * alpha, T_end)
            continue

        candidate_cost = _total_time(candidate, stage_map, characters)
        delta = candidate_cost - current_cost

        if delta < 0 or rng.random() < math.exp(-delta / T):
            current = candidate
            current_cost = candidate_cost
            if current_cost < best_cost:
                best = deepcopy(current)
                best_cost = current_cost

        T = max(T * alpha, T_end)
        if T <= T_end:
            break

    return best


# ---------------------------------------------------------------------------
# Interface publica
# ---------------------------------------------------------------------------

def optimize_characters(
    stages: list[dict] = STAGES,
    characters: dict = CHARACTERS,
    method: str = "sa",
    sa_kwargs: Optional[dict] = None,
) -> OptimizationResult:
    """Alocacao otimizada de personagens para as etapas.

    Parameters
    ----------
    method : "greedy" ou "sa" (SA usa greedy como ponto de partida)
    sa_kwargs : parametros extras para simulated_annealing()
    """
    active = _active_stages(stages)
    stage_map = {s["id"]: s["difficulty"] for s in active}

    greedy_alloc = greedy_allocation(stages, characters)

    if method == "greedy":
        best_alloc = greedy_alloc
        label = "Greedy"
    else:
        kwargs = sa_kwargs or {}
        best_alloc = simulated_annealing(
            stages, characters, initial_alloc=greedy_alloc, **kwargs
        )
        label = "Simulated Annealing"

    stage_results: list[StageResult] = []
    for stage in sorted(active, key=lambda s: s["id"]):
        sid  = stage["id"]
        diff = stage["difficulty"]
        chosen = sorted(best_alloc[sid])
        ag_sum = sum(characters[c]["agility"] for c in chosen)
        stage_results.append(StageResult(
            stage_id=sid,
            difficulty=diff,
            characters=chosen,
            agility_sum=round(ag_sum, 4),
            time=round(diff / ag_sum, 6),
        ))

    total = sum(r.time for r in stage_results)
    remaining = _remaining_uses(best_alloc, characters)

    return OptimizationResult(
        stage_results=stage_results,
        total_time=round(total, 6),
        uses_remaining=remaining,
        method=label,
    )


# ---------------------------------------------------------------------------
# Execucao direta / teste
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import time as _time

    greedy_result = optimize_characters(method="greedy")
    print(f"=== {greedy_result.method} ===")
    for r in greedy_result.stage_results:
        print(f"  Etapa {r.stage_id:2d} (dif={r.difficulty:3d})"
              f"  ag={r.agility_sum:.1f}  tempo={r.time:7.3f}"
              f"  | {', '.join(r.characters)}")
    errs = validate_allocation(
        {r.stage_id: frozenset(r.characters) for r in greedy_result.stage_results},
        CHARACTERS)
    print(f"\n  Usos restantes: {greedy_result.uses_remaining}")
    print(f"  Violacoes: {errs if errs else 'nenhuma'}")
    print(f"  Tempo total: {greedy_result.total_time:.4f}\n")

    t0 = _time.perf_counter()
    sa_result = optimize_characters(method="sa")
    elapsed = _time.perf_counter() - t0
    print(f"=== {sa_result.method} ({elapsed:.1f}s) ===")
    for r in sa_result.stage_results:
        print(f"  Etapa {r.stage_id:2d} (dif={r.difficulty:3d})"
              f"  ag={r.agility_sum:.1f}  tempo={r.time:7.3f}"
              f"  | {', '.join(r.characters)}")
    errs = validate_allocation(
        {r.stage_id: frozenset(r.characters) for r in sa_result.stage_results},
        CHARACTERS)
    print(f"\n  Usos restantes: {sa_result.uses_remaining}")
    print(f"  Violacoes: {errs if errs else 'nenhuma'}")
    print(f"  Tempo total: {sa_result.total_time:.4f}")
    diff = greedy_result.total_time - sa_result.total_time
    pct  = (1 - sa_result.total_time / greedy_result.total_time) * 100
    print(f"\n  Melhoria SA vs Greedy: -{diff:.4f} ({pct:.2f}%)")
