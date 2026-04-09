# Avatar: A Lenda de Aang — Busca Heurística A* e Busca Local

Agente inteligente que guia o grupo do Avatar por um mapa de 82×300 células, resolvendo dois problemas de otimização distintos: encontrar o caminho de menor custo entre 32 checkpoints e alocar os 7 personagens nas 31 etapas da jornada de forma a minimizar o tempo total.

O pathfinding usa o algoritmo **A\*** com heurística de Manhattan e custos de terreno variáveis. A alocação de personagens usa **Simulated Annealing**, que parte de uma solução gulosa proporcional e explora a vizinhança por trocas, adições, remoções e redistribuições de personagens entre etapas, aceitando pioras temporárias para escapar de mínimos locais.

A visualização em **pygame** renderiza o mapa inteiro em tempo real, com o agente se movendo célula a célula pelo caminho calculado e um painel lateral exibindo o estado atual da jornada.

---

## Requisitos

- Python 3.10+
- pygame (`pip install pygame`)

---

## Como executar

```bash
# Com visualização pygame (padrão)
python main.py

# Apenas cálculo, saída no console
python main.py --no-viz

# Usar solução gulosa em vez de SA
python main.py --method greedy

# Mais iterações do Simulated Annealing
python main.py --sa-iter 1000000

# Caminho alternativo para o mapa
python main.py --map caminho/para/mapa.txt

# Velocidade inicial da animação (células por frame)
python main.py --speed 5
```

**Controles da visualização:**

| Tecla | Ação |
|---|---|
| `ENTER` / `ESPAÇO` | Iniciar / pausar |
| `↑` / `↓` | Aumentar / diminuir velocidade |
| `R` | Reiniciar |
| `Q` / `ESC` | Sair |

---

## Estrutura do projeto

```
avatar_astar/
├── main.py                  # Ponto de entrada: orquestra todos os módulos
├── config.py                # Constantes editáveis: terrenos, personagens, etapas
├── map_loader.py            # Leitura e validação do mapa .txt
├── astar.py                 # Algoritmo A* e cálculo de todos os segmentos
├── character_optimizer.py   # Greedy proporcional + Simulated Annealing
├── visualizer.py            # Visualização pygame com cell_size dinâmico
├── data/
│   └── mapa.txt             # Mapa 82×300 (terreno + checkpoints)
└── README.md
```

---

## Algoritmos

### A* (astar.py)

- **Heurística:** distância de Manhattan — admissível porque o menor custo de terreno é 1 e não há movimentos diagonais.
- **Custo g(n):** soma dos custos de terreno das células percorridas.
- **Estruturas:** `heapq` como open list com tie-breaking por contador de inserção; `dict` esparso para `g_scores` (evita inicializar 24.600 entradas com ∞); `set` como closed list.
- **`compute_all_paths`:** executa o A* nos 31 pares consecutivos de checkpoints (0→1→…→Z) e retorna todos os segmentos.

### Simulated Annealing (character_optimizer.py)

- **Estado:** `dict {etapa_id: frozenset de personagens}`.
- **Vizinhança (4 movimentos):**
  - `swap` — troca um personagem exclusivo entre duas etapas
  - `add` — adiciona um personagem com usos disponíveis a uma etapa
  - `remove` — remove um personagem de uma etapa com ≥ 2 participantes
  - `redistribute` — move um personagem de uma etapa grande para uma pequena
- **Restrições:** cada personagem tem `max_uses = 8`; cada etapa precisa de ao menos 1 personagem. Todos os movimentos preservam essas restrições.
- **Resfriamento geométrico:** `T ← T × α` a cada iteração, com `T_start = 80`, `α = 0.99995`, `T_end = 0.01`, `max_iter = 500.000`.
- **Solução inicial:** greedy proporcional — distribui os 56 usos totais às etapas proporcionalmente à dificuldade, usando o Método do Maior Resto para arredondar sem perder usos, com recálculo por lookahead a cada etapa.

---

## Configuração (config.py)

Todos os parâmetros do projeto estão centralizados em `config.py`:

```python
# Custos de terreno
TERRAIN_COSTS = {
    ".": 1,    # Plano
    "R": 5,    # Rochoso
    "F": 10,   # Floresta
    "A": 15,   # Água
    "M": 200,  # Montanhoso
}

# Personagens: nome → agilidade, max_uses
CHARACTERS = {
    "Aang":   {"agility": 1.8, "max_uses": 8},
    "Zuko":   {"agility": 1.6, "max_uses": 8},
    # ...
}
```

As 32 etapas são geradas automaticamente em `STAGES`: etapa 0 sem dificuldade (início), etapas 1–31 com dificuldades 10, 20, …, 310.

O tempo de cada etapa é calculado como:

```
tempo = dificuldade / soma(agilidades dos personagens escolhidos)
```

---

## Resultados

Executado com Simulated Annealing (500.000 iterações, seed=42) no mapa padrão:

| Métrica | Valor |
|---|---|
| Custo total do caminho (A\*) | 2.798 |
| Tempo total das etapas (SA) | ≈ 1.807 |
| **Custo total** | **≈ 4.605** |
| Segmentos calculados | 31 |
| Células no caminho | 1.512 |
| Tempo de execução A\* | < 0,15 s |
| Tempo de execução SA | ≈ 6–8 s |

---

## Autores

Gabriel Emile - 2224098
