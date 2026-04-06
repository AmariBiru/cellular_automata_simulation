# ui/main_window.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import config

class UnifiedEvacuationUI:
    def __init__(self, root, env, tools, sim):
        self.root = root
        self.env = env
        self.tools = tools
        self.sim = sim
        
        self.root.title("eVacOpen - Modular Simulator")
        self.root.geometry("1250x800") 
        self.is_running = False
        
        self.show_grid_var = tk.BooleanVar(value=True)
        self.current_save_file = None
        
        self.create_menu()
        self.create_layout()
        self.sim.recalculate_maps()
        self.draw_grid()
    # Ruler tool
    def select_tool(self, mode):
        self.tools.set_mode(mode)
        self.ruler_step = 0 # Reset ruler state
        self.ruler_start = (0, 0)
        self.ruler_end = (0, 0)
        self.draw_grid() # Redraw to clear any leftover rulers
    def create_menu(self):
        self.menubar = tk.Menu(self.root)

        # --- FILE MENU ---
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_separator()
        file_menu.add_command(label="Open Project...", command=self.open_project, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Project", command=self.save_project, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.save_project_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        self.menubar.add_cascade(label="File", menu=file_menu)

        # --- EDIT MENU ---
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Clear Map (Keep Agents)", command=self.clear_map)
        edit_menu.add_command(label="Clear Agents", command=self.clear_agents)
        self.menubar.add_cascade(label="Edit", menu=edit_menu)

        # --- VIEW & SIMULATION MENU ---
        view_menu = tk.Menu(self.menubar, tearoff=0)
        view_menu.add_checkbutton(label="Show Grid", variable=self.show_grid_var, command=self.draw_grid)
        self.menubar.add_cascade(label="View", menu=view_menu)

        sim_menu = tk.Menu(self.menubar, tearoff=0)
        sim_menu.add_command(label="Play", command=self.start_simulation)
        sim_menu.add_command(label="Stop", command=self.stop_simulation)
        sim_menu.add_separator()
        sim_menu.add_command(label="Step Forward (1 Frame)", command=self.step_simulation)
        self.menubar.add_cascade(label="Simulation", menu=sim_menu)

        self.root.config(menu=self.menubar)

        # --- SETTINGS MENU ---
        settings_menu = tk.Menu(self.menubar, tearoff=0)
        settings_menu.add_command(label="Preferences...", command=self.open_preferences)
        self.menubar.add_cascade(label="Settings", menu=settings_menu)

        # --- HELP MENU ---
        help_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu.add_command(label="About eVacOpen", command=self.show_about)
        self.menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=self.menubar) # <--- This line is already here!
        # KEYBOARD SHORTCUTS
        self.root.bind('<Control-s>', lambda event: self.save_project())
        self.root.bind('<Control-o>', lambda event: self.open_project())
        self.root.bind('<Control-z>', lambda event: self.undo())
        self.root.bind('<Control-Z>', lambda event: self.undo()) # Catch caps lock
        self.root.bind('<Control-y>', lambda event: self.redo())
        self.root.bind('<Control-Y>', lambda event: self.redo())

    # --- UNDO / REDO LOGIC ---
    def undo(self):
        if self.env.undo():
            self.sim.recalculate_maps()
            self.draw_grid()

    def redo(self):
        if self.env.redo():
            self.sim.recalculate_maps()
            self.draw_grid()

    # --- FILE & EDIT LOGIC ---
    def new_project(self):
        if messagebox.askyesno("New Project", "Are you sure? Unsaved changes will be lost."):
            self.env.begin_transaction()
            self.env.static_grid.fill(0)
            self.env.clear_agents()
            self.env.commit_transaction()
            self.current_save_file = None
            self.draw_grid()

    def open_project(self):
        filepath = filedialog.askopenfilename(initialdir="data/saves", filetypes=[("Evac Files", "*.evac"), ("All Files", "*.*")])
        if filepath:
            self.env.load_from_file(filepath)
            self.sim.recalculate_maps()
            self.draw_grid()
            self.current_save_file = filepath

    def save_project(self):
        if not self.current_save_file: self.save_project_as()
        else: self.env.save_to_file(self.current_save_file)

    def save_project_as(self):
        filepath = filedialog.asksaveasfilename(initialdir="data/saves", defaultextension=".evac", filetypes=[("Evac Files", "*.evac")])
        if filepath:
            self.env.save_to_file(filepath)
            self.current_save_file = filepath

    def clear_map(self):
        self.env.begin_transaction()
        for r in range(config.ROWS):
            for c in range(config.COLS):
                self.env.set_cell(r, c, 0)
        self.env.commit_transaction()
        self.draw_grid()

    def clear_agents(self):
        self.env.begin_transaction()
        self.env.clear_agents()
        self.env.commit_transaction()
        self.draw_grid()
        
    def open_preferences(self):
        messagebox.showinfo("Settings", "This is where we will add the Grid Size and Color UI later!")

    def show_about(self):
        messagebox.showinfo("About", "eVacOpen v1.0\nModular Evacuation Simulator\n\nDesigned for safe evacuation testing.")

    # --- UI LAYOUT ---
    def create_layout(self):
        self.panel_left = tk.Frame(self.root, width=200, bg="#f0f0f0", padx=10, pady=10)
        self.panel_left.pack(side=tk.LEFT, fill=tk.Y)
        
        tk.Button(self.panel_left, text="Wall", bg=config.COLOR_WALL, fg="white", command=lambda: self.tools.set_mode(config.MODE_WALL)).pack(fill='x', pady=2)
        tk.Button(self.panel_left, text="Door", bg=config.COLOR_DOOR, fg="black", command=lambda: self.tools.set_mode(config.MODE_DOOR)).pack(fill='x', pady=2)
        tk.Button(self.panel_left, text="Exit", bg=config.COLOR_EXIT, fg="white", command=lambda: self.tools.set_mode(config.MODE_EXIT)).pack(fill='x', pady=2)
        tk.Button(self.panel_left, text="Agent", bg=config.COLOR_AGENT, fg="white", command=lambda: self.tools.set_mode(config.MODE_AGENT)).pack(fill='x', pady=2)
        tk.Button(self.panel_left, text="Erase", bg=config.COLOR_BG, fg="black", command=lambda: self.tools.set_mode(config.MODE_ERASE)).pack(fill='x', pady=2)
        tk.Button(self.panel_left, text="Ruler", bg="#ADD8E6", fg="black", command=lambda: self.select_tool(config.MODE_RULER)).pack(fill='x', pady=2)        
        
        ttk.Separator(self.panel_left, orient='horizontal').pack(fill='x', pady=10)
        
        self.entry_visc = self.add_input("Viscosity", "0.2")
        self.entry_ks = self.add_input("Ks Spread", "2.5")

        self.btn_gen = tk.Button(self.panel_left, text="Generate Agents", command=self.generate_people)
        self.btn_gen.pack(fill='x', pady=5)
        
        self.btn_start = tk.Button(self.panel_left, text="Start", bg="#90EE90", command=self.start_simulation)
        self.btn_start.pack(fill='x', pady=5)
        self.btn_stop = tk.Button(self.panel_left, text="Stop", bg="#FFB6C1", command=self.stop_simulation)
        self.btn_stop.pack(fill='x', pady=5)
        
        self.lbl_stats = tk.Label(self.panel_left, text="Total Agents: 0", bg="#f0f0f0")
        self.lbl_stats.pack(side=tk.BOTTOM, pady=20)

        self.panel_right = tk.Frame(self.root, bg="white")
        self.panel_right.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        self.canvas = tk.Canvas(self.panel_right, bg="white", width=config.COLS*config.GRID_SIZE, height=config.ROWS*config.GRID_SIZE)
        self.canvas.pack(padx=20, pady=20)
        
        # --- MOUSE TRACKERS ---
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.canvas.bind("<Motion>", self.on_mouse_hover) 

    def add_input(self, label_text, default_val):
        frame = tk.Frame(self.panel_left, bg="#f0f0f0")
        frame.pack(fill=tk.X, pady=2)
        tk.Label(frame, text=label_text, width=10, anchor="w", bg="#f0f0f0").pack(side=tk.LEFT)
        entry = tk.Entry(frame, width=5)
        entry.insert(0, default_val)
        entry.pack(side=tk.RIGHT)
        return entry 

    # ==========================================
    # CANVAS DRAWING & RULER LOGIC
    # ==========================================
    def on_mouse_down(self, event):
        # --- RULER 2-CLICK LOGIC ---
        if self.tools.current_mode == config.MODE_RULER:
            if not hasattr(self, 'ruler_step') or self.ruler_step == 0:
                # First Click: Drop Pin A
                self.ruler_start = (event.x, event.y)
                self.ruler_step = 1
            else:
                # Second Click: Drop Pin B & Lock it
                x2, y2 = event.x, event.y
                if event.state & 0x0001: # SHIFT-SNAP for Ruler
                    x1, y1 = self.ruler_start
                    if abs(x2 - x1) > abs(y2 - y1): y2 = y1
                    else: x2 = x1
                self.ruler_end = (x2, y2)
                self.ruler_step = 0
                self.draw_grid() # Redraw to bake the red line in
            return

        # --- NORMAL DRAWING LOGIC ---
        c, r = event.x // config.GRID_SIZE, event.y // config.GRID_SIZE
        self.drag_start_r = r
        self.drag_start_c = c
        self.drag_axis = None
        
        self.env.begin_transaction()
        self.on_mouse_drag(event)

    def on_mouse_hover(self, event):
        # Draws the blue dashed preview line when moving the mouse
        if self.tools.current_mode == config.MODE_RULER and getattr(self, 'ruler_step', 0) == 1:
            self.canvas.delete("ruler_preview") # Erase old preview frame
            
            x1, y1 = self.ruler_start
            x2, y2 = event.x, event.y
            
            if event.state & 0x0001: # SHIFT-SNAP for Preview
                if abs(x2 - x1) > abs(y2 - y1): y2 = y1
                else: x2 = x1
                
            self.canvas.create_line(x1, y1, x2, y2, fill="blue", dash=(4, 4), width=2, tags="ruler_preview")
            dist = (((x2 - x1)/config.GRID_SIZE)**2 + ((y2 - y1)/config.GRID_SIZE)**2) ** 0.5
            self.canvas.create_text((x1+x2)/2, (y1+y2)/2 - 15, text=f"{dist:.1f}m", fill="blue", font=("Arial", 12, "bold"), tags="ruler_preview")

    def on_mouse_drag(self, event):
        if self.tools.current_mode == config.MODE_RULER: return
        
        c, r = event.x // config.GRID_SIZE, event.y // config.GRID_SIZE

        # Check if Shift key is being held down (Event State bit 0)
        if event.state & 0x0001:
            if self.drag_axis is None:
                if r != self.drag_start_r: self.drag_axis = 'vertical'
                elif c != self.drag_start_c: self.drag_axis = 'horizontal'
            
            if self.drag_axis == 'vertical': c = self.drag_start_c
            elif self.drag_axis == 'horizontal': r = self.drag_start_r

        if self.tools.apply_tool(r, c):
            self.draw_grid()

    def on_mouse_release(self, event):
        if self.tools.current_mode == config.MODE_RULER: return
        self.env.commit_transaction()
        self.sim.recalculate_maps()

    def generate_people(self):
        self.env.begin_transaction()
        for _ in range(50):
            r, c = random.randint(1, config.ROWS-2), random.randint(1, config.COLS-2)
            if self.env.get_cell(r, c) == 0:
                self.env.add_agent(r, c)
        self.env.commit_transaction()
        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")
        for r in range(config.ROWS):
            for c in range(config.COLS):
                val = self.env.get_cell(r, c)
                x1, y1 = c*config.GRID_SIZE, r*config.GRID_SIZE
                x2, y2 = x1+config.GRID_SIZE, y1+config.GRID_SIZE
                
                heat = self.sim.heatmap_matrix[r, c]
                if heat > 0.2 and val == 0:
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="#ffcccc", outline="")
                
                if val == config.MODE_WALL: self.canvas.create_rectangle(x1, y1, x2, y2, fill=config.COLOR_WALL, outline="")
                elif val == config.MODE_EXIT: self.canvas.create_rectangle(x1, y1, x2, y2, fill=config.COLOR_EXIT, outline="")
                elif val == config.MODE_DOOR: self.canvas.create_rectangle(x1, y1, x2, y2, fill=config.COLOR_DOOR, outline="")

        if self.show_grid_var.get():
            for r in range(config.ROWS + 1): self.canvas.create_line(0, r*config.GRID_SIZE, config.COLS*config.GRID_SIZE, r*config.GRID_SIZE, fill=config.COLOR_GRID)
            for c in range(config.COLS + 1): self.canvas.create_line(c*config.GRID_SIZE, 0, c*config.GRID_SIZE, config.ROWS*config.GRID_SIZE, fill=config.COLOR_GRID)

        for agent in self.env.agents:
            x1, y1 = agent.c*config.GRID_SIZE, agent.r*config.GRID_SIZE
            pad = 4
            self.canvas.create_oval(x1+pad, y1+pad, x1+config.GRID_SIZE-pad, y1+config.GRID_SIZE-pad, fill=config.COLOR_AGENT, outline="")

        self.lbl_stats.config(text=f"Total Agents: {len(self.env.agents)}")

        # ==========================================
        # NEW: DRAW THE LOCKED RULER (RED LINE)
        # ==========================================
        if self.tools.current_mode == config.MODE_RULER and getattr(self, 'ruler_step', 0) == 0:
            if hasattr(self, 'ruler_start') and hasattr(self, 'ruler_end'):
                x1, y1 = self.ruler_start
                x2, y2 = self.ruler_end
                if (x1, y1) != (x2, y2): # Make sure it's an actual line, not just a dot
                    self.canvas.create_line(x1, y1, x2, y2, fill="red", width=2)
                    # Calculate distance
                    dist = (((x2 - x1)/config.GRID_SIZE)**2 + ((y2 - y1)/config.GRID_SIZE)**2) ** 0.5
                    # Draw text label above the center of the line
                    self.canvas.create_text((x1+x2)/2, (y1+y2)/2 - 15, text=f"{dist:.1f}m", fill="red", font=("Arial", 12, "bold"))
    # --- SIMULATION ---
    def step_simulation(self):
        self.sim.run_step()
        self.draw_grid()
        
    def start_simulation(self):
        try:
            self.sim.visc = float(self.entry_visc.get())
            self.sim.ks = float(self.entry_ks.get())
        except ValueError: pass
        self.sim.recalculate_maps()
        self.is_running = True
        self.run_loop()

    def stop_simulation(self):
        self.is_running = False

    def run_loop(self):
        if not self.is_running: return
        should_continue = self.sim.run_step() 
        self.draw_grid()
        if should_continue: self.root.after(100, self.run_loop)
        else: self.is_running = False