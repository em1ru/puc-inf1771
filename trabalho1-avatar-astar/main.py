# =============================================================================
# main.py — Ponto de entrada do projeto Avatar A*
#
# Uso:
#   py main.py                         # roda tudo com visualizacao
#   py main.py --no-viz                # so calcula e imprime
#   py main.py --method greedy         # usa greedy em vez de SA
#   py main.py --map data/mapa.txt     # caminho alternativo do mapa
#   py main.py --speed 20              # velocidade inicial da animacao
#   py main.py --sa-iter 300000        # iteracoes do SA
# =============================================================================

from __future__ import annotations

import argparse
import os
import sys
import time


# ---------------------------------------------------------------------------
# Argumentos
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="avatar_astar",
        description="Avatar A* — Pathfinding e otimizacao de personagens",
    )
    p.add_argument(
        "--map",
        default=os.path.join(os.path.dirname(__file__), "data", "mapa.txt"),
        metavar="PATH",
        help="Caminho do arquivo de mapa (padrao: data/mapa.txt)",
    )
    p.add_argument(
        "--speed",
        type=int,
        default=10,
        metavar="N",
        help="Velocidade inicial da animacao em celulas/frame (padrao: 10)",
    )
    p.add_argument(
        "--no-viz",
        action="store_true",
        help="Executa sem visualizacao pygame (so calcula e imprime)",
    )
    p.add_argument(
        "--method",
        choices=["sa", "greedy"],
        default="sa",
        help="Metodo de otimizacao de personagens: 'sa' ou 'greedy' (padrao: sa)",
    )
    p.add_argument(
        "--sa-iter",
        type=int,
        default=500_000,
        metavar="N",
        help="Numero de iteracoes do Simulated Annealing (padrao: 500000)",
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# Output formatado
# ---------------------------------------------------------------------------

def _print_results(
    segments: list,
    opt_result,
    method_name: str,
) -> None:
    SEP = "=" * 62

    total_path_cost = sum(c for _, c in segments)
    total_time      = opt_result.total_time
    grand_total     = total_path_cost + total_time

    print(SEP)
    print("AVATAR A* — RESULTADO FINAL")
    print(f"Metodo de otimizacao: {method_name}")
    print()

    # --- Caminho A* ---
    print("--- Caminho (A*) ---")
    from config import CHECKPOINT_SYMBOLS
    for i, (path, cost) in enumerate(segments):
        sym_a = CHECKPOINT_SYMBOLS[i]
        sym_b = CHECKPOINT_SYMBOLS[i + 1]
        print(f"  Segmento {i+1:2d}: {sym_a} -> {sym_b}"
              f"  | celulas={len(path):4d}"
              f"  | custo={cost:6d}")
    print(f"\n  Custo total do caminho: {total_path_cost}")

    # --- Etapas ---
    print()
    print("--- Etapas (Personagens) ---")
    for r in opt_result.stage_results:
        chars_fmt = f"[{', '.join(r.characters)}]"
        print(f"  Etapa {r.stage_id:2d} (dif={r.difficulty:3d}): "
              f"{chars_fmt:<35}  ag={r.agility_sum:.2f}  tempo={r.time:7.3f}")
    print(f"\n  Tempo total das etapas: {total_time:.4f}")

    # --- Uso dos personagens ---
    print()
    print("--- Uso dos Personagens ---")
    from config import CHARACTERS
    for name, rem in opt_result.uses_remaining.items():
        used = CHARACTERS[name]["max_uses"] - rem
        mx   = CHARACTERS[name]["max_uses"]
        bar  = "#" * used + "." * rem
        print(f"  {name:<8}: {used}/{mx} usos  [{bar}]")

    # --- Total ---
    print()
    print(SEP)
    print(f"  CUSTO TOTAL: {total_path_cost} + {total_time:.4f} = {grand_total:.4f}")
    print(SEP)


# ---------------------------------------------------------------------------
# Fluxo principal
# ---------------------------------------------------------------------------

def main() -> None:
    args = _parse_args()

    # 1. Carregar mapa
    print(f"[1/3] Carregando mapa: {args.map}")
    try:
        from map_loader import load_map
        map_data = load_map(args.map)
    except FileNotFoundError as exc:
        print(f"  ERRO: {exc}")
        sys.exit(1)
    except ValueError as exc:
        print(f"  ERRO no mapa: {exc}")
        sys.exit(1)
    print(f"      Grid: {len(map_data.grid)} x {len(map_data.grid[0])}"
          f"  |  Checkpoints: {len(map_data.checkpoints)}")

    # 2. Calcular caminhos A*
    print("[2/3] Calculando caminhos A* ...")
    t0 = time.perf_counter()
    try:
        from astar import compute_all_paths
        segments = compute_all_paths(map_data.grid, map_data.checkpoints)
    except ValueError as exc:
        print(f"  ERRO no A*: {exc}")
        sys.exit(1)
    elapsed_astar = time.perf_counter() - t0
    total_cells = sum(len(p) for p, _ in segments)
    print(f"      {len(segments)} segmentos  |  {total_cells} celulas  |  {elapsed_astar:.3f}s")

    # 3. Otimizar personagens
    method_label = "Simulated Annealing" if args.method == "sa" else "Greedy"
    print(f"[3/3] Otimizando personagens ({method_label}) ...")
    t0 = time.perf_counter()
    from character_optimizer import optimize_characters
    sa_kwargs = {"max_iter": args.sa_iter} if args.method == "sa" else None
    opt_result = optimize_characters(method=args.method, sa_kwargs=sa_kwargs)
    elapsed_opt = time.perf_counter() - t0
    print(f"      Tempo total etapas: {opt_result.total_time:.4f}  |  {elapsed_opt:.2f}s")

    # Imprimir resultados
    print()
    _print_results(segments, opt_result, method_label)

    # 4. Visualizacao
    if args.no_viz:
        return

    try:
        import pygame  # noqa: F401 — verifica disponibilidade
    except ImportError:
        print("\npygame nao instalado. Para instalar: pip install pygame")
        print("Executando sem visualizacao.")
        return

    print("\nAbrindo visualizacao pygame ...")
    try:
        from visualizer import AvatarVisualizer
        viz = AvatarVisualizer(
            grid=map_data.grid,
            checkpoints=map_data.checkpoints,
            segments=segments,
            opt_result=opt_result,
            init_speed=args.speed,
        )
        viz.run()
    except Exception as exc:
        print(f"  Erro na visualizacao: {exc}")
        raise


if __name__ == "__main__":
    main()
