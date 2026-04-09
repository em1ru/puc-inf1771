# =============================================================================
# config.py — Configurações centrais do projeto Avatar A*
# Edite este arquivo para ajustar custos, personagens e etapas.
# =============================================================================

# ---------------------------------------------------------------------------
# Custos de terreno
# Cada caractere do mapa mapeia para um custo de travessia.
# Nota: 'F' = Floresta no arquivo de mapa (não 'V', que é o símbolo do checkpoint da Etapa 27).
# ---------------------------------------------------------------------------
TERRAIN_COSTS: dict[str, int] = {
    ".": 1,    # Plano
    "R": 5,    # Rochoso
    "F": 10,   # Floresta
    "A": 15,   # Água
    "M": 200,  # Montanhoso
}

# ---------------------------------------------------------------------------
# Personagens
# Cada personagem tem:
#   "agility"   — divisor de custo de terreno (quanto maior, mais rápido)
#   "max_uses"  — quantas etapas o personagem pode participar no total
# ---------------------------------------------------------------------------
CHARACTERS: dict[str, dict] = {
    "Aang":   {"agility": 1.8, "max_uses": 8},
    "Zuko":   {"agility": 1.6, "max_uses": 8},
    "Toph":   {"agility": 1.6, "max_uses": 8},
    "Katara": {"agility": 1.6, "max_uses": 8},
    "Sokka":  {"agility": 1.4, "max_uses": 8},
    "Appa":   {"agility": 0.9, "max_uses": 8},
    "Momo":   {"agility": 0.7, "max_uses": 8},
}

# ---------------------------------------------------------------------------
# Símbolos dos checkpoints no mapa (na ordem de etapa 0 → 31)
# A → água (terreno), F → floresta (terreno), M → montanha (terreno),
# R → rochoso (terreno): por isso são pulados na sequência de checkpoints.
# ---------------------------------------------------------------------------
CHECKPOINT_SYMBOLS: list[str] = [
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",  # etapas 0–9
    "B", "C", "D", "E",                                  # etapas 10–13
    "G", "H", "I", "J", "K", "L",                        # etapas 14–19
    "N", "O", "P", "Q",                                  # etapas 20–23
    "S", "T", "U", "V", "W", "X", "Y", "Z",             # etapas 24–31
]

# Conjunto para busca O(1) durante a leitura do mapa
CHECKPOINT_SET: frozenset[str] = frozenset(CHECKPOINT_SYMBOLS)

# ---------------------------------------------------------------------------
# Etapas
# Cada etapa representa o trecho entre dois checkpoints consecutivos.
#   "id"         — índice 0-based (0 = início, 31 = fim)
#   "symbol"     — caractere do checkpoint de destino no mapa
#   "difficulty" — custo base da etapa (None para início e fim)
#
# Fórmula do tempo de uma etapa:
#   tempo = difficulty / sum(agility de cada personagem escolhido)
#
# Dificuldades: 10, 20, ..., 310 para as etapas 1–31 (incrementos de 10).
# Etapa 0 é ponto de partida sem dificuldade; etapa 31 (Z) tem dificuldade 310.
# ---------------------------------------------------------------------------
def _build_stages() -> list[dict]:
    stages = []
    difficulties = [None] + list(range(10, 320, 10))  # 32 valores: None + 31 difs
    for i, symbol in enumerate(CHECKPOINT_SYMBOLS):
        stages.append({
            "id": i,
            "symbol": symbol,
            "difficulty": difficulties[i],
        })
    return stages


STAGES: list[dict] = _build_stages()

# ---------------------------------------------------------------------------
# Dimensões esperadas do mapa (para validação)
# ---------------------------------------------------------------------------
MAP_ROWS: int = 82
MAP_COLS: int = 300
