# =============================================================================
# visualizer.py — Visualizacao pygame do mapa Avatar A*
#
# Dependencia: pip install pygame
#
# Controles:
#   ENTER / ESPACO  — iniciar / pausar-continuar
#   UP / DOWN       — aumentar / diminuir velocidade
#   R               — reiniciar
#   Q / ESC         — sair
# =============================================================================

from __future__ import annotations

import sys
from typing import Optional

try:
    import pygame
except ImportError:
    print("pygame nao instalado. Execute: pip install pygame")
    sys.exit(1)

from character_optimizer import OptimizationResult
from config import CHARACTERS, CHECKPOINT_SYMBOLS

# ---------------------------------------------------------------------------
# Constantes fixas
# ---------------------------------------------------------------------------

MAP_COLS     = 300
MAP_ROWS     = 82
PANEL_W_MIN  = 240   # largura minima do painel (o restante vai para o mapa)
BG           = (26, 26, 46)   # #1a1a2e — fundo uniforme

_TERRAIN: dict[str, tuple[int, int, int]] = {
    ".": (240, 240, 240),
    "R": (120, 120, 120),
    "F": ( 34, 139,  34),
    "A": ( 55,  95, 210),
    "M": (110,  50,  15),
}
_C_CHECKPOINT  = (220,  20,  60)
_C_CP_OUTLINE  = (255, 255, 255)
_C_PATH_DONE   = (130, 100,   0)
_C_PATH_ACTIVE = (255, 215,   0)
_C_PATH_AHEAD  = (170, 170,  55)
_C_AGENT_HALO  = (255, 235,  80)
_C_AGENT       = (255,  85,   0)
_C_SEP         = ( 55,  55, 100)
_C_TEXT        = (210, 210, 215)
_C_TITLE       = (255, 215,   0)
_C_GREEN       = ( 55, 210,  80)
_C_ORANGE      = (255, 140,   0)
_C_RED         = (215,  55,  55)
_C_DIM         = (140, 140, 155)

_FPS = 60


def _use_bar_color(used: int, max_uses: int) -> tuple[int, int, int]:
    ratio = used / max_uses
    if ratio >= 1.0: return _C_RED
    if ratio >= 0.6: return _C_ORANGE
    return _C_GREEN


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------

