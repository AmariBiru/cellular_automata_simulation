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
        self.root.geometry("1000x700") # Window size

        self.is_running = False
        
        # 1. Init Data Grid (0=Empty, 1=Wall, 2=Person, 3=Exit)
        self.grid_data = np.zeros((ROWS, COLS), dtype=int)
        self.setup_floor_plan() # Draw walls
        self.S_matrix = np.zeros((ROWS, COLS), dtype=float) # Static field
        self.D_matrix = np.zeros((ROWS, COLS), dtype=float) # Dynamic field
        self.heatmap_matrix = np.zeros((ROWS, COLS), dtype=float)
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
        self.entry_ks = self.add_input("Ks", "5")
        self.entry_kd = self.add_input("Kd", "0.5")
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
        """Renders the grid_data and the Heatmap to the canvas"""
        self.canvas.delete("all")
        
        # 1. DRAW HEATMAP FLOOR
        for r in range(ROWS):
            for c in range(COLS):
                val = self.grid_data[r, c]
                if val not in [1, 3]: # Don't paint walls or exits
                    heat = self.heatmap_matrix[r, c]
                    if heat > 0.2:
                        x1, y1 = c*GRID_SIZE, r*GRID_SIZE
                        x2, y2 = x1+GRID_SIZE, y1+GRID_SIZE
                        color = self.get_heat_color(heat)
                        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

        # 2. DRAW GRID LINES
        for r in range(ROWS + 1):
            self.canvas.create_line(0, r*GRID_SIZE, COLS*GRID_SIZE, r*GRID_SIZE, fill=COLOR_GRID)
        for c in range(COLS + 1):
            self.canvas.create_line(c*GRID_SIZE, 0, c*GRID_SIZE, ROWS*GRID_SIZE, fill=COLOR_GRID)

        # 3. DRAW WALLS, EXITS, AND AGENTS
        for r in range(ROWS):
            for c in range(COLS):
                val = self.grid_data[r, c]
                x1, y1 = c*GRID_SIZE, r*GRID_SIZE
                x2, y2 = x1+GRID_SIZE, y1+GRID_SIZE
                
                if val == 1: # Wall
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLOR_WALL, outline="")
                elif val == 3: # Exit
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLOR_EXIT, outline="")
                elif val == 2: # Person (Keep them Royal Blue to contrast with the Red floor)
                    pad = 4
                    self.canvas.create_oval(x1+pad, y1+pad, x2-pad, y2-pad, fill=COLOR_AGENT, outline="")

    def get_heat_color(self, heat_val):
        """Converts a heat value into a color gradient (White -> Yellow -> Red)"""
        if heat_val <= 0.2: 
            return "#FFFFFF" # White (Empty/Cool)
            
        # Cap maximum heat at 15.0 for the brightest Red
        ratio = min(heat_val / 15.0, 1.0) 
        
        if ratio < 0.5:
            # Transition: White -> Yellow
            b = int(255 * (1.0 - (ratio * 2)))
            b = max(0, min(255, b))
            return f"#ff{255:02x}{b:02x}"
        else:
            # Transition: Yellow -> Red
            g = int(255 * (1.0 - ((ratio - 0.5) * 2)))
            g = max(0, min(255, g))
            return f"#ff{g:02x}00"

    def generate_people(self):
        """Logic for the Generate Button"""
        # Clear existing people first? 
        # self.grid_data[self.grid_data == 2] = 0

        # Clear Congestion HeatMap
        self.heatmap_matrix = np.zeros((ROWS, COLS), dtype=float)
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
            matrik_c = {} 
            
            # --- DISCRETE SOCIAL FORCE WEIGHTS ---
            # (You could map these to your UI inputs later)
            W_DRIVE = 10.0      # How badly they want to exit
            W_REP_AGENT = 1.5  # How much they avoid each other
            W_REP_WALL = 2.0   # How much they avoid walls

            # ==========================================
            # FASE 1: CALCULATE FORCES & CHOOSE CELL
            # ==========================================
            for r, c in current_agents:
                f_drive = np.array([0.0, 0.0])
                f_rep_agent = np.array([0.0, 0.0])
                f_rep_wall = np.array([0.0, 0.0])
                
                # 1. DRIVING FORCE (Look at S_matrix to find where the exit is)
                best_s = -1
                for dr, dc in[(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < ROWS and 0 <= nc < COLS:
                        if self.S_matrix[nr, nc] > best_s:
                            best_s = self.S_matrix[nr, nc]
                            # Vector pointing towards the best S_matrix value
                            f_drive = np.array([dr, dc], dtype=float)
                
                # Normalize driving force vector
                if np.linalg.norm(f_drive) > 0:
                    f_drive = (f_drive / np.linalg.norm(f_drive)) * W_DRIVE

                # 2. REPULSIVE FORCES (Scan a 5x5 neighborhood around the agent)
                for dr in range(-2, 3):
                    for dc in range(-2, 3):
                        if dr == 0 and dc == 0:
                            continue
                            
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < ROWS and 0 <= nc < COLS:
                            dist = math.sqrt(dr**2 + dc**2)
                            
                            # Vector pointing AWAY from the obstacle
                            direction = np.array([-dr, -dc], dtype=float)
                            direction = direction / dist # Normalize
                            
                            # The closer the obstacle, the stronger the force (Inverse square law)
                            force_magnitude = 1.0 / (dist ** 2)
                            
                            if self.grid_data[nr, nc] == 2: # Repelled by Agent
                                f_rep_agent += direction * force_magnitude * W_REP_AGENT
                            elif self.grid_data[nr, nc] == 1: # Repelled by Wall
                                f_rep_wall += direction * force_magnitude * W_REP_WALL

                # 3. TOTAL FORCE
                F_total = f_drive + f_rep_agent + f_rep_wall

                # 4. CHOOSE THE BEST NEIGHBORING CELL BASED ON TOTAL FORCE
                moves =[
                    (-1, 0), (-1, -1), (0, -1), (1, -1), 
                    (0, 0), (1, 0), (1, 1), (0, 1), (-1, 1)
                ]
                
                best_target = (r, c)
                max_score = -float('inf')

                for dr, dc in moves:
                    nr, nc = r + dr, c + dc
                    # Check bounds
                    if 0 <= nr < ROWS and 0 <= nc < COLS:
                        # Make sure cell is empty or an exit
                        if self.grid_data[nr, nc] in [0, 3] or (dr == 0 and dc == 0):
                            move_vec = np.array([dr, dc], dtype=float)
                            
                            if dr == 0 and dc == 0:
                                score = 0.0 # Score for staying still
                            else:
                                # Normalize move vector
                                move_vec = move_vec / np.linalg.norm(move_vec)
                                
                                # DOT PRODUCT: Calculates how closely the cell's direction
                                # aligns with the F_total vector arrow.
                                score = np.dot(F_total, move_vec)
                                
                            # Add a tiny bit of randomness (Stochasticity) so they don't get stuck in loops
                            score += random.uniform(-0.5, 0.5)

                            if score > max_score:
                                max_score = score
                                best_target = (nr, nc)

                # Store the desired target
                if best_target not in matrik_c:
                    matrik_c[best_target] =[]
                matrik_c[best_target].append((r, c))

            # ==========================================
            # FASE 2: RESOLUSI KONFLIK (Remains exactly the same)
            # ==========================================
            new_grid = np.zeros_like(self.grid_data)
            new_grid[self.grid_data == 1] = 1 # Keep Walls
            new_grid[self.grid_data == 3] = 3 # Keep Exits
            
            for target, daftar_agen in matrik_c.items():
                target_r, target_c = target
                
                if self.grid_data[target_r, target_c] == 3:
                    continue # Agent exits building
                    
                pemenang = random.choice(daftar_agen)
                pemenang_r, pemenang_c = pemenang
                
                new_grid[target_r, target_c] = 2 
                    
                for agen in daftar_agen:
                    if agen != pemenang:
                        kalah_r, kalah_c = agen
                        new_grid[kalah_r, kalah_c] = 2

            self.grid_data = new_grid
            
            # ==========================================
            # UPDATE CONGESTION HEATMAP
            # ==========================================
            # 1. Add heat based on current agent positions
            current_agents_new = np.argwhere(self.grid_data == 2)
            for r, c in current_agents_new:
                # Heat up the cell the agent is in, and a tiny bit around them
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < ROWS and 0 <= nc < COLS and self.grid_data[nr, nc] != 1:
                            # Center gets +2.0 heat, surrounding gets +0.5 heat
                            added_heat = 2.0 if (dr == 0 and dc == 0) else 0.5
                            self.heatmap_matrix[nr, nc] += added_heat
                            
            # 2. Decay the heat by 15% every step so moving agents leave a fading trail
            self.heatmap_matrix *= 0.85 
            # ==========================================

            self.draw_grid()
            self.lbl_stats.config(text=f"Total Agents: {np.sum(self.grid_data == 2)}")
            
            if np.sum(self.grid_data == 2) > 0:
                self.root.after(100, self.run_step)
            else:
                self.stop_simulation()
                self.draw_grid()
                self.lbl_stats.config(text=f"Total Agents: {np.sum(self.grid_data == 2)}")
                
                # Stop simulation if everyone has exited
                if np.sum(self.grid_data == 2) > 0:
                    self.root.after(100, self.run_step)
                else:
                    self.stop_simulation()


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
