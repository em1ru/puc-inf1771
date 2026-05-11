import pygame
import sys, time, random, heapq
from pyswip import Prolog, Functor, Variable, Query

import pathlib
current_path = str(pathlib.Path().resolve())

elapsed_time = 0
auto_play_tempo = 0.5
auto_play = True
show_map = False

scale = 60
size_x = 12
size_y = 12
width  = size_x * scale
height = size_y * scale

player_pos = (1, 1, 'norte')
energia    = 0
pontuacao  = 0

mapa = [[''] * size_x for _ in range(size_y)]

visitados = []
certezas  = []

pl_file = (current_path + '\\main.pl').replace('\\', '/')
prolog = Prolog()
prolog.consult(pl_file)

last_action  = ""
action_queue = []
expected_pos = None   # posicao esperada apos proximo 'andar'
game_over    = False  # True quando agente retorna ao inicio apos explorar

# ---------------------------------------------------------------------------
# Geracao aleatoria de mapa
# ---------------------------------------------------------------------------

def gerar_mapa():
    """Gera posicoes aleatorias para todos os elementos e asserta no Prolog."""
    cells = [(x, y) for x in range(1, 13) for y in range(1, 13)]
    cells.remove((1, 1))   # posicao inicial sempre vazia
    random.shuffle(cells)

    elementos = (
        ['D'] * 2 +   # 2 inimigos dano 50
        ['d'] * 2 +   # 2 inimigos dano 20
        ['T'] * 4 +   # 4 teleporters/morcegos
        ['P'] * 8 +   # 8 pocos/obstaculos
        ['O'] * 3 +   # 3 ouros
        ['U'] * 3     # 3 powerups de energia
    )

    atrib = {}
    for i, elem in enumerate(elementos):
        atrib[cells[i]] = elem

    list(prolog.query("retractall(tile(_,_,_)), retractall(map_size(_,_))"))
    list(prolog.query("assert(map_size(12,12))"))
    for x in range(1, 13):
        for y in range(1, 13):
            c = atrib.get((x, y), '')
            list(prolog.query(f"assert(tile({x},{y},'{c}'))"))

    # nao chamar set_real aqui; sera chamado apos reset_game na inicializacao


def carregar_mapa_arquivo(caminho):
    """Carrega mapa de arquivo .pl substituindo o mapa atual."""
    list(prolog.query("retractall(tile(_,_,_)), retractall(map_size(_,_))"))
    prolog.consult(caminho.replace('\\', '/'))
    list(prolog.query("set_real(1,1)"))
    list(prolog.query("assert(visitado(1,1))"))

# ---------------------------------------------------------------------------
# A* pathfinding
# ---------------------------------------------------------------------------

DIRS      = ['norte', 'leste', 'sul', 'oeste']
DIR_DELTA = {'norte': (0, 1), 'sul': (0, -1), 'leste': (1, 0), 'oeste': (-1, 0)}


def _turns(de, para):
    """Retorna lista minima de acoes de rotacao para mudar de direcao."""
    di = DIRS.index(de)
    pi = DIRS.index(para)
    diff = (pi - di) % 4
    if diff == 0:
        return []
    if diff == 1:
        return ['virar_direita']
    if diff == 2:
        return ['virar_direita', 'virar_direita']
    return ['virar_esquerda']


def astar(sx, sy, sdir, gx, gy, celulas_seguras):
    """
    Retorna lista de acoes Prolog (virar_direita/esquerda/andar)
    para ir de (sx,sy,sdir) ate (gx,gy) passando por celulas_seguras.
    O destino e sempre atingivel mesmo que nao esteja em celulas_seguras.
    Retorna [] se nao ha caminho.
    """
    if sx == gx and sy == gy:
        return []

    def h(x, y):
        return abs(x - gx) + abs(y - gy)

    # (f, g, x, y, direcao, caminho)
    heap = [(h(sx, sy), 0, sx, sy, sdir, [])]
    visitado_astar = {}

    while heap:
        f, g, cx, cy, cdir, path = heapq.heappop(heap)

        if cx == gx and cy == gy:
            return path

        chave = (cx, cy, cdir)
        if chave in visitado_astar and visitado_astar[chave] <= g:
            continue
        visitado_astar[chave] = g

        for d in DIRS:
            dx, dy = DIR_DELTA[d]
            nx, ny = cx + dx, cy + dy
            if not (1 <= nx <= 12 and 1 <= ny <= 12):
                continue
            if (nx, ny) not in celulas_seguras and not (nx == gx and ny == gy):
                continue
            t = _turns(cdir, d)
            new_path = path + t + ['andar']
            ng = g + len(t) + 1
            heapq.heappush(heap, (ng + h(nx, ny), ng, nx, ny, d, new_path))

    return []


