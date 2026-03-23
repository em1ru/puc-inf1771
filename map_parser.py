"""
Módulo para realizar o parsing do mapa no trabalho de Inteligência Artificial sobre o Avatar.
Responsável por carregar a grade do mapa, recuperar custos dos terrenos e identificar os checkpoints.
"""

import json
import os

def _load_config() -> dict:
    """Carrega o arquivo de configuração para obter os custos configuráveis."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback de segurança se o config não for encontrado
        return {}

# Cache local da configuração
_CONFIG = _load_config()

def load_map(file_path: str) -> list[list[str]]:
    """
    Lê o arquivo de texto contendo o mapa.
    
    Argumentos:
        file_path (str): O caminho para o arquivo do mapa.
        
    Retorna:
        list[list[str]]: A matriz do mapa como lista de listas de caracteres.
    """
    grid = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            # Mantem os espaços intactos pois podem representar área vazia do lado direito (uso de rstrip customizado)
            # Remove apenas as quebras de linha '\n' e '\r'
            clean_line = line.rstrip("\n\r")
            if clean_line:
                grid.append(list(clean_line))
    return grid

def get_terrain_cost(char: str) -> int:
    """
    Retorna o custo associado ao tipo de terreno com base no config.json.
    Checkpoints que não possuem custo definido assumem o custo do '.'.
    
    Argumentos:
        char (str): O caractere respectivo do terreno do mapa.
        
    Retorna:
        int: O custo de locomoção atrelado àquele terreno.
    """
    terrains = _CONFIG.get("terrain_costs", {})
    # Se para este caractere existir custo registrado, retorne-o.
    if char in terrains:
        return terrains[char]
    
    # Checkpoints são caminhos válidos sem um terreno estritamente amarrado na especificação original.
    # Assumimos o custo base de terreno "Plano" (.) para o checkpoint.
    return terrains.get(".", 1)

def find_checkpoints(grid: list[list[str]]) -> dict[str, tuple[int, int]]:
    """
    Identifica as coordenadas dos checkpoints presentes no mapa interativamente.
    
    Os checkpoints válidos são os números '0' ao '9', e as letras 'B' ao 'Z',
    puladas as letras F, M, R pois essas conflitam com terrenos previstos na atividade.
    Como pode haver conflitos (ex. um caractere no JSON do checkpoint também ser mapeado como terreno),
    um caractere é aceito como checkpoint de prioridade caso apareça apenas 1 vez (é unico) 
    ou caso não faça parte dos terrains cost nativamente mapeados.
    
    Argumentos:
        grid (list[list[str]]): A matriz do mapa como array 2D.
        
    Retorna:
        dict[str, tuple[int, int]]: Dicionário chave=char (ex: '0', 'B'), valor=(linha, coluna).
    """
    checkpoints = {}
    
    # Criamos o conjunto de checkpoints válidos seguindo a regra da tabela de dificuldade + checkpoint '0' (início)
    valid_keys = set(str(i) for i in range(10)) # 0 até 9
    for ch in "BCDEGHIJKLNOPQSTUVWXYZ":
        valid_keys.add(ch)

    # Contagem de caracteres no mapa para evitar sobrescrever a coordenada de um checkpoint
    # em casos onde regras de terrain_cost e dificuldades conflitam usando a mesma letra,
    # sabendo que terrenos formariam extensos conjuntos e checkpoints costumam ocorrer isoladamente.
    char_counts = {}
    for r, row in enumerate(grid):
        for c, char in enumerate(row):
            char_counts[char] = char_counts.get(char, 0) + 1

    for r, row in enumerate(grid):
        for c, char in enumerate(row):
            # Valida se está dentre as chaves da tabela de regras dos checkpoints
            if char in valid_keys:
                
                # Para evitar conflitar terrenos regulares que acabaram herdando alguma letra da config de checkpoints,
                # garantimos que se é checkpoint real, apareceu apenas 1 vez, ou se for algo como '0', é apenas checkpoint de fato.
                # Do contrário, a prioridade será registrar apenas como checkpoint as unidades sem custo mapeado no terreno.
                if char_counts[char] == 1 or char not in _CONFIG.get("terrain_costs", {}):
                    checkpoints[char] = (r, c)
                    
    return checkpoints

def is_walkable(char: str) -> bool:
    """
    Verifica se a célula onde o agente deseja ir é transitável ou um obstáculo sólido intransponível.
    No universo do mapa apresentado para este problema de busca específico, todos os ambientes 
    (planícies, água, florestas e montanhas) são de fato caminháveis, apenas alterando-se os custos em config.json.
    
    Argumentos:
        char (str): O caractere do terreno a ser validado.
        
    Retorna:
        bool: Retorna sempre True, indicando que nenhuma barreira infinita (como paredes imutáveis) existe.
    """
    return True
