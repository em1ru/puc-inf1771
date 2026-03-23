"""
Planejamento de equipe (Greedy, Hill Climbing, Exhaustive Força Bruta).
"""
import copy
import random
import itertools

def calculate_total_time(assignment: dict, difficulties: dict, agility: dict) -> float:
    time = 0.0
    for stage, chars in assignment.items():
        if not chars: return float('inf')
        time += difficulties.get(stage, 0) / sum(agility[c] for c in chars)
    return time

def greedy_assignment(difficulties: dict, agility: dict, max_uses: int) -> dict:
    sorted_diffs_desc = sorted(difficulties.items(), key=lambda x: x[1], reverse=True)
    sorted_diffs_asc = sorted(difficulties.items(), key=lambda x: x[1])
    sorted_agil_desc = sorted(agility.items(), key=lambda x: x[1], reverse=True)
    sorted_agil_asc = sorted(agility.items(), key=lambda x: x[1])
    
    uses = {c: max_uses for c in agility}
    assign = {s: [] for s in difficulties}
    
    for stage, _ in sorted_diffs_asc:
        for c, _ in sorted_agil_asc:
            if uses[c] > 0:
                assign[stage].append(c); uses[c] -= 1
                break
                
    for stage, _ in sorted_diffs_desc:
        for c, _ in sorted_agil_desc:
            if uses[c] > 0 and c not in assign[stage]:
                assign[stage].append(c); uses[c] -= 1
                
    return assign

def hill_climbing_optimize(assignment: dict, difficulties: dict, agility: dict, max_uses: int, iterations: int = 15000) -> tuple:
    curr_state = copy.deepcopy(assignment)
    best_time = calculate_total_time(curr_state, difficulties, agility)
    keys = list(difficulties.keys())
    
    for _ in range(iterations):
        nxt = copy.deepcopy(curr_state)
        p1, p2 = random.sample(keys, 2)
        if random.choice([True, False]):
            if len(nxt[p1]) > 1:
                mem = random.choice(nxt[p1])
                if mem not in nxt[p2]:
                    nxt[p1].remove(mem); nxt[p2].append(mem)
                    t = calculate_total_time(nxt, difficulties, agility)
                    if t < best_time: best_time, curr_state = t, nxt
        else:
            if len(nxt[p1]) >= 1 and len(nxt[p2]) >= 1:
                A, B = random.choice(nxt[p1]), random.choice(nxt[p2])
                if A != B and A not in nxt[p2] and B not in nxt[p1]:
                    nxt[p1].remove(A); nxt[p1].append(B)
                    nxt[p2].remove(B); nxt[p2].append(A)
                    t = calculate_total_time(nxt, difficulties, agility)
                    if t < best_time: best_time, curr_state = t, nxt
    return curr_state, best_time

def exhaustive_small(difficulties: dict, agility: dict, max_uses: int):
    """Para grupos de até 5 etapas testa todas combinações e retorna a ótima."""
    if len(difficulties) > 5:
        print("[!] Abortando Busca Exaustiva. Numero de etapas maior que 5 levaria à sobrecarga de CPU (O(N!)).")
        return None, float('inf')
        
    chars = list(agility.keys())
    subsets_validos = []
    
    # Gera combinações de 1 a 7 agentes dentro de uma etapa
    for r in range(1, len(chars) + 1):
        for combo in itertools.combinations(chars, r):
            subsets_validos.append(list(combo))
            
    best_time = float('inf')
    best_assign = None
    stages = list(difficulties.keys())
    
    # Backtracking DFS para arvore de 127^5 com branch and bound de teto de stamina
    def solve(layer, local_uses, current_assign, current_timer):
        nonlocal best_time, best_assign
        
        # Poda: se caminho atual isolado já é mais sofrido que o best global, para
        if current_timer >= best_time: return
            
        # Otimização final quando alcança fundo
        if layer == len(stages):
            if current_timer < best_time:
                best_time = current_timer
                best_assign = copy.deepcopy(current_assign)
            return
            
        stage_id = stages[layer]
        diff = difficulties[stage_id]
        
        for ans in subsets_validos:
            valid = True
            for c in ans:
                if local_uses[c] + 1 > max_uses:
                    valid = False; break
            
            if valid:
                 # Avança arvore
                 for c in ans: local_uses[c] += 1
                 time_cost = diff / sum(agility[c] for c in ans)
                 current_assign[stage_id] = ans
                 
                 solve(layer + 1, local_uses, current_assign, current_timer + time_cost)
                 
                 # Recua arvore (backtrack cleanup)
                 for c in ans: local_uses[c] -= 1
                 
    # Inicia root call
    solve(0, {c: 0 for c in chars}, {}, 0.0)
    return best_assign, best_time

def print_assignment(assignment: dict, difficulties: dict, agility: dict) -> None:
    print(f"{'Etapa':<7} | {'Personagem/Trupe':<35} | {'Dificuldade':<12} | {'Tempo Etapa':<12} | {'Soma Acumulada'}")
    acc = 0.0
    am_ref = "0123456789BCDEGHIJKLNOPQSTUVWXYZ"
    
    for s in sorted(assignment.keys(), key=lambda x: am_ref.index(x) if x in am_ref else 999):
        c = assignment.get(s, [])
        v = (difficulties.get(s, 0) / sum(agility[x] for x in c)) if c else float('inf')
        acc += v
        print(f"{s:<7} | {', '.join(c):<35} | {difficulties.get(s,0):<12} | {v:<12.2f} | {acc:.2f}")
    print(f"RESUMO DOS TURNOS: TEMPO FINAL -> {acc:.3f}h de jornada")
