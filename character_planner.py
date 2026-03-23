"""
Módulo para realizar o planejamento de alocação da equipe do Avatar 
sobre as jornadas perigosas espalhadas pelos checkpoints mapeados, balanceando agilidade local e fôlego de usos.
Inclui a geração matemática sob preceitos Gulosos e submissão estocástica de otimização vizinha (Hill Climbing).
"""

import copy
import random
import json
import os

def calculate_total_time(assignment: dict, difficulties: dict, agility: dict) -> float:
    """
    Calcula o tempo integral final que a trupe tomará para vencer as instâncias mapeadas,
    considerando a composição específica definida no dicionário de alocações.
    
    A fórmula base cobrada para cada step processado:
    Tempo Etapa local = (Dificuldade do Grid local) / Σ(Status de Agilidades do Grupo Integrante)
    
    Argumentos:
        assignment (dict): O bundle alocado na forma chave=Etapa e value=Lista de Participantes.
        difficulties (dict): Index das dificuldades para serem atravessadas.
        agility (dict): Database em memória da capacidade de atravessamento para cada char model.
        
    Retorna:
        float: O tempo virtual total da operação, em float.
    """
    total_time = 0.0
    for stage, chars in assignment.items():
        # Tranca para segurança div_by_zero ou rota esvaziada por mutação indevida
        if not chars:
            return float('inf') 
            
        stage_difficulty = difficulties.get(stage, 0)
        # Calcula a proficiência total de quem está ativamente puxando carga nessa etapa
        combined_strength = sum(agility[char] for char in chars)
        
        total_time += stage_difficulty / combined_strength
        
    return total_time


def greedy_assignment(difficulties: dict, agility: dict, max_uses: int) -> dict:
    """
    Cria a estratégia padrão "Gulosa" (Greedy Design). 
    A tática se divide em 2 fases: Primeiro tranca o mínimo requisitado (1 guia) nas partes 
    menos ofensivas com auxílio de tropas fracas, em seguida lança bombardeios maciços de times 
    ultra rápidos para extinguirem o slot nas etapas mais difíceis da grade de complexidade superior.
    
    Argumentos:
        difficulties (dict): Referências chave-valor para as metas e seus debuffs.
        agility (dict): Referências mapeando capacidade e multiplicadores (ex: Aang = 1.8).
        max_uses (int): Teto de usos totais tolerados por avatar model base (8).
        
    Retorna:
        dict: Blueprint guloso para { "nome_do_checkpoint": [ "Aang", "Appa" ] } ...
    """
    sorted_difficulties_desc = sorted(difficulties.items(), key=lambda x: x[1], reverse=True)
    sorted_difficulties_asc = sorted(difficulties.items(), key=lambda x: x[1])
    
    sorted_agility_desc = sorted(agility.items(), key=lambda x: x[1], reverse=True)
    sorted_agility_asc = sorted(agility.items(), key=lambda x: x[1])
    
    remaining_energy = {c: max_uses for c in agility.keys()}
    assignment = {stage: [] for stage, _ in difficulties.items()}
    
    # Fase Primeira: Assegurar e lacrar presenças básicas obrigatórias.
    # Assina os personagens na contra mão para poupar os grandes (Aang, Zukko) nas fáceis.
    for stage_id, ref_diff in sorted_difficulties_asc:
        for char, ref_speed in sorted_agility_asc:
            if remaining_energy[char] > 0:
                assignment[stage_id].append(char)
                remaining_energy[char] -= 1
                break # Cobertura unitária feita.
                
    # Fase Dupla: Transbordamento guloso (Overfill Greedying).
    # Com as básicas minimamente tripuladas, varre-se focado do Desastre Pior para o Desastre Menor
    # engoflando todos os "Aangs" que restaram vivos no tanking cru de stage diff.
    for stage_id, _ in sorted_difficulties_desc:
        for char, _ in sorted_agility_desc:
            # Nunca sobrecarregue 1 só agente numa mesma run
            if remaining_energy[char] > 0 and char not in assignment[stage_id]:
                assignment[stage_id].append(char)
                remaining_energy[char] -= 1
                
    return assignment


