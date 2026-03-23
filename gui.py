import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import json
import os

import map_parser
import character_planner
import astar

# Cores GUI
GUI_COLORS = {
    ".": "white",
    "R": "gray70",
    "V": "darkgreen",
    "A": "blue",
    "M": "orange", # Montanha
    "*": "cyan",   
    "@": "red",
    "BG": "black"
}

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Avatar Pathfinding - Sistema Especialista (Trabalho 1 - PUC-Rio)")
        self.geometry("900x650")
        self.configure(bg="#2E2E2E")
        self.running_simulation = False
        
        # Variáveis de Estado Backend
        self.grid_data = []
        self.terrain_costs = {}
        self.difficulties = {}
        self.agility = {}
        self.max_uses = 8
        self.checkpoints = {}
        self.sequence = []
        self.assignment = {}
        
        self.delay_speed = tk.DoubleVar(value=0.1)
        
        self.build_ui()
        self.load_settings_db()

    def build_ui(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        
        # Navbar / Top Controle
        top_frame = tk.Frame(self, bg="#444", pd=5)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Button(top_frame, text="Carregar Mapa (.txt)", command=self.action_load_map).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Executar Vredito A*", command=self.action_start_simulation).pack(side=tk.LEFT, padx=5)
        
        tk.Label(top_frame, text="Velocidade Visual (s):", bg="#444", fg="white").pack(side=tk.LEFT, padx=10)
        ttk.Scale(top_frame, from_=0.0, to=1.0, variable=self.delay_speed, orient=tk.HORIZONTAL, length=100).pack(side=tk.LEFT)
        
        # Painel Lateral (Infos)
        side_frame = tk.Frame(self, width=250, bg="#333", relief=tk.SUNKEN)
        side_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        tk.Label(side_frame, text="PAINEL DE TELEMETRIA", font=('Consolas', 12, 'bold'), bg="#333", fg="cyan").pack(pady=10)
        
        self.lbl_stage = tk.Label(side_frame, text="Etapa Atual: Idle", bg="#333", fg="white", anchor="w")
        self.lbl_stage.pack(fill=tk.X, padx=10, pady=5)
        
        self.lbl_troop = tk.Label(side_frame, text="Grupo Ativo: None", bg="#333", fg="yellow", anchor="w", wraplength=200)
        self.lbl_troop.pack(fill=tk.X, padx=10, pady=5)
        
        self.lbl_acc_cost = tk.Label(side_frame, text="Custo Acumulado Terreno: 0", bg="#333", fg="white", anchor="w")
        self.lbl_acc_cost.pack(fill=tk.X, padx=10, pady=5)
        
        self.lbl_acc_time = tk.Label(side_frame, text="Tempo Fictício (Chars): 0", bg="#333", fg="white", anchor="w")
        self.lbl_acc_time.pack(fill=tk.X, padx=10, pady=5)
        
        self.lbl_nodes = tk.Label(side_frame, text="Nós Varridos RAM (A*): 0", bg="#333", fg="#ff8888", anchor="w")
        self.lbl_nodes.pack(fill=tk.X, padx=10, pady=5)
        
        # Matriz Central / Canvas
        canvas_frame = tk.Frame(self, bg="black")
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.canvas = tk.Canvas(canvas_frame, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def load_settings_db(self):
        try:
            with open("config.json", "r", encoding="utf-8") as fs:
                db = json.load(fs)
                self.terrain_costs = db.get("terrain_costs", {})
                self.difficulties = db.get("difficulty", {})
                self.agility = db.get("agility", {})
                self.max_uses = db.get("max_uses_per_character", 8)
                print("[GUI] Config loaded nativamente da file tree.")
        except Exception:
             messagebox.showwarning("Falta de Config", "Não achei o config.json, caindo em falback.")

    def action_load_map(self):
        filep = filedialog.askopenfilename(title="Selecione o array texto do MAPA", filetypes=(("Text Files", "*.txt"),))
        if not filep: return
        
        try:
            self.grid_data = map_parser.load_map(filep)
            self.checkpoints = map_parser.find_checkpoints(self.grid_data)
            alpha_ref = "0123456789BCDEGHIJKLNOPQSTUVWXYZ"
            self.sequence = sorted(self.checkpoints.keys(), key=lambda k: alpha_ref.index(k) if k in alpha_ref else 999)
            
            # Planeja antecipadamente via Greedy (rápido pra GUI) pra setar a arvore de turnos
            plan_g = character_planner.greedy_assignment(self.difficulties, self.agility, self.max_uses)
            self.assignment, _ = character_planner.hill_climbing_optimize(plan_g, self.difficulties, self.agility, self.max_uses, 500)
            
            self.render_canvas_state(set(), None)
            messagebox.showinfo("Sucesso", "Mapeamento Topográfico e Logístico extraído com louvor!")
        except Exception as e:
            messagebox.showerror("Erro Crítico IO", str(e))

    def render_canvas_state(self, path_set, current_agent_pos):
        if not self.grid_data: return
        self.canvas.delete("all")
        
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if cw <= 1 or ch <= 1: cw, ch = 650, 600
        
        max_r, max_c = len(self.grid_data), len(self.grid_data[0])
        cell_w, cell_h = cw / max_c, ch / max_r
        
        for r in range(max_r):
            for c in range(max_c):
                char_id = self.grid_data[r][c]
                
                if current_agent_pos and current_agent_pos == (r, c):
                    color = GUI_COLORS["@"]
                elif (r, c) in path_set:
                    color = GUI_COLORS["*"]
                elif str.isalnum(char_id) and char_id not in ["R", "V", "A", "M"]:
                    color = "magenta"
                else:
                    color = GUI_COLORS.get(char_id, "black")
                    
                x1, y1 = c * cell_w, r * cell_h
                x2, y2 = x1 + cell_w, y1 + cell_h
                
                # Otimização tk: criar tudo como rectangles pequenos
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=color)

    def action_start_simulation(self):
        if not self.grid_data or self.running_simulation:
            messagebox.showwarning("Atenção", "Mapa ausente ou Thread de execução do A* já está viva.")
            return
            
        self.running_simulation = True
        thread = threading.Thread(target=self._background_sim_runner, daemon=True)
        thread.start()
        
    def _background_sim_runner(self):
        acc_cost = 0
        acc_time_virt = 0.0
        acc_nodes = 0
        global_path = []
        
        for i in range(len(self.sequence) - 1):
            o_id, d_id = self.sequence[i], self.sequence[i+1]
            start_coord, goal_coord = self.checkpoints[o_id], self.checkpoints[d_id]
            
            spath, cst, ndes, _ = astar.astar(self.grid_data, start_coord, goal_coord, self.terrain_costs)
            
            troop = self.assignment.get(d_id, [])
            diff = self.difficulties.get(d_id, 0)
            time_spent = (diff / sum(self.agility[x] for x in troop)) if troop else 0
            
            acc_cost += cst
            acc_nodes += ndes
            acc_time_virt += time_spent
            
            if global_path: global_path.extend(spath[1:])
            else: global_path.extend(spath)
            
            # Request Main Thread para Atualizar a UI em tempo real do Path! (Thread-Safety via event)
            params = (o_id, d_id, acc_cost, acc_nodes, acc_time_virt, troop, set(global_path), goal_coord)
            self.after(0, self._ui_updater, *params)
            
            wait_time = self.delay_speed.get()
            if wait_time > 0:
                time.sleep(wait_time)
                
        self.running_simulation = False
        self.after(0, lambda: messagebox.showinfo("Simulação Real Finalizada", "Avatar cruzou a linha de chegada em 'Z'!"))
        
    def _ui_updater(self, o_id, d_id, cst, ndes, tm, trp, pset, agent_pos):
        self.lbl_stage.config(text=f"Etapa Direção: {o_id} -> {d_id}")
        self.lbl_troop.config(text=f"Grupo Ativo: {', '.join(trp)}")
        self.lbl_acc_cost.config(text=f"Custo Terreno: {cst} un")
        self.lbl_nodes.config(text=f"Nós Expandidos (RAM): {ndes}")
        self.lbl_acc_time.config(text=f"Relógio Personagens: {tm:.2f} h")
        self.render_canvas_state(pset, agent_pos)

if __name__ == "__main__":
    app = Application()
    app.mainloop()