def get_celulas_seguras():
    """Celulas transitaveis: visitadas OU certeza com memoria vazia."""
    seguras = set((v[0], v[1]) for v in visitados)
    for c in certezas:
        x, y = int(c[0]), int(c[1])
        if list(prolog.query(f"memory({x},{y},[])")):
            seguras.add((x, y))
    return seguras


def get_celulas_nao_perigosas():
    """Todas as celulas que nao sao confirmadamente perigosas."""
    perigosas = set()
    for c in certezas:
        x, y = int(c[0]), int(c[1])
        if list(prolog.query(
            f"memory({x},{y},L), (member(brisa,L); member(passos,L); member(flash,L))"
        )):
            perigosas.add((x, y))
    return {(x, y) for x in range(1, 13) for y in range(1, 13)} - perigosas

# ---------------------------------------------------------------------------
# Decisao do agente
# ---------------------------------------------------------------------------

def decisao():
    global action_queue, expected_pos, game_over

    if game_over:
        return ""

    # Detectar teletransporte: posicao diferente do esperado
    if expected_pos is not None:
        if (player_pos[0], player_pos[1]) != expected_pos and player_pos[2] != 'morto':
            action_queue.clear()
        expected_pos = None

    # Executar proxima acao da fila se houver
    if action_queue:
        action = action_queue.pop(0)
        if action == 'andar':
            dx, dy = DIR_DELTA.get(player_pos[2], (0, 0))
            nx, ny = player_pos[0] + dx, player_pos[1] + dy
            if 1 <= nx <= 12 and 1 <= ny <= 12:
                expected_pos = (nx, ny)
        return action

    # Consultar Prolog: pegar ou explorar?
    acoes = list(prolog.query("executa_acao(X)"))
    if not acoes:
        return ""

    acao = str(acoes[0]['X'])

    if acao == 'pegar':
        return 'pegar'

    # acao == 'explorar': consultar Prolog para objetivo de navegacao
    objetivos = list(prolog.query("escolhe_objetivo(X,Y)"))
    if not objetivos:
        return ""

    gx = int(objetivos[0]['X'])
    gy = int(objetivos[0]['Y'])

    # Detectar fim de jogo: agente retorna ao inicio sem mais o que explorar
    if gx == 1 and gy == 1 and player_pos[0] == 1 and player_pos[1] == 1:
        game_over = True
        return ""

    if gx == player_pos[0] and gy == player_pos[1]:
        return ""

    # Planejar caminho com A*
    seguras = get_celulas_seguras()
    seguras.add((player_pos[0], player_pos[1]))
    acoes_caminho = astar(player_pos[0], player_pos[1], player_pos[2], gx, gy, seguras)

    # Fallback: relaxar restricoes e tentar celulas nao confirmadamente perigosas
    if not acoes_caminho:
        seguras_relaxadas = get_celulas_nao_perigosas()
        seguras_relaxadas.add((player_pos[0], player_pos[1]))
        acoes_caminho = astar(player_pos[0], player_pos[1], player_pos[2], gx, gy, seguras_relaxadas)

    if acoes_caminho:
        action_queue.extend(acoes_caminho)
        action = action_queue.pop(0)
        if action == 'andar':
            dx, dy = DIR_DELTA.get(player_pos[2], (0, 0))
            nx, ny = player_pos[0] + dx, player_pos[1] + dy
            if 1 <= nx <= 12 and 1 <= ny <= 12:
                expected_pos = (nx, ny)
        return action

    return ""

# ---------------------------------------------------------------------------
# Interface Prolog <-> Python
# ---------------------------------------------------------------------------

def exec_prolog(a):
    global last_action
    if a != "":
        list(prolog.query(a))
    last_action = a


