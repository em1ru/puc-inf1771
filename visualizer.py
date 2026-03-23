"""
Módulo para realizar a visualização gráfica no terminal (viewport centralizada).
Permite acompanhar visualmente o deslocamento do agente sem poluir as linhas do console com a imensa matriz 82x300 completa.
"""

def print_map(grid: list[list[str]], path: list[tuple[int, int]] = None, current_pos: tuple[int, int] = None) -> None:
    """
    Exibe o mapa no terminal com uma viewport fixa de tamanho 30x80 blocos (linhas x colunas).
    O recorte de janela é dinamicamente calculado para tentar manter 'current_pos' próximo ao centro.
    
    Argumentos:
        grid (list[list[str]]): A matriz bidimensional contendo o mapa lido de um parser.
        path (list[tuple[int, int]], opcional): O histórico dos pontos já visitados, 
            os quais serão renderizados com o caractere especial '*'.
        current_pos (tuple[int, int], opcional): A posição atual a que o agente se encontra,
            esta será renderizada com destaque sob o caractere especial '@'.
    """
    if not grid:
        print("Mapa vazio. Nenhuma matriz disponível para impressão.")
        return

    # Determinamos e padronizamos a dimensão da janela no console (Viewport) requerida.
    VIEW_HEIGHT = 30
    VIEW_WIDTH = 80

    max_rows = len(grid)
    max_cols = len(grid[0]) if max_rows > 0 else 0

    # Determina qual célula será o "Ponto focal" da nossa lente de visão
    if current_pos is None:
        focus_r = max_rows // 2
        focus_c = max_cols // 2
    else:
        focus_r, focus_c = current_pos

    # Descobrimos os "starts" da view projetada subtraindo metade da altura/largura da posição central.
    start_r = max(0, focus_r - VIEW_HEIGHT // 2)
    end_r = start_r + VIEW_HEIGHT
    
    # Compensamos se a aba inferior bater no teto do array, limitando à borda exata da direita do array.
    if end_r > max_rows:
        end_r = max_rows
        start_r = max(0, end_r - VIEW_HEIGHT)

    # Analogamente para a aba horizontal
    start_c = max(0, focus_c - VIEW_WIDTH // 2)
    end_c = start_c + VIEW_WIDTH
    
    if end_c > max_cols:
        end_c = max_cols
        start_c = max(0, end_c - VIEW_WIDTH)

    # Formamos um simples set focado em busca ultra rápida com complexidade O(1) de acesso 
    path_set = set(path) if path else set()

    # Preparamos os blocos de output para que seja retornado como bloco no stdout,
    # resultando em uma atualização de frame lisa sem flickers de linhas soltas no terminal.
    output = []
    
    # Montamos as bordas gráficas customizadas limitando ao len da horizontal_border
    horizontal_border = "+" + "-" * (end_c - start_c) + "+"
    output.append(horizontal_border)

    # Roteamos individualmente pixel a pixel, de acordo com as restrições e regras visuais do Game Board
    for r in range(start_r, end_r):
        line = ["|"]  # Cerca lado esquerdo visual do frame
        for c in range(start_c, end_c):
            # Posicionamento por sobreposição visual:
            # 1. Maior Prioridade -> Renderiza '@' se for Exatamente a célula Agent
            # 2. Média Prioridade -> Renderiza '*' se já andamos por aqui (Histórico de Path)
            # 3. Menor Prioridade -> Renderiza simplesmente o Terrain Normal contido na célula da Source Grid
            if current_pos and r == current_pos[0] and c == current_pos[1]:
                line.append("@")
            elif (r, c) in path_set:
                line.append("*")
            else:
                line.append(grid[r][c])
        
        line.append("|")  # Cerca limite do lado direito estrito da borda
        output.append("".join(line))
        
    output.append(horizontal_border)

    # Imprimindo com .join faz o print rodar em uma grande chamada sys.stdout (otimizado pra terminal)
    print("\n".join(output))
