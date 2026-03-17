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

# COLORS
COLOR_BG = "#FFFFFF"       
COLOR_GRID = "#E0E0E0"     
COLOR_WALL = "#404040"     
COLOR_AGENT = "#4169E1"    
COLOR_EXIT = "#32CD32"     
COLOR_DOOR = "#FFE4B5"     

class PedestrianEvacuationUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Phase-Based Rule Simulation with Heatmap")
        self.root.geometry("1250x800") 

        self.is_running = False
        
        # 1. Init Data Grid
        self.grid_data = np.zeros((ROWS, COLS), dtype=int)
        self.static_grid = np.zeros((ROWS, COLS), dtype=int) 
        
        self.setup_floor_plan()
        
        self.S_matrix = np.full((ROWS, COLS), 500.0) 
        self.heatmap_matrix = np.zeros((ROWS, COLS), dtype=float) 
        
        self.calculate_distance_map() 
        
        self.create_layout()
        self.draw_grid()

    def create_layout(self):
        self.panel_left = tk.Frame(self.root, width=200, bg="#f0f0f0", padx=10, pady=10)
        self.panel_left.pack(side=tk.LEFT, fill=tk.Y)
        
        tk.Label(self.panel_left, text="CA Parameters", font=("Arial", 12, "bold"), bg="#f0f0f0").pack(pady=(0, 20))
        self.entry_ks = self.add_input("Ks (Rasionalitas)", "3.0")
        ttk.Separator(self.panel_left, orient='horizontal').pack(fill='x', pady=20)

        self.btn_gen = tk.Button(self.panel_left, text="Generate", command=self.generate_people, bg="white", width=15, pady=5)
        self.btn_gen.pack(pady=5)
        self.btn_start = tk.Button(self.panel_left, text="Start", command=self.start_simulation, bg="#dddddd", width=15, pady=5)
        self.btn_start.pack(pady=5)
        self.btn_stop = tk.Button(self.panel_left, text="Stop", command=self.stop_simulation, bg="#dddddd", width=15, pady=5)
        self.btn_stop.pack(pady=5)
        
        self.lbl_stats = tk.Label(self.panel_left, text="Total Agents: 0", bg="#f0f0f0", font=("Arial", 10))
        self.lbl_stats.pack(side=tk.BOTTOM, pady=20)

        self.panel_right = tk.Frame(self.root, bg="white")
        self.panel_right.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        
        tk.Label(self.panel_right, text="Simulation of Evacuation in the Building", font=("Arial", 14, "bold"), fg="blue", bg="white").pack(pady=10)

        self.canvas = tk.Canvas(self.panel_right, bg="white", width=COLS*GRID_SIZE, height=ROWS*GRID_SIZE)
        self.canvas.pack(padx=20, pady=20)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def add_input(self, label_text, default_val):
        frame = tk.Frame(self.panel_left, bg="#f0f0f0")
        frame.pack(fill=tk.X, pady=2)
        tk.Label(frame, text=label_text, width=15, anchor="w", bg="#f0f0f0").pack(side=tk.LEFT)
        entry = tk.Entry(frame, width=8)
        entry.insert(0, default_val)
        entry.pack(side=tk.RIGHT)
        return entry 
    
    def setup_floor_plan(self):
        self.grid_data = np.zeros((ROWS, COLS), dtype=int)
        
        self.grid_data[0, :] = 1
        self.grid_data[ROWS-1, :] = 1
        self.grid_data[:, 0] = 1
        self.grid_data[:, COLS-1] = 1
        
        self.grid_data[5:25, 20] = 1
        self.grid_data[10, 1:20] = 1
        self.grid_data[20, 1:20] = 1
        self.grid_data[15, 20:39] = 1
        
        self.grid_data[10, 10:13] = 4 
        self.grid_data[20, 10:13] = 4 
        self.grid_data[15, 25:28] = 4 
        self.grid_data[12:15, 20] = 4 
        
        self.grid_data[ROWS-1, 18:22] = 3 
        
        # FIX PENTING 1: Simpan blueprint ke static_grid
        self.static_grid = np.copy(self.grid_data)

    def calculate_distance_map(self):
        raw_S = np.full((ROWS, COLS), 500.0)
        pq =[]
        for r, c in np.argwhere(self.static_grid == 3):
            raw_S[r, c] = 0.0
            heapq.heappush(pq, (0.0, r, c))
            
        while pq:
            dist, r, c = heapq.heappop(pq)
            if dist > raw_S[r, c]: continue
            for dr, dc, weight in[(-1,0,1.0), (1,0,1.0), (0,-1,1.0), (0,1,1.0), (-1,-1,1.4), (-1,1,1.4), (1,-1,1.4), (1,1,1.4)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < ROWS and 0 <= nc < COLS and self.static_grid[nr, nc] != 1:
                    if dist + weight < raw_S[nr, nc]:
                        raw_S[nr, nc] = dist + weight
                        heapq.heappush(pq, (dist + weight, nr, nc))

        door_cells = set(tuple(x) for x in np.argwhere(self.static_grid == 4))
        door_groups =[]
        
        while door_cells:
            start = door_cells.pop()
            group = [start]
            q = [start]
            while q:
                r, c = q.pop(0)
                for dr, dc in[(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (1,1), (-1,1), (1,-1)]:
                    nr, nc = r+dr, c+dc
                    if (nr, nc) in door_cells:
                        door_cells.remove((nr, nc))
                        group.append((nr, nc))
                        q.append((nr, nc))
            door_groups.append(group)
            
        self.S_matrix = np.full((ROWS, COLS), 500.0)
        pq =[]
        
        for r, c in np.argwhere(self.static_grid == 3):
            self.S_matrix[r, c] = 0.0
            heapq.heappush(pq, (0.0, r, c))

        for group in door_groups:
            door_set = set(group)
            neighbors = set()
            
            for r, c in group:
                for dr, dc in[(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (1,1), (-1,1), (1,-1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < ROWS and 0 <= nc < COLS:
                        if self.static_grid[nr, nc] != 1 and (nr, nc) not in door_set:
                            neighbors.add((nr, nc))
                            
            clusters =[]
            unvisited_neighbors = set(neighbors)
            
            while unvisited_neighbors:
                start_n = unvisited_neighbors.pop()
                cluster = [start_n]
                q_n =[start_n]
                while q_n:
                    curr_r, curr_c = q_n.pop(0)
                    for dr, dc in[(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (1,1), (-1,1), (1,-1)]:
                        nr, nc = curr_r+dr, curr_c+dc
                        if (nr, nc) in unvisited_neighbors:
                            unvisited_neighbors.remove((nr, nc))
                            cluster.append((nr, nc))
                            q_n.append((nr, nc))
                clusters.append(cluster)
                
            best_avg = 500.0
            for cluster in clusters:
                avg_val = sum(raw_S[nr, nc] for nr, nc in cluster) / len(cluster)
                if avg_val < best_avg:
                    best_avg = avg_val
                    
            for r, c in group:
                self.S_matrix[r, c] = best_avg
                heapq.heappush(pq, (best_avg, r, c))

        while pq:
            dist, r, c = heapq.heappop(pq)
            if dist > self.S_matrix[r, c]: continue
            for dr, dc, weight in[(-1,0,1.0), (1,0,1.0), (0,-1,1.0), (0,1,1.0), (-1,-1,1.4), (-1,1,1.4), (1,-1,1.4), (1,1,1.4)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < ROWS and 0 <= nc < COLS and self.static_grid[nr, nc] != 1:
                    if self.static_grid[nr, nc] == 4:
                        continue
                    if dist + weight < self.S_matrix[nr, nc]:
                        self.S_matrix[nr, nc] = dist + weight
                        heapq.heappush(pq, (dist + weight, nr, nc))

    def draw_grid(self):
        self.canvas.delete("all")
        
        # FIX PENTING 2: Menggunakan static_grid untuk menggambar lantai, tembok, dan pintu
        for r in range(ROWS):
            for c in range(COLS):
                static_val = self.static_grid[r, c]
                x1, y1 = c*GRID_SIZE, r*GRID_SIZE
                x2, y2 = x1+GRID_SIZE, y1+GRID_SIZE
                
                if static_val == 1: 
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLOR_WALL, outline="")
                elif static_val == 3: 
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLOR_EXIT, outline="")
                elif static_val == 4: 
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLOR_DOOR, outline="")
                else:
                    heat = self.heatmap_matrix[r, c]
                    if heat > 0.2:
                        color = self.get_heat_color(heat)
                        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
                    else:
                        self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLOR_BG, outline="")

        for r in range(ROWS + 1):
            self.canvas.create_line(0, r*GRID_SIZE, COLS*GRID_SIZE, r*GRID_SIZE, fill=COLOR_GRID)
        for c in range(COLS + 1):
            self.canvas.create_line(c*GRID_SIZE, 0, c*GRID_SIZE, ROWS*GRID_SIZE, fill=COLOR_GRID)

        for r in range(ROWS):
            for c in range(COLS):
                static_val = self.static_grid[r, c]
                live_val = self.grid_data[r, c]
                x1, y1 = c*GRID_SIZE, r*GRID_SIZE
                
                if static_val != 1:
                    s_val = self.S_matrix[r, c]
                    text_val = "500" if s_val >= 500 else f"{s_val:.1f}"
                    self.canvas.create_text(x1 + GRID_SIZE/2, y1 + GRID_SIZE/2, text=text_val, fill="black", font=("Arial", 7))

                if live_val == 2: 
                    pad = 4
                    self.canvas.create_oval(x1+pad, y1+pad, x1+GRID_SIZE-pad, y1+GRID_SIZE-pad, fill=COLOR_AGENT, outline="")

    def get_heat_color(self, heat_val):
        if heat_val <= 0.2: return "#FFFFFF" 
        ratio = min(heat_val / 15.0, 1.0) 
        if ratio < 0.5:
            b = int(255 * (1.0 - (ratio * 2)))
            b = max(0, min(255, b))
            return f"#ff{255:02x}{b:02x}"
        else:
            g = int(255 * (1.0 - ((ratio - 0.5) * 2)))
            g = max(0, min(255, g))
            return f"#ff{g:02x}00"

    def generate_people(self):
        self.heatmap_matrix = np.zeros((ROWS, COLS), dtype=float)
        count = 0
        while count < 50:
            r = random.randint(1, ROWS-2)
            c = random.randint(1, COLS-2)
            # FIX PENTING 3: Cek blueprint asli agar agen tidak spawn di atas tembok
            if self.static_grid[r, c] == 0 and self.grid_data[r, c] == 0:
                self.grid_data[r, c] = 2
                count += 1
                
        self.lbl_stats.config(text=f"Total Agents: {np.sum(self.grid_data == 2)}")
        self.calculate_distance_map()
        self.draw_grid()

    def start_simulation(self):
        self.calculate_distance_map() 
        self.is_running = True
        self.btn_start.config(bg="#90EE90")
        self.run_step()

    def stop_simulation(self):
        self.is_running = False
        self.btn_start.config(bg="#dddddd")

    def run_step(self):
        if not self.is_running:
            return

        current_agents = np.argwhere(self.grid_data == 2)
        if len(current_agents) == 0:
            self.stop_simulation()
            return

        try: ks = float(self.entry_ks.get())
        except ValueError: ks = 3.0

        distance_groups = defaultdict(list)
        for r, c in current_agents:
            d = round(self.S_matrix[r, c], 1)
            distance_groups[d].append((r, c))
            
        sorted_distances = sorted(distance_groups.keys())
        
        new_grid = np.copy(self.grid_data)
        used_exits = set() 

        for d in sorted_distances:
            unresolved_agents = distance_groups[d].copy()
            
            while unresolved_agents:
                proposals = defaultdict(list)
                
                for r, c in unresolved_agents:
                    moves =[
                        (r, c), (r-1, c), (r+1, c), (r, c-1), (r, c+1),
                        (r-1, c-1), (r-1, c+1), (r+1, c-1), (r+1, c+1)
                    ]
                    
                    valid_moves = []
                    distances =[]
                    
                    for nr, nc in moves:
                        if 0 <= nr < ROWS and 0 <= nc < COLS:
                            is_empty = (new_grid[nr, nc] in [0, 4]) 
                            is_available_exit = (new_grid[nr, nc] == 3 and (nr, nc) not in used_exits)
                            is_my_own_spot = (nr == r and nc == c)
                            
                            if is_empty or is_available_exit or is_my_own_spot:
                                valid_moves.append((nr, nc))
                                distances.append(self.S_matrix[nr, nc])
                    
                    if valid_moves:
                        min_dist = np.min(distances)
                        weights =[np.exp(-ks * (dist - min_dist)) for dist in distances]
                        total_w = sum(weights)
                        probs = [w / total_w for w in weights]
                        
                        choice_idx = np.random.choice(len(valid_moves), p=probs)
                        best_target = valid_moves[choice_idx]
                    else:
                        best_target = (r, c)
                        
                    proposals[best_target].append((r, c))

                for target, contenders in proposals.items():
                    if len(contenders) == 1:
                        winner = contenders[0]
                    else:
                        winner = random.choice(contenders) 
                        
                    unresolved_agents.remove(winner)
                    
                    if winner != target:
                        # FIX PENTING 4: Kembalikan sel lama ke bentuk aslinya (Lantai atau Pintu)
                        new_grid[winner[0], winner[1]] = self.static_grid[winner[0], winner[1]]
                        
                        if new_grid[target[0], target[1]] == 3:
                            used_exits.add(target) 
                        else:
                            new_grid[target[0], target[1]] = 2 

        self.grid_data = new_grid
        
        current_agents_new = np.argwhere(self.grid_data == 2)
        for r, c in current_agents_new:
            for dr in[-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = r + dr, c + dc
                    # Gunakan static_grid agar dinding tidak memanas
                    if 0 <= nr < ROWS and 0 <= nc < COLS and self.static_grid[nr, nc] != 1:
                        added_heat = 2.0 if (dr == 0 and dc == 0) else 0.5
                        self.heatmap_matrix[nr, nc] += added_heat
                        
        self.heatmap_matrix *= 0.85 

        self.draw_grid()
        self.lbl_stats.config(text=f"Total Agents: {np.sum(self.grid_data == 2)}")
        
        if np.sum(self.grid_data == 2) > 0:
            self.root.after(100, self.run_step)
        else:
            self.stop_simulation()

    def on_canvas_click(self, event):
        """FIX PENTING 5: Sinkronisasi klik dengan Blueprint"""
        c = event.x // GRID_SIZE
        r = event.y // GRID_SIZE
        if 0 <= r < ROWS and 0 <= c < COLS:
            if self.static_grid[r, c] in[1, 4]:
                self.grid_data[r, c] = 0
                self.static_grid[r, c] = 0
            elif self.static_grid[r, c] == 0:
                self.grid_data[r, c] = 1
                self.static_grid[r, c] = 1
                
            self.calculate_distance_map()
            self.draw_grid()

if __name__ == "__main__":
    root = tk.Tk()
    app = PedestrianEvacuationUI(root)
    root.mainloop()