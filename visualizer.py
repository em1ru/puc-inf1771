"""
Módulo para realizar a visualização gráfica no terminal usando códigos ANSI.
"""

# Tabela de dicionário ANSI para as cores dos blocos no console
ANSI_COLORS = {
    ".": "\030[37m",       # Branco (Plano)
    "R": "\033[90m",       # Cinza (Rochoso)
    "V": "\033[32m",       # Verde (Floresta)
    "A": "\033[34m",       # Azul (Água)
    "M": "\033[33m",       # Amarelo escuro (Montanha)
    "*": "\033[96m",       # Ciano Brilhante (Caminho percorrido)
    "@": "\033[91m\033[1m" # Vermelho em Negrito (Posição atual do Agente)
}
ANSI_RESET = "\033[0m"
ANSI_MAGENTA = "\033[95m\033[1m" # Magenta para Checkpoints numéricos ou letrados

def print_map(grid: list[list[str]], path: list[tuple[int, int]] = None, current_pos: tuple[int, int] = None) -> None:
    if not grid:
        return

    VIEW_HEIGHT, VIEW_WIDTH = 30, 80
    max_rows, max_cols = len(grid), len(grid[0]) if grid else 0

    if current_pos is None:
        focus_r, focus_c = max_rows // 2, max_cols // 2
    else:
        focus_r, focus_c = current_pos

    start_r = max(0, focus_r - VIEW_HEIGHT // 2)
    end_r = min(max_rows, start_r + VIEW_HEIGHT)
    if end_r - start_r < VIEW_HEIGHT: start_r = max(0, end_r - VIEW_HEIGHT)

    start_c = max(0, focus_c - VIEW_WIDTH // 2)
    end_c = min(max_cols, start_c + VIEW_WIDTH)
    if end_c - start_c < VIEW_WIDTH: start_c = max(0, end_c - VIEW_WIDTH)

    path_set = set(path) if path else set()
    output = []
    
    horizontal_border = "+" + "-" * (end_c - start_c) + "+"
    output.append(horizontal_border)

    for r in range(start_r, end_r):
        line = ["|"] 
        for c in range(start_c, end_c):
            char = grid[r][c]
            
            # Prioridade de render
            # 1. Agente
            if current_pos and r == current_pos[0] and c == current_pos[1]:
                visual_char = "@"
                color = ANSI_COLORS["@"]
            # 2. Rota
            elif (r, c) in path_set:
                visual_char = "*"
                color = ANSI_COLORS["*"]
            # 3. Checkpoints (números ou letras exclusivas q não são o terreno nativo)
            elif str.isalnum(char) and char not in [".", "R", "V", "A", "M"]:
                visual_char = char
                color = ANSI_MAGENTA
            # 4. Terreno
            else:
                visual_char = char
                color = ANSI_COLORS.get(char, "\033[37m")
                
            line.append(f"{color}{visual_char}{ANSI_RESET}")
        
        line.append("|")
        output.append("".join(line))
        
    output.append(horizontal_border)
    print("\n".join(output))
