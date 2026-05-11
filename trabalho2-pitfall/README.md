# INF1771 - Trabalho 2: Agente Lógico - Pitfall!

Implementação do agente Pitfall Harry usando **SWI-Prolog + Python**, baseada no exemplo do Mundo do Wumpus.

## Autores

Gabriel Emile - 2224098  
Lis Almeida - 2421294  
Rafaela Bessa - 2420043

## Vídeo de Apresentação

[Link do vídeo](#) <!-- substituir pelo link após gravar -->

## Dependências

- [SWI-Prolog 8.4.3](https://www.swi-prolog.org/download/stable/bin/swipl-8.4.3-1.x64.exe.envelope)
- Python 3.11+
- `pip install pygame pyswip`

## Como executar

```bash
cd trabalho2-pitfall
py -3.11 gmap.py
```

Pressione `M` durante o jogo para alternar entre mapa real e mapa de conhecimento do agente.

## Descrição

O agente explora um labirinto 12×12 gerado **aleatoriamente** a cada execução, com:
- 2 inimigos de dano 50 (`D`)
- 2 inimigos de dano 20 (`d`)
- 4 teleporters/morcegos (`T`)
- 8 poços (`P`)
- 3 pedras de ouro (`O`)
- 3 powerups de energia (`U`)

### Sensores

| Sensor | Gatilho |
|--------|---------|
| `brisa` | células adjacentes a poços |
| `flash` | células adjacentes a teleporters |
| `passos` | células adjacentes a inimigos |
| `brilho` | célula com ouro |
| `reflexo` | célula com powerup |

### Lógica do Agente (Prolog)

O predicado `executa_acao/1` decide a ação atual:
1. **Pegar** — se há ouro ou powerup na posição atual
2. **Explorar** — delega ao Python via `escolhe_objetivo/2`

O predicado `escolhe_objetivo/2` escolhe o próximo alvo:
1. Célula segura inferida e ainda não visitada
2. Retornar ao início se energia < 30
3. Retornar ao início se exploração esgotada
4. Arriscar célula adjacente desconhecida (não confirmadamente perigosa)

### Pathfinding (Python)

A* com heurística Manhattan, respeitando células confirmadamente seguras. Em caso de falha, relaxa a restrição para qualquer célula não confirmadamente perigosa.
