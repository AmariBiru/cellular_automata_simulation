import tkinter as tk
from tkinter import ttk
import numpy as np
import random
import heapq 
import math
from collections import defaultdict

# --- CONFIGURATION ---
GRID_SIZE = 25  
COLS = 40       
ROWS = 30       

COLOR_BG = "#FFFFFF"       
COLOR_GRID = "#E0E0E0"     
COLOR_WALL = "#404040"     
COLOR_AGENT = "#4169E1"    
COLOR_EXIT = "#32CD32"     
COLOR_DOOR = "#FFE4B5"     

class UnifiedEvacuationUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Viscous Fluid Dynamics with Softmax Spreading")
        self.root.geometry("1250x800") 

        self.is_running = False
        
        self.grid_data = np.zeros((ROWS, COLS), dtype=int)
        self.static_grid = np.zeros((ROWS, COLS), dtype=int) 
        self.setup_floor_plan()
        
        self.S_matrix = np.full((ROWS, COLS), 500.0)             
        self.heatmap_matrix = np.zeros((ROWS, COLS), dtype=float) 
        self.Phi_wall = np.full((ROWS, COLS), 500.0)             
        self.V_des = np.zeros((ROWS, COLS, 2), dtype=float)      
        
        self.draw_mode = 1 
        
        self.create_layout()
        self.recalculate_all_maps()
        self.draw_grid()

    def create_layout(self):
        self.panel_left = tk.Frame(self.root, width=200, bg="#f0f0f0", padx=10, pady=10)
        self.panel_left.pack(side=tk.LEFT, fill=tk.Y)
        
        tk.Label(self.panel_left, text="Drawing Tools", font=("Arial", 12, "bold"), bg="#f0f0f0").pack(pady=10)
        btn_frame = tk.Frame(self.panel_left, bg="#f0f0f0")
        btn_frame.pack(fill='x', pady=5)
        
        tk.Button(btn_frame, text="Tembok", bg=COLOR_WALL, fg="white", width=15, command=lambda: self.set_draw_mode(1)).pack(pady=2)
        tk.Button(btn_frame, text="Pintu", bg=COLOR_DOOR, fg="black", width=15, command=lambda: self.set_draw_mode(4)).pack(pady=2)
        tk.Button(btn_frame, text="Exit", bg=COLOR_EXIT, fg="white", width=15, command=lambda: self.set_draw_mode(3)).pack(pady=2)
        tk.Button(btn_frame, text="Penghapus", bg=COLOR_BG, fg="black", width=15, command=lambda: self.set_draw_mode(0)).pack(pady=2)
        
        ttk.Separator(self.panel_left, orient='horizontal').pack(fill='x', pady=15)
        
        tk.Label(self.panel_left, text="Fluid Parameters", font=("Arial", 12, "bold"), bg="#f0f0f0").pack(pady=5)
        # --- PERBAIKAN: KEDUA INPUT INI SEKARANG ADA DI UI ---
        self.entry_visc = self.add_input("Viskositas", "0.2")
        self.entry_ks = self.add_input("Ks (Menyebar)", "2.5")
        
        self.show_arrows = tk.BooleanVar(value=True)
        tk.Checkbutton(self.panel_left, text="Tampilkan Vektor", variable=self.show_arrows, command=self.draw_grid, bg="#f0f0f0").pack(pady=5)
        
        ttk.Separator(self.panel_left, orient='horizontal').pack(fill='x', pady=15)
        self.btn_gen = tk.Button(self.panel_left, text="Generate Agents", command=self.generate_people, bg="white", width=15)
        self.btn_gen.pack(pady=5)
        self.btn_start = tk.Button(self.panel_left, text="Start", command=self.start_simulation, bg="#90EE90", width=15)
        self.btn_start.pack(pady=5)
        self.btn_stop = tk.Button(self.panel_left, text="Stop", command=self.stop_simulation, bg="#FFB6C1", width=15)
        self.btn_stop.pack(pady=5)
        
        self.lbl_stats = tk.Label(self.panel_left, text="Total Agents: 0", bg="#f0f0f0", font=("Arial", 10))
        self.lbl_stats.pack(side=tk.BOTTOM, pady=20)

        self.panel_right = tk.Frame(self.root, bg="white")
        self.panel_right.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        self.canvas = tk.Canvas(self.panel_right, bg="white", width=COLS*GRID_SIZE, height=ROWS*GRID_SIZE)
        self.canvas.pack(padx=20, pady=20)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<Button-1>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def add_input(self, label_text, default_val):
        frame = tk.Frame(self.panel_left, bg="#f0f0f0")
        frame.pack(fill=tk.X, pady=2)
        tk.Label(frame, text=label_text, width=15, anchor="w", bg="#f0f0f0").pack(side=tk.LEFT)
        entry = tk.Entry(frame, width=5)
        entry.insert(0, default_val)
        entry.pack(side=tk.RIGHT)
        return entry 

    def set_draw_mode(self, mode): self.draw_mode = mode

    def setup_floor_plan(self):
        self.grid_data = np.zeros((ROWS, COLS), dtype=int)
        self.grid_data[0, :] = 1; self.grid_data[ROWS-1, :] = 1
        self.grid_data[:, 0] = 1; self.grid_data[:, COLS-1] = 1
        self.grid_data[5:25, 20] = 1; self.grid_data[10, 1:20] = 1
        self.grid_data[20, 1:20] = 1; self.grid_data[15, 20:39] = 1
        self.grid_data[10, 10:13] = 4; self.grid_data[20, 10:13] = 4 
        self.grid_data[15, 25:28] = 4; self.grid_data[12:15, 20] = 4 
        self.grid_data[ROWS-1, 18:22] = 3 
        self.static_grid = np.copy(self.grid_data)

    def paint(self, event):
        c = event.x // GRID_SIZE; r = event.y // GRID_SIZE
        if 0 <= r < ROWS and 0 <= c < COLS:
            val = self.draw_mode
            if self.static_grid[r, c] != val:
                self.static_grid[r, c] = val
                if self.grid_data[r, c] != 2: self.grid_data[r, c] = val
                self.draw_grid_fast(r, c)

    def draw_grid_fast(self, r, c):
        val = self.static_grid[r, c]
        color = COLOR_BG
        if val == 1: color = COLOR_WALL
        elif val == 3: color = COLOR_EXIT
        elif val == 4: color = COLOR_DOOR
        x1, y1 = c*GRID_SIZE, r*GRID_SIZE
        self.canvas.create_rectangle(x1, y1, x1+GRID_SIZE, y1+GRID_SIZE, fill=color, outline="")

    def on_release(self, event):
        self.recalculate_all_maps()
        self.draw_grid()

    def recalculate_all_maps(self):
        self.calculate_distance_to_walls()  
        self.calculate_distance_map()       
        self.calculate_V_des()              

    def calculate_distance_to_walls(self):
        self.Phi_wall = np.full((ROWS, COLS), 500.0)
        pq =[]
        for r, c in np.argwhere(self.static_grid == 1):
            self.Phi_wall[r, c] = 0.0; heapq.heappush(pq, (0.0, r, c))
        while pq:
            dist, r, c = heapq.heappop(pq)
            if dist > self.Phi_wall[r, c]: continue
            for dr, dc, weight in[(-1,0,1.0), (1,0,1.0), (0,-1,1.0), (0,1,1.0), (-1,-1,1.4), (-1,1,1.4), (1,-1,1.4), (1,1,1.4)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < ROWS and 0 <= nc < COLS:
                    if dist + weight < self.Phi_wall[nr, nc]:
                        self.Phi_wall[nr, nc] = dist + weight; heapq.heappush(pq, (dist + weight, nr, nc))

    def calculate_distance_map(self):
        try: visc = float(self.entry_visc.get())
        except: visc = 0.2

        raw_S = np.full((ROWS, COLS), 500.0)
        pq =[]
        for r, c in np.argwhere(self.static_grid == 3):
            raw_S[r, c] = 0.0; heapq.heappush(pq, (0.0, r, c))
            
        while pq:
            dist, r, c = heapq.heappop(pq)
            if dist > raw_S[r, c]: continue
            for dr, dc, weight in[(-1,0,1.0), (1,0,1.0), (0,-1,1.0), (0,1,1.0), (-1,-1,1.4), (-1,1,1.4), (1,-1,1.4), (1,1,1.4)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < ROWS and 0 <= nc < COLS and self.static_grid[nr, nc] != 1:
                    phi_val = self.Phi_wall[nr, nc]
                    penalty = max(0.0, 3.0 - phi_val) * visc
                    if dist + weight + penalty < raw_S[nr, nc]:
                        raw_S[nr, nc] = dist + weight + penalty
                        heapq.heappush(pq, (dist + weight + penalty, nr, nc))

        door_cells = set(tuple(x) for x in np.argwhere(self.static_grid == 4))
        door_groups =[]
        while door_cells:
            start = door_cells.pop()
            group =[start]; q = [start]
            while q:
                r, c = q.pop(0)
                for dr, dc in[(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (1,1), (-1,1), (1,-1)]:
                    nr, nc = r+dr, c+dc
                    if (nr, nc) in door_cells:
                        door_cells.remove((nr, nc))
                        group.append((nr, nc)); q.append((nr, nc))
            door_groups.append(group)
            
        self.S_matrix = np.full((ROWS, COLS), 500.0)
        pq =[]
        for r, c in np.argwhere(self.static_grid == 3):
            self.S_matrix[r, c] = 0.0; heapq.heappush(pq, (0.0, r, c))

        for group in door_groups:
            door_set = set(group)
            neighbors = set()
            for r, c in group:
                for dr, dc in[(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (1,1), (-1,1), (1,-1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < ROWS and 0 <= nc < COLS and self.static_grid[nr, nc] != 1 and (nr, nc) not in door_set:
                        neighbors.add((nr, nc))
            
            clusters =[]; unvisited = set(neighbors)
            while unvisited:
                start_n = unvisited.pop()
                cluster =[start_n]; q_n =[start_n]
                while q_n:
                    curr_r, curr_c = q_n.pop(0)
                    for dr, dc in[(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (1,1), (-1,1), (1,-1)]:
                        nr, nc = curr_r+dr, curr_c+dc
                        if (nr, nc) in unvisited:
                            unvisited.remove((nr, nc))
                            cluster.append((nr, nc)); q_n.append((nr, nc))
                clusters.append(cluster)
                
            best_avg = 500.0
            for cluster in clusters:
                avg_val = sum(raw_S[nr, nc] for nr, nc in cluster) / len(cluster)
                if avg_val < best_avg: best_avg = avg_val
                    
            for r, c in group:
                self.S_matrix[r, c] = best_avg; heapq.heappush(pq, (best_avg, r, c))

        while pq:
            dist, r, c = heapq.heappop(pq)
            if dist > self.S_matrix[r, c]: continue
            for dr, dc, weight in[(-1,0,1.0), (1,0,1.0), (0,-1,1.0), (0,1,1.0), (-1,-1,1.4), (-1,1,1.4), (1,-1,1.4), (1,1,1.4)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < ROWS and 0 <= nc < COLS and self.static_grid[nr, nc] != 1:
                    if self.static_grid[nr, nc] == 4: continue
                    phi_val = self.Phi_wall[nr, nc]
                    penalty = max(0.0, 3.0 - phi_val) * visc
                    if dist + weight + penalty < self.S_matrix[nr, nc]:
                        self.S_matrix[nr, nc] = dist + weight + penalty
                        heapq.heappush(pq, (dist + weight + penalty, nr, nc))

    def calculate_V_des(self):
        def get_val(r, c, default):
            return self.S_matrix[r, c] if (0 <= r < ROWS and 0 <= c < COLS and self.static_grid[r, c] != 1) else default

        for r in range(ROWS):
            for c in range(COLS):
                if self.static_grid[r, c] != 1:
                    vc = self.S_matrix[r, c]
                    vl = get_val(r, c-1, vc); vr = get_val(r, c+1, vc)
                    vu = get_val(r-1, c, vc); vd = get_val(r+1, c, vc)

                    dx = (vr - vl)/2.0 if vr != vc and vl != vc else (vr - vc if vr != vc else vc - vl)
                    dy = (vd - vu)/2.0 if vd != vc and vu != vc else (vd - vc if vd != vc else vc - vu)

                    vx, vy = -dx, -dy
                    magnitude = math.hypot(vx, vy)
                    if magnitude > 0: vx /= magnitude; vy /= magnitude
                        
                    self.V_des[r, c, 0] = vy; self.V_des[r, c, 1] = vx 

    def draw_grid(self):
        self.canvas.delete("all")
        for r in range(ROWS):
            for c in range(COLS):
                val = self.static_grid[r, c]
                x1, y1 = c*GRID_SIZE, r*GRID_SIZE
                x2, y2 = x1+GRID_SIZE, y1+GRID_SIZE
                
                if val == 1: self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLOR_WALL, outline="")
                elif val == 3: self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLOR_EXIT, outline="")
                elif val == 4: self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLOR_DOOR, outline="")
                else:
                    heat = self.heatmap_matrix[r, c]
                    if heat > 0.2:
                        color = self.get_heat_color(heat)
                        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
                    else:
                        self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLOR_BG, outline="")

                if self.show_arrows.get() and val not in[1, 3]:
                    vy, vx = self.V_des[r, c, 0], self.V_des[r, c, 1]
                    if vx != 0 or vy != 0:
                        cx, cy = x1 + GRID_SIZE/2, y1 + GRID_SIZE/2
                        self.canvas.create_line(cx, cy, cx + vx*(GRID_SIZE/2.5), cy + vy*(GRID_SIZE/2.5), arrow=tk.LAST, fill="blue", width=1.5)

                if self.grid_data[r, c] == 2: 
                    pad = 4; self.canvas.create_oval(x1+pad, y1+pad, x2-pad, y2-pad, fill=COLOR_AGENT, outline="")

        for r in range(ROWS + 1): self.canvas.create_line(0, r*GRID_SIZE, COLS*GRID_SIZE, r*GRID_SIZE, fill=COLOR_GRID)
        for c in range(COLS + 1): self.canvas.create_line(c*GRID_SIZE, 0, c*GRID_SIZE, ROWS*GRID_SIZE, fill=COLOR_GRID)

    def get_heat_color(self, heat_val):
        if heat_val <= 0.2: return "#FFFFFF" 
        ratio = min(heat_val / 15.0, 1.0) 
        if ratio < 0.5: return f"#ff{255:02x}{max(0, int(255*(1.0-ratio*2))):02x}"
        else: return f"#ff{max(0, int(255*(1.0-(ratio-0.5)*2))):02x}00"

    def generate_people(self):
        count = 0
        while count < 100:
            r, c = random.randint(1, ROWS-2), random.randint(1, COLS-2)
            if self.static_grid[r, c] == 0 and self.grid_data[r, c] == 0:
                self.grid_data[r, c] = 2; count += 1
        self.lbl_stats.config(text=f"Total Agents: {np.sum(self.grid_data == 2)}")
        self.draw_grid()

    def start_simulation(self):
        self.recalculate_all_maps()
        self.is_running = True
        self.btn_start.config(bg="#32CD32")
        self.run_step()

    def stop_simulation(self):
        self.is_running = False
        self.btn_start.config(bg="#90EE90")

    def run_step(self):
        if not self.is_running: return
        current_agents = np.argwhere(self.grid_data == 2)
        if len(current_agents) == 0:
            self.stop_simulation(); return

        try: ks = float(self.entry_ks.get())
        except ValueError: ks = 2.5

        C_rep = 0.5     
        Radius = 1.5    
        M_wall = 2.0    

        rho = np.zeros((ROWS, COLS), dtype=float)
        for r, c in current_agents: rho[r, c] = 1.0

        distance_groups = defaultdict(list)
        for r, c in current_agents:
            distance_groups[round(self.S_matrix[r, c], 1)].append((r, c))
            
        sorted_distances = sorted(distance_groups.keys())
        new_grid = np.copy(self.grid_data)
        used_exits = set() 

        for d in sorted_distances:
            unresolved_agents = distance_groups[d].copy()
            while unresolved_agents:
                proposals = defaultdict(list)
                for r, c in unresolved_agents:
                    v_des = self.V_des[r, c] 
                    v_int = np.array([0.0, 0.0])
                    
                    R_search = int(math.ceil(Radius))
                    for dr in range(-R_search, R_search + 1):
                        for dc in range(-R_search, R_search + 1):
                            if dr == 0 and dc == 0: continue
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < ROWS and 0 <= nc < COLS:
                                if rho[nr, nc] > 0: 
                                    dist = math.hypot(dr, dc)
                                    if dist <= Radius:
                                        norm_vec = np.array([dr, dc]) / dist
                                        if np.dot(norm_vec, v_des) >= -0.5:
                                            v_int += -C_rep * rho[nr, nc] * (norm_vec / dist)

                    if np.linalg.norm(v_int) > 1.5:
                        v_int = (v_int / np.linalg.norm(v_int)) * 1.5

                    lambda_val = max(0.0, 1.0 - (self.Phi_wall[r, c] / M_wall)) 
                    v_obs = max(0.0, 1.0 + np.dot(v_des, v_int)) * v_des
                    V_final = lambda_val * v_obs + (1.0 - lambda_val) * (v_des + v_int)
                    
                    moves =[(r, c), (r-1, c), (r+1, c), (r, c-1), (r, c+1),
                            (r-1, c-1), (r-1, c+1), (r+1, c-1), (r+1, c+1)]
                    
                    valid_moves = []
                    scores =[]
                    
                    for nr, nc in moves:
                        if 0 <= nr < ROWS and 0 <= nc < COLS:
                            if new_grid[nr, nc] in [0, 4] or (new_grid[nr, nc] == 3 and (nr, nc) not in used_exits) or (nr == r and nc == c):
                                move_vec = np.array([nr - r, nc - c])
                                if nr == r and nc == c: 
                                    score = 0.0
                                else:
                                    move_vec = move_vec / math.hypot(move_vec[0], move_vec[1])
                                    score = np.dot(V_final, move_vec)
                                
                                valid_moves.append((nr, nc))
                                scores.append(score)
                    
                    if valid_moves:
                        scores = np.array(scores)
                        exp_scores = np.exp(ks * (scores - np.max(scores)))
                        probs = exp_scores / np.sum(exp_scores)
                        
                        choice_idx = np.random.choice(len(valid_moves), p=probs)
                        best_target = valid_moves[choice_idx]
                    else:
                        best_target = (r, c)
                                    
                    proposals[best_target].append((r, c))

                for target, contenders in proposals.items():
                    winner = contenders[0] if len(contenders) == 1 else random.choice(contenders)
                    unresolved_agents.remove(winner)
                    if winner != target:
                        new_grid[winner[0], winner[1]] = self.static_grid[winner[0], winner[1]]
                        if new_grid[target[0], target[1]] == 3: used_exits.add(target) 
                        else: new_grid[target[0], target[1]] = 2 

        self.grid_data = new_grid
        
        current_agents_new = np.argwhere(self.grid_data == 2)
        for r, c in current_agents_new:
            for dr in[-1, 0, 1]:
                for dc in[-1, 0, 1]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < ROWS and 0 <= nc < COLS and self.static_grid[nr, nc] != 1:
                        added_heat = 2.0 if (dr == 0 and dc == 0) else 0.5
                        self.heatmap_matrix[nr, nc] += added_heat
                        
        self.heatmap_matrix *= 0.85 

        self.draw_grid()
        self.lbl_stats.config(text=f"Total Agents: {np.sum(self.grid_data == 2)}")
        self.root.after(100, self.run_step)

if __name__ == "__main__":
    root = tk.Tk()
    app = UnifiedEvacuationUI(root)
    root.mainloop()