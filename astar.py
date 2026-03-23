"""
Módulo para a implementação do Algoritmo A* (A-Star).
Responsável por encontrar o menor caminho entre dois pontos no mapa
considerando os custos dos terrenos, além de traçar rotas completas 
passando por múltiplos checkpoints sequenciais.
"""

import heapq

def astar(grid: list[list[str]], start: tuple[int, int], goal: tuple[int, int], terrain_costs: dict) -> tuple[list[tuple[int, int]], int]:
    """
    Encontra o caminho de menor custo entre o ponto de partida e o destino 
    usando o algoritmo heurístico A*.
    
    Argumentos:
        grid (list[list[str]]): A matriz bidimensional do mapa.
        start (tuple[int, int]): A coordenada (linha, coluna) inicial.
        goal (tuple[int, int]): A coordenada (linha, coluna) destino.
        terrain_costs (dict): Dicionário mapeando os caracteres de terreno para o respectivo custo monetário (int).
        
    Retorna:
        tuple[list[tuple[int, int]], int]:
            - Lista de coordenadas no formato (linha, coluna) representando o caminho (incluindo o início e fim).
            - O custo total de travessia desse caminho (g(n)).
            - Caso não exista caminho factível, retorna ([], -1).
    """
    if not grid or not grid[0]:
        return [], -1
        
    max_rows = len(grid)
    max_cols = len(grid[0])
    
    # Admissibilidade da Heurística para A*: 
    # Usamos Distância de Manhattan porque o deslocamento é exclusivamente em cruz (4 direções).
    # Como o custo mínimo em qualquer terreno natural do mapa é 1 ('.'), a distância x 1
    # nunca superestima o custo real até o alvo. Isso assegura que o A* achará a rota ótima.
    def heuristic(a: tuple[int, int], b: tuple[int, int]) -> float:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
        
    def get_cost(r: int, c: int) -> int:
        char = grid[r][c]
        # Se for um marcador de terreno não nativo em terrain_costs, ele recai sendo um "Plano" com peso 1.
        return terrain_costs.get(char, terrain_costs.get('.', 1))

    # Fila de prioridades baseada em heap nativo que preserva a ordenação min-heap.
    # Armazena elementos na estrutura: (f_score, g_score, (linha, coluna))
    # Para se f_score empatar, empatará por g_score antes da verificação impossível dos tuples.
    open_set = []
    heapq.heappush(open_set, (0, 0, start))
    
    # Dicionário "came_from" mapeia nó -> pai. Essencial para retrospectiva do caminho ótimo.
    came_from = {}
    
    # g_score rastreia o custo exato percorrido até dado nó a partir da Origem.
    g_score = {start: 0}
    
    # f_score mapeia o custo rastreado + heurística predita (estimativa total).
    f_score = {start: heuristic(start, goal)}
    
    # Nós já fechados, visitados e totalmente explorados
    closed_set = set()
    
    # Vetores de movimentos admitidos: Cima, Baixo, Esquerda, Direita 
    # Diagonal não é permitida pelo problema.
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    while open_set:
        # Extrai o elemento do topo da heap com os menores custos. 
        current_f, current_g, current = heapq.heappop(open_set)
        
        # Objetivo alcançado perfeitamente com custo mínimo
        if current == goal:
            path = []
            atual = current
            # Refaz o trajeto de trás para a frente com base na genealogia armazenada
            while atual in came_from:
                path.append(atual)
                atual = came_from[atual]
            
            # Adiciona a root e inverte a lista.
            path.append(start)
            path.reverse()
            
            # O current_g atual representa a somatória total das travessias até a chegado do Alvo
            return path, current_g
            
        # Poda nós de que a heap já tem um prospecto otimizado gravado e concluído 
        if current in closed_set:
            continue
            
        closed_set.add(current)
        r, c = current
        
        # Expande o estado para as ramificações permitidas
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            
            # Limites estruturais do grid para não sair de array out-of-bounds
            if 0 <= nr < max_rows and 0 <= nc < max_cols:
                neighbor = (nr, nc)
                
                # Desabilita nós fechados com avaliações passadas e definitivas
                if neighbor in closed_set:
                    continue
                
                # Custo "real" predito da vizinhança. Transitar consome a penalidade de pisar no bloco `neighbor`.
                transition_cost = get_cost(nr, nc)
                tentative_g = g_score[current] + transition_cost
                
                # Sobrescreve o melhor caminho se achamos um novo trajeto viável ou mais leve de g(n).
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    
                    # h(n) atualizada até a reta final para f(n).
                    f = tentative_g + heuristic(neighbor, goal)
                    f_score[neighbor] = f
                    
                    # Adiciona esse braço da expansão no nosso min-heap.
                    heapq.heappush(open_set, (f, tentative_g, neighbor))
                    
    # Retorno de falha limpa da execução quando queue é defletida ao 0 e não se esbarra com o Goal
    return [], -1