class AvatarVisualizer:
    """Mapa inteiro visivel de uma vez, agente animado, painel lateral fixo.

    O cell_size e calculado automaticamente para que o mapa preencha toda a
    area disponivel (resolucao da tela menos o painel) sem espaco preto.
    """

    def __init__(
        self,
        grid: list[list[str]],
        checkpoints: dict[str, tuple[int, int]],
        segments: list[tuple[list[tuple[int, int]], int]],
        opt_result: OptimizationResult,
        init_speed: int = 10,
    ) -> None:
        self.grid        = grid
        self.checkpoints = checkpoints
        self.segments    = segments
        self.opt         = opt_result

        # Caminho completo (sem duplicar pontos de juncao)
        self.full_path: list[tuple[int, int]] = []
        self.seg_starts: list[int] = []
        for i, (path, _) in enumerate(segments):
            self.seg_starts.append(len(self.full_path))
            self.full_path.extend(path if i == 0 else path[1:])
        self.seg_starts.append(len(self.full_path))

        self.pos    = 0
        self.speed  = max(1, init_speed)
        self.paused = False
        self.state  = "title"

        # Dimensoes calculadas em run()
        self.cell    = 5
        self.map_w   = MAP_COLS * self.cell
        self.map_h   = MAP_ROWS * self.cell
        self.panel_w = 300   # recalculado em run()

        self._map_surf:     Optional[pygame.Surface] = None
        self._summary_surf: Optional[pygame.Surface] = None
        self._font_xl:      Optional[pygame.font.Font] = None
        self._font_lg:      Optional[pygame.font.Font] = None
        self._font_md:      Optional[pygame.font.Font] = None
        self._font_sm:      Optional[pygame.font.Font] = None

    # -----------------------------------------------------------------------
    # Geometria
    # -----------------------------------------------------------------------

    def _seg_of(self, pos: int) -> int:
        for i in range(len(self.seg_starts) - 1):
            if self.seg_starts[i] <= pos < self.seg_starts[i + 1]:
                return i
        return len(self.segments) - 1

    def _cell_center(self, row: int, col: int) -> tuple[int, int]:
        return col * self.cell + self.cell // 2, row * self.cell + self.cell // 2

    # -----------------------------------------------------------------------
    # Pre-renderizacao do mapa
    # -----------------------------------------------------------------------

    def _build_map_surface(self) -> pygame.Surface:
        c = self.cell
        surf = pygame.Surface((self.map_w, self.map_h))
        surf.fill(BG)

        for row, row_data in enumerate(self.grid):
            for col, ch in enumerate(row_data):
                color = _TERRAIN.get(ch, (180, 0, 180))
                surf.fill(color, (col * c, row * c, c, c))

        # Checkpoints
        cp_r  = max(5, c + 3)
        cp_lbl_size = max(9, c + 1)
        try:
            cp_font = pygame.font.SysFont("Consolas", cp_lbl_size, bold=True)
        except Exception:
            cp_font = pygame.font.Font(None, cp_lbl_size + 4)

        for sym, (row, col) in self.checkpoints.items():
            cx, cy = self._cell_center(row, col)
            pygame.draw.circle(surf, _C_CHECKPOINT, (cx, cy), cp_r)
            pygame.draw.circle(surf, _C_CP_OUTLINE, (cx, cy), cp_r, 2)
            lbl = cp_font.render(sym, True, (255, 255, 255))
            surf.blit(lbl, (cx - lbl.get_width() // 2, cy - lbl.get_height() // 2))

        return surf

    def _build_summary_surf(self) -> pygame.Surface:
        """Copia do mapa com todos os segmentos desenhados."""
        surf = self._map_surf.copy()
        n    = len(self.segments)
        pt   = max(2, self.cell // 2)
        for i, (path, _) in enumerate(self.segments):
            t     = i / max(1, n - 1)
            color = (255, int(215 - 115 * t), 0)
            for row, col in path:
                cx, cy = self._cell_center(row, col)
                surf.fill(color, (cx - pt // 2, cy - pt // 2, pt, pt))
        return surf

    # -----------------------------------------------------------------------
    # Desenho frame-a-frame
    # -----------------------------------------------------------------------

    def _draw_paths(self, surf: pygame.Surface, seg_idx: int) -> None:
        pt = max(2, self.cell // 2)
        for i, (path, _) in enumerate(self.segments):
            color = (_C_PATH_DONE   if i < seg_idx  else
                     _C_PATH_ACTIVE if i == seg_idx else
                     _C_PATH_AHEAD)
            for row, col in path:
                cx, cy = self._cell_center(row, col)
                surf.fill(color, (cx - pt // 2, cy - pt // 2, pt, pt))

    def _draw_agent(self, surf: pygame.Surface) -> None:
        if self.pos >= len(self.full_path):
            return
        row, col = self.full_path[self.pos]
        cx, cy   = self._cell_center(row, col)
        r_halo = max(5, self.cell + 4)
        r_body = max(3, self.cell + 1)
        pygame.draw.circle(surf, _C_AGENT_HALO, (cx, cy), r_halo)
        pygame.draw.circle(surf, _C_AGENT,      (cx, cy), r_body)
        pygame.draw.circle(surf, (255, 255, 180), (cx, cy), r_halo, 1)

    # -----------------------------------------------------------------------
    # Painel lateral
    # -----------------------------------------------------------------------

    def _draw_panel(self, surf: pygame.Surface, seg_idx: int) -> None:
        px  = self.map_w
        win_h = surf.get_height()
        surf.fill(BG, (px, 0, self.panel_w, win_h))
        pygame.draw.line(surf, _C_SEP, (px, 0), (px, win_h), 1)

        xi = px + 12
        y  = 10

        def line(s: str, font, color: tuple = _C_TEXT) -> None:
            nonlocal y
            t = font.render(s, True, color)
            surf.blit(t, (xi, y))
            y += t.get_height() + 3

        def sep(gap: int = 6) -> None:
            nonlocal y
            y += gap // 2
            pygame.draw.line(surf, _C_SEP, (px + 6, y), (px + self.panel_w - 6, y))
            y += gap // 2 + 2

        def bar(used: int, total: int, w: int, h: int = 9) -> None:
            nonlocal y
            pygame.draw.rect(surf, (35, 35, 65), (xi, y, w, h), border_radius=3)
            if used > 0:
                fw = max(2, w * used // total)
                pygame.draw.rect(surf, _use_bar_color(used, total),
                                 (xi, y, fw, h), border_radius=3)
            y += h + 3

        sym_a = CHECKPOINT_SYMBOLS[seg_idx]
        sym_b = CHECKPOINT_SYMBOLS[seg_idx + 1]

        # ── Cabecalho da etapa ──────────────────────────────────────────
        line(f"ETAPA {seg_idx + 1:2d} / {len(self.segments)}", self._font_xl, _C_TITLE)
        line(f"  {sym_a}  ->  {sym_b}", self._font_lg, (185, 195, 255))
        sep()

        # ── Dados da etapa ──────────────────────────────────────────────
        sr = self.opt.stage_results[seg_idx]
        line(f"Dif {sr.difficulty:>3}   Ag {sr.agility_sum:.2f}   T {sr.time:.2f}",
             self._font_md)
        sep()

        # ── Personagens ─────────────────────────────────────────────────
        line("PERSONAGENS", self._font_md, _C_TITLE)
        bar_w = self.panel_w - 26
        used_map = self._chars_used_so_far(seg_idx)
        for ch in sorted(CHARACTERS):
            used    = used_map[ch]
            mx      = CHARACTERS[ch]["max_uses"]
            ag      = CHARACTERS[ch]["agility"]
            active  = ch in sr.characters
            color   = _C_TITLE if active else _C_TEXT
            label   = f"{'*' if active else ' '}{ch:<8} {ag:.1f}  {used}/{mx}"
            line(label, self._font_sm, color)
            bar(used, mx, bar_w)
        sep()

        # ── Caminho ─────────────────────────────────────────────────────
        line("CAMINHO (A*)", self._font_md, _C_TITLE)
        _, seg_cost  = self.segments[seg_idx]
        acum_path    = sum(c for _, c in self.segments[:seg_idx + 1])
        acum_time    = sum(r.time for r in self.opt.stage_results[:seg_idx + 1])
        line(f"Seg {seg_cost:>4}   Acum {acum_path:>5}", self._font_sm)
        line(f"Tempo acum {acum_time:>8.2f}", self._font_sm)
        sep()

        # ── Progresso ───────────────────────────────────────────────────
        line("PROGRESSO", self._font_md, _C_TITLE)
        n  = len(self.segments)
        bw = self.panel_w - 26
        bh = 16
        pygame.draw.rect(surf, (38, 38, 72), (xi, y, bw, bh), border_radius=5)
        fw = max(4, bw * (seg_idx + 1) // n)
        pygame.draw.rect(surf, _C_TITLE,     (xi, y, fw, bh), border_radius=5)
        pt = self._font_sm.render(f"{seg_idx + 1} / {n}", True, (18, 18, 18))
        surf.blit(pt, (xi + bw // 2 - pt.get_width() // 2, y + 1))
        y += bh + 4
        sep()

        # ── Estado ──────────────────────────────────────────────────────
        estado  = "[ PAUSADO ]" if self.paused else "[  rodando  ]"
        ecor    = _C_RED if self.paused else _C_GREEN
        line(f"Vel {self.speed:>3} cel/fr   {estado}", self._font_md, ecor)
        sep()

        # ── Controles ───────────────────────────────────────────────────
        for ctrl in ("ENTER/SPC : pausar",
                     "UP / DOWN : velocidade",
                     "R         : reiniciar",
                     "Q / ESC   : sair"):
            line(ctrl, self._font_sm, _C_DIM)

    def _chars_used_so_far(self, seg_idx: int) -> dict[str, int]:
        used = {name: 0 for name in CHARACTERS}
        for i in range(seg_idx + 1):
            for ch in self.opt.stage_results[i].characters:
                used[ch] += 1
        return used

    # -----------------------------------------------------------------------
    # Tela inicial
    # -----------------------------------------------------------------------

    def _draw_title(self, surf: pygame.Surface) -> None:
        surf.blit(self._map_surf, (0, 0))
        pt = max(2, self.cell // 2)
        for path, _ in self.segments:
            for row, col in path:
                cx, cy = self._cell_center(row, col)
                surf.fill(_C_PATH_AHEAD, (cx - pt // 2, cy - pt // 2, pt, pt))

        # Painel de boas-vindas
        px = self.map_w
        h  = surf.get_height()
        surf.fill(BG, (px, 0, self.panel_w, h))
        pygame.draw.line(surf, _C_SEP, (px, 0), (px, h), 1)

        xi, y = px + 16, 24
        def ln(s, font, color=_C_TEXT):
            nonlocal y
            t = font.render(s, True, color)
            surf.blit(t, (xi, y));  y += t.get_height() + 7

        ln("AVATAR  A*",             self._font_xl, _C_TITLE)
        ln("A Lenda de Aang",        self._font_lg, (185, 200, 255))
        y += 8
        ln(f"Mapa        {MAP_ROWS} x {MAP_COLS}", self._font_md)
        ln(f"Cell size   {self.cell} px",           self._font_md)
        ln(f"Checkpoints {len(self.checkpoints)}",  self._font_md)
        ln(f"Segmentos   {len(self.segments)}",     self._font_md)
        ln(f"Cel. path   {len(self.full_path)}",    self._font_md)
        y += 8
        ln(f"Otimizacao: {self.opt.method}",        self._font_md)
        ln(f"Tempo total {self.opt.total_time:.2f}", self._font_md)
        y += 14
        ln("Pressione ENTER",   self._font_xl, _C_GREEN)
        ln("para iniciar",      self._font_lg, _C_GREEN)
        y += 14
        for ctrl in ("ENTER/SPC : pausar",
                     "UP / DOWN : velocidade",
                     "R         : reiniciar",
                     "Q / ESC   : sair"):
            ln(ctrl, self._font_sm, _C_DIM)

    # -----------------------------------------------------------------------
    # Tela de resumo final
    # -----------------------------------------------------------------------

    def _draw_done(self, surf: pygame.Surface) -> None:
        if self._summary_surf is None:
            self._summary_surf = self._build_summary_surf()

        # Mapa com todos os caminhos
        surf.blit(self._summary_surf, (0, 0))

        # Banner central
        vp_w = self.map_w
        banner = pygame.Surface((vp_w, 48), pygame.SRCALPHA)
        banner.fill((0, 0, 0, 175))
        surf.blit(banner, (0, self.map_h // 2 - 24))
        msg = self._font_xl.render(
            "Percurso concluido!   Pressione Q para sair.", True, _C_GREEN)
        surf.blit(msg, (vp_w // 2 - msg.get_width() // 2, self.map_h // 2 - 15))

        # Painel de resumo
        px = self.map_w
        win_h = surf.get_height()
        surf.fill(BG, (px, 0, self.panel_w, win_h))
        pygame.draw.line(surf, _C_SEP, (px, 0), (px, win_h), 1)

        xi, y = px + 12, 14
        total_path = sum(c for _, c in self.segments)
        total_time = self.opt.total_time

        def ln(s, font, color=_C_TEXT):
            nonlocal y
            t = font.render(s, True, color)
            surf.blit(t, (xi, y));  y += t.get_height() + 5

        def sep():
            nonlocal y;  y += 4
            pygame.draw.line(surf, _C_SEP, (px+6, y), (px+self.panel_w-6, y))
            y += 6

        ln("RESUMO FINAL",    self._font_xl, _C_TITLE)
        ln(self.opt.method,   self._font_md, _C_DIM)
        sep()
        ln("CAMINHO (A*)",    self._font_md, _C_TITLE)
        ln(f"Custo total    {total_path}", self._font_md)
        ln(f"Segmentos      {len(self.segments)}", self._font_md)
        ln(f"Celulas path   {len(self.full_path)}", self._font_md)
        sep()
        ln("ETAPAS",          self._font_md, _C_TITLE)
        ln(f"Tempo total    {total_time:.2f}", self._font_md)
        sep()
        ln("USOS",            self._font_md, _C_TITLE)
        bar_w = self.panel_w - 26
        for name in sorted(CHARACTERS):
            used = CHARACTERS[name]["max_uses"] - self.opt.uses_remaining[name]
            mx   = CHARACTERS[name]["max_uses"]
            ag   = CHARACTERS[name]["agility"]
            t = self._font_sm.render(f"{name:<8} {ag:.1f}  {used}/{mx}", True, _C_TEXT)
            surf.blit(t, (xi, y));  y += t.get_height() + 2
            pygame.draw.rect(surf, (35, 35, 65), (xi, y, bar_w, 8), border_radius=3)
            fw = max(2, bar_w * used // mx)
            pygame.draw.rect(surf, _use_bar_color(used, mx), (xi, y, fw, 8), border_radius=3)
            y += 11
        sep()
        ln("CUSTO TOTAL",     self._font_lg, _C_TITLE)
        ln(f"{total_path} + {total_time:.2f}", self._font_md)
        ln(f"= {total_path + total_time:.2f}", self._font_xl, _C_GREEN)

    # -----------------------------------------------------------------------
    # Loop principal
    # -----------------------------------------------------------------------

    def run(self) -> None:
        pygame.init()

        # -- Calcula cell_size para preencher a tela sem espaco preto --------
        # Formula: cell = min((scr_w - PANEL_MIN) // 300, scr_h // 82)
        # O painel recebe o espaco restante: panel_w = scr_w - map_w
        info  = pygame.display.Info()
        scr_w = info.current_w                  # largura total (sem fator)
        scr_h = int(info.current_h * 0.94)     # altura menos barra de tarefas
        self.cell    = max(1, min((scr_w - PANEL_W_MIN) // MAP_COLS,
                                   scr_h // MAP_ROWS))
        self.map_w   = MAP_COLS * self.cell
        self.map_h   = MAP_ROWS * self.cell
        self.panel_w = scr_w - self.map_w       # painel ocupa o restante
        win_w        = scr_w                    # janela = largura total, sem preto
        win_h        = self.map_h
        # --------------------------------------------------------------------

        screen = pygame.display.set_mode((win_w, win_h))
        pygame.display.set_caption("Avatar A* - A Lenda de Aang")

        def _font(size: int, bold: bool = False) -> pygame.font.Font:
            for name in ("Consolas", "Courier New", "Courier", "monospace"):
                try:
                    f = pygame.font.SysFont(name, size, bold=bold)
                    if f:
                        return f
                except Exception:
                    pass
            return pygame.font.Font(None, size + 4)

        self._font_xl = _font(18, bold=True)
        self._font_lg = _font(15, bold=True)
        self._font_md = _font(13)
        self._font_sm = _font(12)

        self._map_surf = self._build_map_surface()
        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); return

                if event.type == pygame.KEYDOWN:
                    k = event.key
                    if k in (pygame.K_q, pygame.K_ESCAPE):
                        pygame.quit(); return

                    if self.state == "title" and k in (pygame.K_RETURN, pygame.K_SPACE):
                        self.state = "running"

                    elif self.state in ("running", "done"):
                        if k in (pygame.K_SPACE, pygame.K_RETURN):
                            self.paused = not self.paused
                        elif k == pygame.K_UP:
                            self.speed = min(self.speed + 5, 200)
                        elif k == pygame.K_DOWN:
                            self.speed = max(self.speed - 5, 1)
                        elif k == pygame.K_r:
                            self.pos  = 0;  self.paused = False
                            self.state = "running";  self._summary_surf = None

            # Renderizacao
            screen.fill(BG)

            if self.state == "title":
                self._draw_title(screen)

            elif self.state in ("running", "done"):
                seg_idx = self._seg_of(self.pos)

                if self.state == "done":
                    self._draw_done(screen)
                else:
                    screen.blit(self._map_surf, (0, 0))
                    self._draw_paths(screen, seg_idx)
                    self._draw_agent(screen)
                    self._draw_panel(screen, seg_idx)

                if self.state == "running" and not self.paused:
                    self.pos += self.speed
                    if self.pos >= len(self.full_path):
                        self.pos = len(self.full_path) - 1
                        self.state = "done"

            pygame.display.flip()
            clock.tick(_FPS)
