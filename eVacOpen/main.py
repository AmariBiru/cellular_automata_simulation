# main.py
import tkinter as tk
from core.environment import Environment
from core.simulation import FluidDynamicsModel
from editor.tools import ToolManager
from ui.main_window import UnifiedEvacuationUI

def setup_initial_map(env):
    """A basic box layout to start with."""
    for c in range(env.cols):
        env.set_cell(0, c, 1)
        env.set_cell(env.rows-1, c, 1)
    for r in range(env.rows):
        env.set_cell(r, 0, 1)
        env.set_cell(r, env.cols-1, 1)

if __name__ == "__main__":
    env = Environment()
    setup_initial_map(env)
    
    tools = ToolManager(env)
    sim = FluidDynamicsModel(env)
    
    root = tk.Tk()
    app = UnifiedEvacuationUI(root, env, tools, sim)
    root.mainloop()