import tkinter as tk
from tkinter import ttk
import numpy as np
import random
import heapq 
import math

# --- CONFIGURATION ---
GRID_SIZE = 20  # Size of cell in pixels
COLS = 40       # Width of the building
ROWS = 30       # Height of the building

# COLORS
COLOR_BG = "#FFFFFF"       # White background
COLOR_GRID = "#E0E0E0"     # Light gray grid lines
COLOR_WALL = "#404040"     # Dark Gray Walls
COLOR_AGENT = "#4169E1"    # Royal Blue (Like the screenshot)
COLOR_EXIT = "#32CD32"     # Lime Green

class PedestrianEvacuationUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CA for Pedestrian - Simulation UI")
        self.root.geometry("1000x650") # Window size

        self.is_running = False
        
        # 1. Init Data Grid (0=Empty, 1=Wall, 2=Person, 3=Exit)
        self.grid_data = np.zeros((ROWS, COLS), dtype=int)
        self.setup_floor_plan() # Draw walls
        self.S_matrix = np.zeros((ROWS, COLS), dtype=float) # Static field
        self.D_matrix = np.zeros((ROWS, COLS), dtype=float) # Dynamic field
        self.calculate_static_floor_field()
        # 2. CREATE UI LAYOUT
        self.create_layout()
        
        # 3. INITIAL DRAW
        self.draw_grid()

    def create_layout(self):
        # --- LEFT PANEL (CONTROLS) ---
        self.panel_left = tk.Frame(self.root, width=200, bg="#f0f0f0", padx=10, pady=10)
        self.panel_left.pack(side=tk.LEFT, fill=tk.Y)
        
        # Title
        tk.Label(self.panel_left, text="CA Parameters", font=("Arial", 12, "bold"), bg="#f0f0f0").pack(pady=(0, 20))
        # Change these lines in create_layout:
        self.entry_density = self.add_input("Density", "10")
        self.entry_diff_s = self.add_input("Diffusion S", "0.1")
        self.entry_decay = self.add_input("Decay", "0.3")
        self.entry_ks = self.add_input("Ks", "2")
        self.entry_kd = self.add_input("Kd", "1")
        self.entry_steps = self.add_input("Time Steps", "200")

        # Separator
        ttk.Separator(self.panel_left, orient='horizontal').pack(fill='x', pady=20)

        # Buttons
        self.btn_gen = tk.Button(self.panel_left, text="Generate", command=self.generate_people, 
                                 bg="white", width=15, pady=5)
        self.btn_gen.pack(pady=5)

        self.btn_start = tk.Button(self.panel_left, text="Start", command=self.start_simulation, 
                                   bg="#dddddd", width=15, pady=5)
        self.btn_start.pack(pady=5)

        self.btn_stop = tk.Button(self.panel_left, text="Stop", command=self.stop_simulation, 
                                  bg="#dddddd", width=15, pady=5)
        self.btn_stop.pack(pady=5)
        
        # Stats Label
        self.lbl_stats = tk.Label(self.panel_left, text="Total Agents: 0", bg="#f0f0f0", font=("Arial", 10))
        self.lbl_stats.pack(side=tk.BOTTOM, pady=20)

        # --- RIGHT PANEL (CANVAS / MAP) ---
        self.panel_right = tk.Frame(self.root, bg="white")
        self.panel_right.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        
        # Title label for map
        tk.Label(self.panel_right, text="Simulation of Evacuation in the Building", 
                 font=("Arial", 14, "bold"), fg="blue", bg="white").pack(pady=10)

        # The Canvas (The Grid)
        self.canvas = tk.Canvas(self.panel_right, bg="white", width=COLS*GRID_SIZE, height=ROWS*GRID_SIZE)
        self.canvas.pack(padx=20, pady=20)
        
        # Bind Click to Toggle Wall (Optional feature)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

    def add_input(self, label_text, default_val):
        """Helper to make the input boxes look nice"""
        frame = tk.Frame(self.panel_left, bg="#f0f0f0")
        frame.pack(fill=tk.X, pady=2)
        tk.Label(frame, text=label_text, width=10, anchor="w", bg="#f0f0f0").pack(side=tk.LEFT)
        entry = tk.Entry(frame, width=8)
        entry.insert(0, default_val)
        entry.pack(side=tk.RIGHT)
        return entry # --- ADD THIS RETURN LINE ---
    
    def setup_floor_plan(self):
        """Draws a dummy floor plan with rooms"""
        # Reset
        self.grid_data = np.zeros((ROWS, COLS), dtype=int)
        
        # 1. Outer Walls
        self.grid_data[0, :] = 1
        self.grid_data[ROWS-1, :] = 1
        self.grid_data[:, 0] = 1
        self.grid_data[:, COLS-1] = 1
        
        # 2. Internal Walls (Creating Rooms)
        # Vertical wall in middle
        self.grid_data[5:25, 20] = 1
        
        # Horizontal walls (Rooms on left)
        self.grid_data[10, 1:20] = 1
        self.grid_data[20, 1:20] = 1
        
        # Horizontal walls (Rooms on right)
        self.grid_data[15, 20:39] = 1
        
        # 3. Doors (Punch holes in walls)
        self.grid_data[10, 10:13] = 0 # Door Room 1
        self.grid_data[20, 10:13] = 0 # Door Room 2
        self.grid_data[15, 25:28] = 0 # Door Room 3
        self.grid_data[12:15, 20] = 0 # Door Corridor
        
        # 4. Exits
        self.grid_data[ROWS-1, 18:22] = 3 # Exit at bottom

    def draw_grid(self):
        """Renders the grid_data to the canvas"""
        self.canvas.delete("all")
        
        # Draw Grid Lines
        for r in range(ROWS + 1):
            self.canvas.create_line(0, r*GRID_SIZE, COLS*GRID_SIZE, r*GRID_SIZE, fill=COLOR_GRID)
        for c in range(COLS + 1):
            self.canvas.create_line(c*GRID_SIZE, 0, c*GRID_SIZE, ROWS*GRID_SIZE, fill=COLOR_GRID)

        # Draw Objects
        for r in range(ROWS):
            for c in range(COLS):
                val = self.grid_data[r, c]
                x1, y1 = c*GRID_SIZE, r*GRID_SIZE
                x2, y2 = x1+GRID_SIZE, y1+GRID_SIZE
                
                if val == 1: # Wall
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLOR_WALL, outline="")
                elif val == 2: # Person
                    # Draw a smaller dot for person
                    pad = 4
                    self.canvas.create_oval(x1+pad, y1+pad, x2-pad, y2-pad, fill=COLOR_AGENT, outline="")
                elif val == 3: # Exit
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLOR_EXIT, outline="")

    def generate_people(self):
        """Logic for the Generate Button"""
        # Clear existing people first? 
        # self.grid_data[self.grid_data == 2] = 0
        
        # Add 50 random people in empty spaces
        count = 0
        while count < 50:
            r = random.randint(1, ROWS-2)
            c = random.randint(1, COLS-2)
            if self.grid_data[r, c] == 0:
                self.grid_data[r, c] = 2
                count += 1
                
        self.lbl_stats.config(text=f"Total Agents: {np.sum(self.grid_data == 2)}")
        self.calculate_static_floor_field()
        self.draw_grid()

    def start_simulation(self):
            # Rerun the pathfinding (Static Floor Field) before starting
            self.calculate_static_floor_field() 
            
            self.is_running = True
            self.btn_start.config(bg="#90EE90") # Light green
            self.run_step()

    def stop_simulation(self):
        self.is_running = False
        self.btn_start.config(bg="#dddddd")

    def run_step(self):
        if not self.is_running:
            return

        current_agents = np.argwhere(self.grid_data == 2)
        
        try:
            ks = float(self.entry_ks.get())
            kd = float(self.entry_kd.get())
            decay = float(self.entry_decay.get())
        except (AttributeError, ValueError):
            ks, kd, decay = 2.0, 1.0, 0.3

        # Matrik C: Menyimpan target grid dan siapa saja yang ingin ke sana (untuk cek konflik)
        # Format: {(baris_target, kolom_target):[(baris_agen, kolom_agen, nilai_Tij), ...]}
        matrik_c = {} 
        
        # ==========================================
        # FASE 1: PEMBUATAN MATRIK T (Stochastic Probability)
        # ==========================================
        for r, c in current_agents:
            # 9 Arah (Moore Neighborhood)
            moves =[
                (-1, 0), (-1, -1), (0, -1), (1, -1), 
                (0, 0), (1, 0), (1, 1), (0, 1), (-1, 1)
            ]
            
            weights = []
            valid_targets =[]
            
            for dr, dc in moves:
                nr, nc = r + dr, c + dc
                
                # Check batas dinding
                if 0 <= nr < ROWS and 0 <= nc < COLS:
                    # Cek apakah terisi dinding (1) atau orang lain (2)
                    is_occupied = 1 if (self.grid_data[nr, nc] in [1, 2]) else 0
                    
                    # Boleh memilih diam di tempat
                    if dr == 0 and dc == 0:
                        is_occupied = 0 
                        
                    if is_occupied == 0:
                        s_val = self.S_matrix[nr, nc]
                        d_val = self.D_matrix[nr, nc]
                        
                        # Hitung bobot peluang (bukan sekadar nilai mutlak)
                        weight = np.exp(kd * d_val) * np.exp(ks * s_val)
                        weights.append(weight)
                        valid_targets.append((nr, nc))

            total_weight = sum(weights)
            
            if total_weight > 0:
                # === STOCHASTIC MAGIC HAPPENS HERE ===
                # Gunakan 'weights' sebagai probabilitas. Agen akan lebih sering
                # memilih nilai tinggi, tapi masih bisa "tersandung/geser" ke nilai rendah.
                pilihan = random.choices(valid_targets, weights=weights, k=1)[0]
                target_r, target_c = pilihan
            else:
                # Jika terhalang sempurna di segala sisi, diam di tempat
                target_r, target_c = r, c
                
            # Simpan tujuan ke Matrik C (Kita tidak perlu lagi menyimpan nilai T)
            target = (target_r, target_c)
            if target not in matrik_c:
                matrik_c[target] =[]
            matrik_c[target].append((r, c))       

        # ==========================================
        # FASE 2: RESOLUSI KONFLIK & PARALEL (Stochastic)
        # ==========================================
        new_grid = np.zeros_like(self.grid_data)
        new_grid[self.grid_data == 1] = 1 # Dinding tetap
        new_grid[self.grid_data == 3] = 3 # Pintu keluar tetap
        
        # Evaluasi semua pergerakan secara paralel
        for target, daftar_agen in matrik_c.items():
            target_r, target_c = target
            
            # Jika target adalah Pintu Keluar, keluarkan agen
            if self.grid_data[target_r, target_c] == 3:
                for (agen_r, agen_c) in daftar_agen:
                    self.D_matrix[agen_r, agen_c] += 1
                continue
                
            # === STOCHASTIC CONFLICT RESOLUTION ===
            # Jika ada lebih dari 1 agen yang ingin ke grid ini, pilih pemenang secara acak!
            pemenang = random.choice(daftar_agen)
            pemenang_r, pemenang_c = pemenang
            
            # Pemenang menempati grid tujuan
            new_grid[target_r, target_c] = 2 
            
            # Pemenang meninggalkan jejak (D -> D+1) jika dia berpindah
            if (pemenang_r, pemenang_c) != (target_r, target_c):
                self.D_matrix[pemenang_r, pemenang_c] += 1
                
            # Yang kalah konflik gagal bergerak, harus tetap di tempat asalnya
            for agen in daftar_agen:
                if agen != pemenang:
                    kalah_r, kalah_c = agen
                    new_grid[kalah_r, kalah_c] = 2

        # Fase Decay (Pelemahan jejak)
        self.D_matrix *= (1 - decay)
        
        # Update UI
        self.grid_data = new_grid
        self.draw_grid()
        self.lbl_stats.config(text=f"Total Agents: {np.sum(self.grid_data == 2)}")
        self.root.after(100, self.run_step)

    def on_canvas_click(self, event):
        """Optional: Click to add/remove walls manually"""
        c = event.x // GRID_SIZE
        r = event.y // GRID_SIZE
        if 0 <= r < ROWS and 0 <= c < COLS:
            if self.grid_data[r, c] == 1:
                self.grid_data[r, c] = 0
            elif self.grid_data[r, c] == 0:
                self.grid_data[r, c] = 1
            self.draw_grid()

    def calculate_static_floor_field(self):
            """Calculates the static field using BFS (flows around walls)."""
            # 1. Initialize with a very high distance (infinity)
            self.S_matrix = np.full((ROWS, COLS), -1.0, dtype=float)
            
            # 2. Find all exit coordinates and set their distance to 0
            exits = np.argwhere(self.grid_data == 3)
            queue = []
            for r, c in exits:
                self.S_matrix[r, c] = 0
                queue.append((r, c))
                
            # 3. Spread 'water' from exits to all reachable cells
            while queue:
                r, c = queue.pop(0)
                current_dist = self.S_matrix[r, c]
                
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    
                    # Check bounds and ensure it's not a wall
                    if 0 <= nr < ROWS and 0 <= nc < COLS and self.grid_data[nr, nc] != 1:
                        # If this cell hasn't been visited yet
                        if self.S_matrix[nr, nc] == -1:
                            self.S_matrix[nr, nc] = current_dist + 1
                            queue.append((nr, nc))

            # 4. Normalize: Flip it so higher values are closer to exit
            max_val = np.max(self.S_matrix)
            # Cells that can't reach the exit stay at 0 attractiveness
            self.S_matrix = np.where(self.S_matrix == -1, 0, max_val - self.S_matrix)# --- MAIN ---



if __name__ == "__main__":
    root = tk.Tk()
    app = PedestrianEvacuationUI(root)
    root.mainloop()
