"""
Módulo para a implementação do Algoritmo A* (A-Star).
Responsável por encontrar o menor caminho considerando custos, e métricas de desempenho.
"""

import heapq
import time

def astar(grid: list[list[str]], start: tuple[int, int], goal: tuple[int, int], terrain_costs: dict) -> tuple[list[tuple[int, int]], int, int, float]:
    """
    Algoritmo heurístico A* otimizado com telemetria.
    
    Retorna:
        tuple: (caminho, custo_total, nos_expandidos, tempo_segundos)
    """
    start_time = time.perf_counter()
    nodes_expanded = 0
    
    if not grid or not grid[0]:
        return [], -1, nodes_expanded, time.perf_counter() - start_time
        
    max_rows, max_cols = len(grid), len(grid[0])
    
    def heuristic(a: tuple[int, int], b: tuple[int, int]) -> float:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
        
    def get_cost(r: int, c: int) -> int:
        char = grid[r][c]
        return terrain_costs.get(char, terrain_costs.get('.', 1))

    open_set = []
    heapq.heappush(open_set, (0, 0, start))
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}
    closed_set = set()
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    while open_set:
        _, current_g, current = heapq.heappop(open_set)
        nodes_expanded += 1
        
        if current == goal:
            path = []
            atual = current
            while atual in came_from:
                path.append(atual)
                atual = came_from[atual]
            path.append(start)
            path.reverse()
            return path, current_g, nodes_expanded, time.perf_counter() - start_time
            
        if current in closed_set:
            continue
            
        closed_set.add(current)
        r, c = current
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < max_rows and 0 <= nc < max_cols:
                neighbor = (nr, nc)
                if neighbor in closed_set:
                    continue
                
                tentative_g = g_score[current] + get_cost(nr, nc)
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + heuristic(neighbor, goal)
                    f_score[neighbor] = f
                    heapq.heappush(open_set, (f, tentative_g, neighbor))
                    
    return [], -1, nodes_expanded, time.perf_counter() - start_time


def find_route(grid: list[list[str]], checkpoints: dict[str, tuple[int, int]], checkpoint_sequence: list[str], terrain_costs: dict) -> tuple[list[tuple[int, int]], int, int, float]:
    total_path = []
    total_cost = 0
    total_nodes = 0
    total_time = 0.0
    
    if len(checkpoint_sequence) < 2:
        if len(checkpoint_sequence) == 1 and checkpoint_sequence[0] in checkpoints:
            return [checkpoints[checkpoint_sequence[0]]], 0, 0, 0.0
        return [], -1, 0, 0.0
        
    for i in range(len(checkpoint_sequence) - 1):
        s_char, g_char = checkpoint_sequence[i], checkpoint_sequence[i+1]
        
        if s_char not in checkpoints or g_char not in checkpoints:
            return [], -1, total_nodes, total_time
            
        spath, scost, snodes, stime = astar(grid, checkpoints[s_char], checkpoints[g_char], terrain_costs)
        
        if scost == -1 or not spath:
            return [], -1, total_nodes, total_time
            
        if total_path:
            total_path.extend(spath[1:])
        else:
            total_path.extend(spath)
            
        total_cost += scost
        total_nodes += snodes
        total_time += stime

    return total_path, total_cost, total_nodes, total_time

if __name__ == '__main__':
    test_grid = [
        ["S", ".", ".", "A", "M"],
        [".", "M", ".", "A", "M"],
        [".", "M", "M", ".", "E"]
    ]
    test_tc = {".": 1, "A": 15, "M": 200, "S": 1, "E": 1}
    p, c, n, t = astar(test_grid, (0,0), (2,4), test_tc)
    print(f"Custo={c}, Nós={n}, Segundos={t:.5f}")