def find_route(grid: list[list[str]], checkpoints: dict[str, tuple[int, int]], checkpoint_sequence: list[str], terrain_costs: dict) -> tuple[list[tuple[int, int]], int]:
    """
    Desvenda rotas continuadas e encavaladas conectando o início sequencialmente
    pelos checkpoints intermediários até a sua glória final no último checkpoint.
    
    Argumentos:
        grid (list[list[str]]): A matriz do mapa.
        checkpoints (dict): Mapeamento dos checkponits identificados (resultado do parser).
        checkpoint_sequence (list[str]): O array dos targets sequenciados: ex. ["0", "1", "2"].
        terrain_costs (dict): Parametrizações locais do cenário de cada bloco e suas precificações.
        
    Retorna:
        tuple[list[tuple[int, int]], int]:
            - O Array linear completo do ponto inicial '0' até o clímax da string da sequência.
            - O custo consolidado acumulado destas rotas concatenadas.
    """
    total_path = []
    total_cost = 0
    
    if len(checkpoint_sequence) < 2:
        if len(checkpoint_sequence) == 1:
            start_chr = checkpoint_sequence[0]
            if start_chr in checkpoints:
                return [checkpoints[start_chr]], 0
        return [], -1
        
    for i in range(len(checkpoint_sequence) - 1):
        start_char = checkpoint_sequence[i]
        goal_char = checkpoint_sequence[i+1]
        
        # Verificação rigorosa pra não puxar chaves não detectadas durante a verredura do grid.
        if start_char not in checkpoints or goal_char not in checkpoints:
            print(f"Erro: Tentando transição em um Nó Desconhecido ou Faltante no Mapa: '{start_char}' -> '{goal_char}'.")
            return [], -1
            
        start_pos = checkpoints[start_char]
        goal_pos = checkpoints[goal_char]
        
        # Engatilha a busca unificada A* na sub-janela segmentada.
        segment_path, segment_cost = astar(grid, start_pos, goal_pos, terrain_costs)
        
        if segment_cost == -1 or not segment_path:
            print(f"Rota Bloqueada e/ou Inalcançável: Entre o marcador {start_char} e {goal_char}.")
            return [], -1
            
        # Adiciona à rota global.
        # Caso a varredura global já possua elementos das paradas passadas, dropamos o range[0],
        # a primeira coordenada, para ela não acumular e duplicar nó parado durante as transições de parágrafo.
        # Ex: Rota 1 termina em B. Rota 2 se inicia em B; sem slice, rota global exibiria: ..., B, B, ...
        if total_path:
            total_path.extend(segment_path[1:])
        else:
            total_path.extend(segment_path)
            
        total_cost += segment_cost

    return total_path, total_cost


if __name__ == '__main__':
    # =========================================================================
    # BATERIA DE TESTES SINTÉTICOS UNITÁRIOS 
    # Rodamos no próprio módulo um grid imaginário condensado apenas para aferir.
    # =========================================================================
    
    test_grid = [
        ["S", ".", ".", "A", "M", ".", ".", ".", ".", "."],
        [".", "M", ".", "A", "M", ".", "R", "R", ".", "."],
        [".", "M", ".", ".", ".", ".", "V", "R", ".", "."],
        [".", "M", "M", "M", ".", ".", "V", ".", ".", "."],
        [".", ".", ".", "M", ".", "A", "A", ".", "M", "."],
        [".", "V", ".", "M", ".", "A", "M", ".", "M", "."],
        [".", "V", ".", ".", ".", ".", "M", ".", "M", "."],
        [".", "M", "M", "M", "M", "M", "M", ".", "M", "."],
        [".", ".", ".", ".", ".", ".", ".", ".", "M", "."],
        ["A", "A", "A", "A", "A", "M", "M", ".", ".", "E"]
    ]
    
    test_terrain_costs = {
        ".": 1,
        "R": 5,
        "V": 10,
        "A": 15,
        "M": 200,
        "S": 1, # Start Dummy Checkpoint Cost
        "E": 1  # Goal Dummy Checkpoint Cost
    }
    
    # Marcador de Início do agente no Teste
    test_start = (0, 0)
    # Marcador de Objetivo no Canto Inferior Direito
    test_goal = (9, 9)
    
    print("Iniciando varredura com algoritmo A* ...")
    path, cost = astar(test_grid, test_start, test_goal, test_terrain_costs)
    
    if cost != -1:
        print(f"-> Custo total do trajeto encontrado: {cost}")
        print(f"-> Qtd nós percorridos: {len(path)}")
        
        print("\n=== MAPA TESTE SOLUCIONADO ===")
        path_set = set(path)
        
        # Demonstração em Terminal Cru pra mostrar e debugar o A* nativo desvinculado
        for ri in range(len(test_grid)):
            row_str = ""
            for ci in range(len(test_grid[0])):
                # Cor do texto de highlight
                if (ri, ci) == test_start:
                    row_str += "S "
                elif (ri, ci) == test_goal:
                    row_str += "E "
                elif (ri, ci) in path_set:
                    row_str += "* " # Sinaliza a rota com *
                else:
                    row_str += test_grid[ri][ci] + " "
            print(row_str)
            
        # Simula as chamadas em Sequência via check_route caso S -> Pivo -> E
        test_checkpoints = {'0': (0,0), '1': (5,1), '2': (9,9)}
        test_seq = ['0', '1', '2']
        _, total_seq_cost = find_route(test_grid, test_checkpoints, test_seq, test_terrain_costs)
        print(f"\n=> Teste find_route Sequencial ['0' -> '1' -> '2']: Custo Resultante = {total_seq_cost}")
        
    else:
        print("Caminho não pode ser encontrado no Test Case.")