def update_prolog():
    global player_pos, mapa, energia, pontuacao, visitados, certezas, show_map

    list(prolog.query("atualiza_obs, verifica_player"))

    x = Variable()
    y = Variable()
    visitado = Functor("visitado", 2)
    vq = Query(visitado(x, y))
    visitados.clear()
    while vq.nextSolution():
        visitados.append((x.value, y.value))
    vq.closeQuery()

    x = Variable()
    y = Variable()
    certeza = Functor("certeza", 2)
    cq = Query(certeza(x, y))
    certezas.clear()
    while cq.nextSolution():
        certezas.append((x.value, y.value))
    cq.closeQuery()

    if show_map:
        x = Variable()
        y = Variable()
        z = Variable()
        tile = Functor("tile", 3)
        tq = Query(tile(x, y, z))
        while tq.nextSolution():
            mapa[y.get_value() - 1][x.get_value() - 1] = str(z.value)
        tq.closeQuery()
    else:
        for j in range(size_y):
            for i in range(size_x):
                mapa[j][i] = ''

        x = Variable()
        y = Variable()
        z = Variable()
        memory = Functor("memory", 3)
        mq = Query(memory(x, y, z))
        while mq.nextSolution():
            for s in z.value:
                sx = str(s)
                idx_y = y.get_value() - 1
                idx_x = x.get_value() - 1
                if sx == 'brisa':
                    mapa[idx_y][idx_x] += 'P'
                elif sx == 'flash':
                    mapa[idx_y][idx_x] += 'T'
                elif sx == 'passos':
                    mapa[idx_y][idx_x] += 'D'
                elif sx == 'reflexo':
                    mapa[idx_y][idx_x] += 'U'
                elif sx == 'brilho':
                    mapa[idx_y][idx_x] += 'O'
        mq.closeQuery()

    x = Variable()
    y = Variable()
    z = Variable()
    posicao = Functor("posicao", 3)
    pq = Query(posicao(x, y, z))
    pq.nextSolution()
    player_pos = (x.value, y.value, str(z.value))
    pq.closeQuery()

    x = Variable()
    energia_f = Functor("energia", 1)
    eq = Query(energia_f(x))
    eq.nextSolution()
    energia = x.value
    eq.closeQuery()

    x = Variable()
    pontuacao_f = Functor("pontuacao", 1)
    pnq = Query(pontuacao_f(x))
    pnq.nextSolution()
    pontuacao = x.value
    pnq.closeQuery()

# ---------------------------------------------------------------------------
# Carregamento de assets
# ---------------------------------------------------------------------------

