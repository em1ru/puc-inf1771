# Avatar - Pathfinding e Planejamento Heurístico (Trabalho 1 de IA)

Este repositório encapsula o sistema solicitado para a disciplina de Inteligência Artificial da PUC-Rio lidando com A* e Busca Estocástica Local (Hill Climbing).

## Estrutura do Projeto

*   `config.json`: Database parametrizável central abrigando as conversões e os custos (agilidades, custos de terrenos, e pontuações alfanuméricas das etapas).
*   `map_parser.py`: Engine decodificadora da topologia do mapa, que levanta as matrizes bidimensionais do arquivo `.txt`.
*   `astar.py`: Solver da grade A* alimentado pela Heurística de Distância de Manhattan.
*   `character_planner.py`: Planejador Estratégico baseando-se num Greedy Approach e polindo até 15.000 iterações em random-walk (*Hill Climbing*).
*   `visualizer.py`: Renderizador em `30x80` ASCII puro focado.
*   `main.py`: O orquestrador central de tudo.

## Como Executar

A execução é simplificada diretamente usando console via interpretador Python padrão.

```bash
# Execução Padrão:
python main.py --map mapa.txt --config config.json --speed 0.05
```

### Argumentos CLI (`main.py`)

*   `--map <path>`: O caminho exato para a sua matriz, ex: `MAPA_LENDA-AANG.txt`. Caso o arquivo local não seja achado, o `main.py` gerará em memória uma savana vazia gigante para impedir a crash na demonstração matemática.
*   `--config <path>`: Apontador explícito para a configuração.
*   `--speed <float>`: Tempo de animação em Delay Visual no terminal. Para pular instantaneamente ao relatório numérico da resposta, rode com `--speed 0`.
