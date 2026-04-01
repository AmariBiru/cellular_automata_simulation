# core/environment.py
import numpy as np
from core.entity import Agent
import config

class Environment:
    def __init__(self):
        self.rows = config.ROWS
        self.cols = config.COLS
        self.static_grid = np.zeros((self.rows, self.cols), dtype=int)
        self.agents = []
        self.next_agent_id = 0

    def get_cell(self, r, c):
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return self.static_grid[r, c]
        return None

    def set_cell(self, r, c, val):
        if 0 <= r < self.rows and 0 <= c < self.cols:
            self.static_grid[r, c] = val

    def add_agent(self, r, c):
        if any(a.r == r and a.c == c for a in self.agents): return
        agent = Agent(self.next_agent_id, r, c)
        self.agents.append(agent)
        self.next_agent_id += 1

    def remove_agent_at(self, r, c):
        self.agents = [a for a in self.agents if not (a.r == r and a.c == c)]

    def remove_agent(self, agent):
        if agent in self.agents:
            self.agents.remove(agent)

    def is_occupied(self, r, c):
        if self.get_cell(r, c) == config.MODE_WALL: return True
        return any(a.r == r and a.c == c for a in self.agents)