# Avatar - Pathfinding, Telemetria Avançada e Planejamentos Estratégicos

Repositório que hospeda a resolução para a disciplina de Inteligência Artificial baseada nas missões da série "A Lenda de Aang". Realizado com A* Tracking, Combinatórias Exaustivas, Hill Climbing e Interfaces Interativas em Tkinter e ANSI.

## Arquitetura de Módulos (Nível 4)

*   `config.json`: Database parametrizável central (Agilidades, Checkpoints e Terrenos).
*   `map_parser.py`: Engine de decodificação espacial lendo grids 82x300.
*   `astar.py`: Solver A* alimentado Pela Distância de Manhattan, reportando métricas minuciosas de Hardware (Segundos, e Stack Overflow Nodes).
*   `character_planner.py`: Otimizador Multi-layer lidando com preenchimento Guloso, Local Search (Hill Climbing) ou Força Bruta Completa para steps <= 5.
*   `visualizer.py`: Renderizador `ANSI` de terminal de altíssimo contraste baseando em dicionários escape coloridos.
*   `tests.py`: Validador Unitário da API blindando asserts crueis e verificando comportamentos de vazamento de Stamina nos personagens.
*   `gui.py`: Uma aplicação Executável Gráfica baseada no package padrão `tkinter`.
*   `main.py`: Linha de comando mestre CLI para a bancada do Orquestrador.

## Modos de Operação (Como Rodar)

### Modo Linha de Comando Clássico (Terminal Animado)
Processamento escalado para ser acompanhado a cru no Shell:
```bash
python main.py --map MAPA_LENDA-AANG.txt --config config.json --speed 0.05
```

### Modo Interface Gráfica (Desktop Bônus)
Gerações matemáticas convertidas organicamente em renderizações 2D via Canvas:
```bash
python gui.py
```
*(Seu ambiente OS abrirá uma ViewPort amigável `900x650` contendo painéis, file choosers, e botões dinâmicos de submissão do tracking.)*

### Modo Diagnósticos (Unitary Asserts)
Valide a conformidade da suite das engrenagens lógicas, caso modifique trechos críticos do Pathfinding no código-fonte principal:
```bash
python tests.py
```