def load():
    global sys_font, clock
    global img_wall, img_grass, img_floor
    global img_gold, img_health, img_pit, img_bat, img_enemy1, img_enemy2
    global bw_img_floor, bw_img_gold, bw_img_health, bw_img_pit
    global bw_img_bat, bw_img_enemy1, bw_img_enemy2
    global img_player_up, img_player_down, img_player_left, img_player_right, img_tomb

    sys_font = pygame.font.Font(pygame.font.get_default_font(), 20)
    clock    = pygame.time.Clock()

    tile_size = (width // size_x, height // size_y)

    def load_img(name):
        img = pygame.image.load(name)
        return pygame.transform.scale(img, tile_size)

    img_wall         = load_img('wall.jpg')
    img_grass        = load_img('grass.jpg')
    img_floor        = load_img('floor.png')
    img_gold         = load_img('gold.png')
    img_pit          = load_img('pit.png')
    img_enemy1       = load_img('enemy1.png')
    img_enemy2       = load_img('enemy2.png')
    img_bat          = load_img('bat.png')
    img_health       = load_img('health.png')
    img_player_up    = load_img('player_up.png')
    img_player_down  = load_img('player_down.png')
    img_player_left  = load_img('player_left.png')
    img_player_right = load_img('player_right.png')
    img_tomb         = load_img('tombstone.png')

    bw_img_floor   = load_img('bw_floor.png')
    bw_img_gold    = load_img('bw_gold.png')
    bw_img_pit     = load_img('bw_pit.png')
    bw_img_enemy1  = load_img('bw_enemy1.png')
    bw_img_enemy2  = load_img('bw_enemy2.png')
    bw_img_bat     = load_img('bw_bat.png')
    bw_img_health  = load_img('bw_health.png')

# ---------------------------------------------------------------------------
# Loop de jogo
# ---------------------------------------------------------------------------

def update(dt, screen):
    global elapsed_time
    elapsed_time += dt
    if (elapsed_time / 1000) > auto_play_tempo:
        if auto_play and player_pos[2] != 'morto':
            exec_prolog(decisao())
            update_prolog()
        elapsed_time = 0


def key_pressed(event):
    global show_map
    if event.type == pygame.KEYDOWN:
        if not auto_play and player_pos[2] != 'morto':
            if event.key == pygame.K_LEFT:
                exec_prolog("virar_esquerda")
                update_prolog()
            elif event.key == pygame.K_RIGHT:
                exec_prolog("virar_direita")
                update_prolog()
            elif event.key == pygame.K_UP:
                exec_prolog("andar")
                update_prolog()
            if event.key == pygame.K_SPACE:
                exec_prolog("pegar")
                update_prolog()
        if event.key == pygame.K_m:
            show_map = not show_map
            update_prolog()


def draw_screen(screen):
    screen.fill((0, 0, 0))

    tw = width  // size_x
    th = height // size_y

    for row in range(size_y):
        for col in range(size_x):
            gx = col + 1
            gy = size_y - row   # y do Prolog (1 embaixo, 12 em cima)

            visited = (gx, gy) in [(v[0], v[1]) for v in visitados]
            certain = (gx, gy) in [(c[0], c[1]) for c in certezas]

            base = img_floor if visited else bw_img_floor
            screen.blit(base, (col * tw, row * th))

            cell = mapa[gy - 1][col]   # mapa indexado por (y_prolog-1, x_prolog-1)

            if 'P' in cell:
                img = img_pit     if certain else bw_img_pit
                screen.blit(img, (col * tw, row * th))
            if 'T' in cell:
                img = img_bat     if certain else bw_img_bat
                screen.blit(img, (col * tw, row * th))
            if 'D' in cell:
                img = img_enemy1  if certain else bw_img_enemy1
                screen.blit(img, (col * tw, row * th))
            if 'd' in cell:
                img = img_enemy2  if certain else bw_img_enemy2
                screen.blit(img, (col * tw, row * th))
            if 'U' in cell:
                img = img_health  if certain else bw_img_health
                screen.blit(img, (col * tw, row * th))
            if 'O' in cell:
                img = img_gold    if certain else bw_img_gold
                screen.blit(img, (col * tw, row * th))

            if col == player_pos[0] - 1 and row == size_y - player_pos[1]:
                d = player_pos[2]
                if d == 'norte':
                    screen.blit(img_player_up,    (col * tw, row * th))
                elif d == 'sul':
                    screen.blit(img_player_down,  (col * tw, row * th))
                elif d == 'leste':
                    screen.blit(img_player_right, (col * tw, row * th))
                elif d == 'oeste':
                    screen.blit(img_player_left,  (col * tw, row * th))
                else:
                    screen.blit(img_tomb,         (col * tw, row * th))

    t = sys_font.render(f"Pontuacao: {pontuacao}", False, (255, 255, 255))
    screen.blit(t, t.get_rect(top=height + 5, left=40))

    t = sys_font.render(last_action, False, (255, 255, 255))
    screen.blit(t, t.get_rect(top=height + 5, left=width // 2 - 40))

    t = sys_font.render(f"Energia: {energia}", False, (255, 255, 255))
    screen.blit(t, t.get_rect(top=height + 5, left=width - 140))

    if game_over:
        msg = sys_font.render("FIM DE JOGO - Pontuacao Final: " + str(pontuacao), False, (255, 220, 0))
        screen.blit(msg, msg.get_rect(center=(width // 2, height // 2)))


def main_loop(screen):
    global clock
    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
                break
            key_pressed(e)

        dt = clock.tick()
        update(dt, screen)
        draw_screen(screen)
        pygame.display.update()

# ---------------------------------------------------------------------------
# Inicializacao
# ---------------------------------------------------------------------------

# reset_game ja foi chamado automaticamente ao consultar main.pl
gerar_mapa()                                     # gera mapa e asserta tiles
list(prolog.query("set_real(1,1)"))              # registra posicao inicial na KB
list(prolog.query("assert(visitado(1,1))"))      # marca inicio como visitado
update_prolog()                                  # sincroniza estado Python

pygame.init()
pygame.display.set_caption('INF1771 Trabalho 2 - Agente Logico - Pitfall')
screen = pygame.display.set_mode((width, height + 30))
load()

main_loop(screen)
pygame.quit()
