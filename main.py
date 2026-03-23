import argparse
import time
import os
import sys
import json

import map_parser
import character_planner
import astar
import visualizer

def generate_synthetic_map_and_checkpoints(rows: int = 82, cols: int = 300) -> list[list[str]]:
    print(f"\n[AVISO CRÍTICO] Arquivo de mapa não encontrado no disco local. "
          f"Gerando bypass visual sintético {rows}x{cols} para teste.")
    grid = [['.' for _ in range(cols)] for _ in range(rows)]
    sequence = [str(i) for i in range(10)] + list("BCDEGHIJKLNOPQSTUVWXYZ")
    for i, ch in enumerate(sequence):
        r = (i * 2 + 1) % rows
        c = (i * 9 + 5) % cols
        grid[r][c] = ch
    return grid

def main():
    parser = argparse.ArgumentParser(description="Orquestrador CLI com Telemetria A*")
    parser.add_argument("--map", type=str, default="mapa.txt", help="Caminho para grade.")
    parser.add_argument("--config", type=str, default="config.json", help="Arquivo JSON.")
    parser.add_argument("--speed", type=float, default=0.05, help="Delay Animação.")
    args = parser.parse_args()
    
    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
    except FileNotFoundError:
        print(f"[ERRO] {args.config} ausente.")
        sys.exit(1)
        
    terrain_costs = cfg.get("terrain_costs", {})
    difficulties = cfg.get("difficulty", {})
    agility = cfg.get("agility", {})
    max_uses = cfg.get("max_uses_per_character", 8)

    try:
        grid = map_parser.load_map(args.map)
        if not grid: raise ValueError()
    except:
        grid = generate_synthetic_map_and_checkpoints()
        
    checkpoints = map_parser.find_checkpoints(grid)
    if not checkpoints: sys.exit(1)
        
    alpha_ref = "0123456789BCDEGHIJKLNOPQSTUVWXYZ"
    sorted_sequence = sorted(checkpoints.keys(), key=lambda k: alpha_ref.index(k) if k in alpha_ref else 999)

    print("\n[PLANEJAMENTO DE PERSONAGENS]...")
    base_chars = character_planner.greedy_assignment(difficulties, agility, max_uses)
    best_assign, _ = character_planner.hill_climbing_optimize(base_chars, difficulties, agility, max_uses, 5000)
    character_planner.print_assignment(best_assign, difficulties, agility)
    print("-> Alocação Concluída.")
    
    time.sleep(1.0)
    print("\n[INICIANDO ROTAS E A* PATHFINDING]\n")
    
    total_terrain_cost = 0
    actual_char_time_accum = 0.0
    
    global_nodes_expanded = 0
    global_exec_time = 0.0
    global_path = []

    for i in range(len(sorted_sequence) - 1):
        origin_id, dest_id = sorted_sequence[i], sorted_sequence[i+1]
        start_coord, goal_coord = checkpoints[origin_id], checkpoints[dest_id]
        
        # Desempacota 4 variáveis (Path, Custo_Fisico, Contagem_Vertices, Segundos_Perfcounter)
        path_segment, segment_cost, nodes_exp, exec_t = astar.astar(grid, start_coord, goal_coord, terrain_costs)
        
        if segment_cost == -1 or not path_segment:
            print(f"[FALHA] {origin_id} para {dest_id} intransponível! A* encerrado.")
            sys.exit(1)
            
        stage_troop = best_assign.get(dest_id, [])
        stage_diff_val = difficulties.get(dest_id, 0)
        
        step_spent_time = (stage_diff_val / sum(agility[c] for c in stage_troop)) if stage_troop else float('inf')
        
        total_terrain_cost += segment_cost
        actual_char_time_accum += step_spent_time
        
        global_nodes_expanded += nodes_exp
        global_exec_time += exec_t
        
        accumulated_hybrid_cost = total_terrain_cost + actual_char_time_accum
        
        print(f"\n>> Segmento {origin_id} -> {dest_id}:")
        print(f"   * Terreno: {segment_cost} uni  |  Nós Varridos (A*): {nodes_exp}  |  CPU: {exec_t:.5f}s")
        print(f"   * Tempo Carga: {step_spent_time:.2f} ({', '.join(stage_troop)})")
        print(f"   [-] Acumulado Global Atual: {accumulated_hybrid_cost:.2f}")
        
        if global_path: global_path.extend(path_segment[1:])
        else: global_path.extend(path_segment)
            
        if args.speed > 0:
            visualizer.print_map(grid, path=global_path, current_pos=goal_coord)
            time.sleep(args.speed)
            
    if args.speed <= 0:
         visualizer.print_map(grid, path=global_path, current_pos=checkpoints[sorted_sequence[-1]])

    print("\n" + "/="*25 + "\\")
    print("RELATÓRIO DE TELEMETRIA FINAL".center(50))
    print("\\="*25 + "/")
    print(f"  [>] A* -> Distância (Custo Geo): {total_terrain_cost}")
    print(f"  [>] A* -> Engine Exec Time: {global_exec_time:.5f} segundos")
    print(f"  [>] A* -> RAM (Nós Expandidos): {global_nodes_expanded} state nodes")
    print(f"  [>] Tempo Escalar Drenado (Group): {actual_char_time_accum:.2f}")
    print(f"\n  [X] CUSTO TOTAL ABSOLUTO FINAL: {total_terrain_cost + actual_char_time_accum:.2f}")
    print("="*52 + "\n\n")

if __name__ == '__main__':
    main()
