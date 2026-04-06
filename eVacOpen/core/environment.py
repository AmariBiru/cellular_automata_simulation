# core/environment.py
import numpy as np
from core.entity import Agent
import config
import json

class Environment:
    def __init__(self):
        self.rows = config.ROWS
        self.cols = config.COLS
        self.static_grid = np.zeros((self.rows, self.cols), dtype=int)
        self.agents = []
        self.next_agent_id = 0
        
        # --- EFFICIENT DELTA TRACKING (UNDO/REDO) ---
        self.history = []
        self.history_index = -1
        self.current_transaction = None

    # ==========================================
    # TRANSACTION ENGINE
    # ==========================================
    def begin_transaction(self):
        """Starts recording changes when the mouse clicks down."""
        self.current_transaction = []

    def commit_transaction(self):
        """Saves the recorded changes to history when the mouse lets go."""
        if self.current_transaction: # Only save if we actually drew something
            # Erase "future" history if we undo and then draw something new
            self.history = self.history[:self.history_index + 1]
            
            self.history.append(self.current_transaction)
            self.history_index += 1
            self.current_transaction = None

            # Limit history to 100 actions so we don't use up all RAM
            if len(self.history) > 100: 
                self.history.pop(0)
                self.history_index -= 1
        else:
            self.current_transaction = None

    # ==========================================
    # GRID AND AGENT MODIFIERS
    # ==========================================
    def get_cell(self, r, c):
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return self.static_grid[r, c]
        return None

    def set_cell(self, r, c, val):
        if 0 <= r < self.rows and 0 <= c < self.cols:
            old_val = self.static_grid[r, c]
            if old_val != val: # Only record if the cell actually changed
                if self.current_transaction is not None:
                    self.current_transaction.append({"type": "cell", "r": r, "c": c, "old": old_val, "new": val})
                self.static_grid[r, c] = val

    def add_agent(self, r, c):
        if any(a.r == r and a.c == c for a in self.agents): return
        agent = Agent(self.next_agent_id, r, c)
        
        if self.current_transaction is not None:
            self.current_transaction.append({"type": "add_agent", "agent": agent})
            
        self.agents.append(agent)
        self.next_agent_id += 1

    def remove_agent_at(self, r, c):
        for a in self.agents:
            if a.r == r and a.c == c:
                if self.current_transaction is not None:
                    self.current_transaction.append({"type": "remove_agent", "agent": a})
                self.agents.remove(a)
                return

    def remove_agent(self, agent):
        if agent in self.agents:
            if self.current_transaction is not None:
                self.current_transaction.append({"type": "remove_agent", "agent": agent})
            self.agents.remove(agent)

    def clear_agents(self):
        # Delete them one by one so the tracker records every deletion!
        for a in list(self.agents):
            self.remove_agent(a)

    def is_occupied(self, r, c):
        if self.get_cell(r, c) == config.MODE_WALL: return True
        return any(a.r == r and a.c == c for a in self.agents)

    # ==========================================
    # UNDO / REDO LOGIC
    # ==========================================
    def undo(self):
        if self.history_index >= 0:
            transaction = self.history[self.history_index]
            # Undo must be read in REVERSE order!
            for action in reversed(transaction):
                if action["type"] == "cell":
                    self.static_grid[action["r"], action["c"]] = action["old"]
                elif action["type"] == "add_agent":
                    self.agents.remove(action["agent"]) # Undo Add = Remove
                elif action["type"] == "remove_agent":
                    self.agents.append(action["agent"]) # Undo Remove = Add Back
            
            self.history_index -= 1
            return True
        return False

    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            transaction = self.history[self.history_index]
            # Redo is read in normal order
            for action in transaction:
                if action["type"] == "cell":
                    self.static_grid[action["r"], action["c"]] = action["new"]
                elif action["type"] == "add_agent":
                    self.agents.append(action["agent"])
                elif action["type"] == "remove_agent":
                    self.agents.remove(action["agent"])
            return True
        return False

    # ==========================================
    # FILE I/O (JSON SAVE/LOAD)
    # ==========================================
    def get_state(self):
        """Creates a snapshot of the current map and agents for saving."""
        return {
            "rows": self.rows,
            "cols": self.cols,
            "static_grid": self.static_grid.tolist(), 
            "agents": [{"id": a.id, "r": a.r, "c": a.c, "speed": a.speed} for a in self.agents]
        }

    def load_state(self, state):
        """Restores the map and agents from a loaded file."""
        self.rows = state["rows"]
        self.cols = state["cols"]
        self.static_grid = np.array(state["static_grid"])
        
        # Bypass the transaction tracker when loading a file
        self.agents = []
        for a_data in state["agents"]:
            agent = Agent(a_data["id"], a_data["r"], a_data["c"])
            agent.speed = a_data["speed"]
            self.agents.append(agent)
            self.next_agent_id = max(self.next_agent_id, a_data["id"] + 1)

    def save_to_file(self, filepath):
        state = self.get_state()
        with open(filepath, 'w') as f:
            json.dump(state, f)

    def load_from_file(self, filepath):
        with open(filepath, 'r') as f:
            state = json.load(f)
        self.load_state(state)
        # Clear undo history so you can't "undo" opening a completely new file
        self.history = []
        self.history_index = -1
        self.current_transaction = None