def hill_climbing_optimize(assignment: dict, difficulties: dict, agility: dict, max_uses: int, iterations: int = 15000) -> tuple:
    """
    Hill Climbing Estocástico em cima da resposta do Guloso.
    Em longas repetições iterativas, cria perturbações e remanejamentos discretos
    com a condição matemática única subversiva: "Só aceitamos se o score bater nosso melhor recorde."
    
    Argumentos:
        assignment (dict): Estrutura gulosa semente do planner base.
        iterations (int): Limite máximo de tics e sorteios que a CPU efetuará explorando os "vizinhos".
        
    Retorna:
        tuple: (Melhor Estado Alocado de Blueprint {Dict}, Seu Tempo Escalar {Float})
    """
    current_state = copy.deepcopy(assignment)
    global_record_time = calculate_total_time(current_state, difficulties, agility)
    stg_keys = list(difficulties.keys())
    
    for _ in range(iterations):
        neighbor = copy.deepcopy(current_state)
        # Sorteia quais ilhas vamos assaltar as staminas pra remanejar
        p1, p2 = random.sample(stg_keys, 2)
        
        flux_mode = random.choice(['SHIFT', 'CROSS_SWAP'])
        
        if flux_mode == 'SHIFT':
            # Remove o maluco da primeira ilha e manda inteiramente pra segunda.
            if len(neighbor[p1]) > 1: # Proteções contra vazios
                displaced_member = random.choice(neighbor[p1])
                # Lança só se não se chocar clonado na ilha alvo.
                if displaced_member not in neighbor[p2]:
                    neighbor[p1].remove(displaced_member)
                    neighbor[p2].append(displaced_member)
                    
                    test_time = calculate_total_time(neighbor, difficulties, agility)
                    if test_time < global_record_time:
                        global_record_time = test_time
                        current_state = neighbor
                        
        elif flux_mode == 'CROSS_SWAP':
            # Reverte 1 com o outro pra não ferir limites populacionais originais fixos nas pernas.
            if len(neighbor[p1]) >= 1 and len(neighbor[p2]) >= 1:
                guy_A = random.choice(neighbor[p1])
                guy_B = random.choice(neighbor[p2])
                
                # Previne overlap de identidades no caso de tentarmos dar o Momo pra quem já tá de Appa 
                # e vice versa numa troca duplicada
                if guy_A != guy_B and guy_A not in neighbor[p2] and guy_B not in neighbor[p1]:
                    neighbor[p1].remove(guy_A)
                    neighbor[p1].append(guy_B)
                    
                    neighbor[p2].remove(guy_B)
                    neighbor[p2].append(guy_A)
                    
                    test_time = calculate_total_time(neighbor, difficulties, agility)
                    if test_time < global_record_time:
                        global_record_time = test_time
                        current_state = neighbor
                        
    return current_state, global_record_time


def print_assignment(assignment: dict, difficulties: dict, agility: dict) -> None:
    """Ferramenta visual tabular para formatar os resultados do solver heurístico no terminal."""
    print(f"{'Etapa':<7} | {'Personagem/Trupe':<35} | {'Dificuldade':<12} | {'Tempo Etapa':<12} | {'Soma Acumulada'}")
    print("-" * 90)
    
    acc_time = 0.0
    # Regra de hack simples: Ordena usando a tabela alfa real para não expor fora da cronologia da história Avatar original
    alpha_mask = ["1","2","3","4","5","6","7","8","9", "B","C","D","E","G","H","I","J","K","L","N","O","P","Q","S","T","U","V","W","X","Y","Z"]
    ordered_display = sorted(assignment.keys(), key=lambda x: alpha_mask.index(x) if x in alpha_mask else 999)
    
    for idx_stage in ordered_display:
        troop = assignment.get(idx_stage, [])
        local_diff = difficulties.get(idx_stage, 0)
        
        step_spent = (local_diff / sum(agility[c] for c in troop)) if troop else float('inf')
        acc_time += step_spent
        
        # Concatenação pra visibilidade da UI de Console
        roster_str = ", ".join(troop)
        print(f"{idx_stage:<7} | {roster_str:<35} | {local_diff:<12} | {step_spent:<12.2f} | {acc_time:.2f}")
        
    print("-" * 90)
    print(f"RESUMO DOS TURNOS ESCRITURADOS: TEMPO FINAL -> {acc_time:.3f}h de jornada")


if __name__ == '__main__':
    # ---------------------------------------------------------
    # TEST DRIVE DA LÓGICA DE PROGRAMAÇÃO DA ETAPA 2 
    # Extração viva do config do próprio workspace.
    # ---------------------------------------------------------
    
    cfg_target = os.path.join(os.path.dirname(__file__), 'config.json')
    try:
        with open(cfg_target, 'r', encoding='utf-8') as fs:
            metadata = json.load(fs)
    except FileNotFoundError:
        print("[ERRO FATAL DE FS] config.json desaparecido do diretório root.")
        metadata = {"difficulty": {}, "agility": {}, "max_uses_per_character": 8}
        
    root_diffs = metadata.get("difficulty", {})
    root_agils = metadata.get("agility", {})
    root_allow = metadata.get("max_uses_per_character", 8)
    
    print("\n\n" + "="*50)
    print(" INICIO DE TESTE DE PERFOMANCE E BALANCO GULOSO".center(50))
    print("="*50)
    raw_gulosa = greedy_assignment(root_diffs, root_agils, root_allow)
    print_assignment(raw_gulosa, root_diffs, root_agils)
    
    print("\n\n" + "="*50)
    print(" APLICANDO OTIMIZACAO STOCHASTIC HILL CLIMBING".center(50))
    print("        (Processando ~15000 iterations)          ".center(50))
    print("="*50)
    climbed_assig, climbed_acc = hill_climbing_optimize(raw_gulosa, root_diffs, root_agils, root_allow, iterations=15000)
    print_assignment(climbed_assig, root_diffs, root_agils)
