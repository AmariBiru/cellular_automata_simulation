# core/simulation.py
import numpy as np
import heapq
import math
import random
from collections import defaultdict
import config

class FluidDynamicsModel:
    def __init__(self, environment):
        self.env = environment
        self.S_matrix = np.full((config.ROWS, config.COLS), 500.0)             
        self.heatmap_matrix = np.zeros((config.ROWS, config.COLS), dtype=float) 
        self.Phi_wall = np.full((config.ROWS, config.COLS), 500.0)             
        self.V_des = np.zeros((config.ROWS, config.COLS, 2), dtype=float) 
        
        # UI Programmable Variables!
        self.visc = 0.2
        self.ks = 2.5

    def recalculate_maps(self):
        self.calculate_distance_to_walls()  
        self.calculate_distance_map()       
        self.calculate_V_des() 

    def calculate_distance_to_walls(self):
        self.Phi_wall = np.full((config.ROWS, config.COLS), 500.0)
        pq = []
        for r, c in np.argwhere(self.env.static_grid == config.MODE_WALL):
            self.Phi_wall[r, c] = 0.0
            heapq.heappush(pq, (0.0, r, c))
        while pq:
            dist, r, c = heapq.heappop(pq)
            if dist > self.Phi_wall[r, c]: continue
            for dr, dc, weight in [(-1,0,1.0), (1,0,1.0), (0,-1,1.0), (0,1,1.0), (-1,-1,1.4), (-1,1,1.4), (1,-1,1.4), (1,1,1.4)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < config.ROWS and 0 <= nc < config.COLS:
                    if dist + weight < self.Phi_wall[nr, nc]:
                        self.Phi_wall[nr, nc] = dist + weight
                        heapq.heappush(pq, (dist + weight, nr, nc))

    def calculate_distance_map(self):
        raw_S = np.full((config.ROWS, config.COLS), 500.0)
        pq = []
        for r, c in np.argwhere(self.env.static_grid == config.MODE_EXIT):
            raw_S[r, c] = 0.0
            heapq.heappush(pq, (0.0, r, c))
            
        while pq:
            dist, r, c = heapq.heappop(pq)
            if dist > raw_S[r, c]: continue
            for dr, dc, weight in [(-1,0,1.0), (1,0,1.0), (0,-1,1.0), (0,1,1.0), (-1,-1,1.4), (-1,1,1.4), (1,-1,1.4), (1,1,1.4)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < config.ROWS and 0 <= nc < config.COLS and self.env.static_grid[nr, nc] != config.MODE_WALL:
                    phi_val = self.Phi_wall[nr, nc]
                    penalty = max(0.0, 3.0 - phi_val) * self.visc
                    if dist + weight + penalty < raw_S[nr, nc]:
                        raw_S[nr, nc] = dist + weight + penalty
                        heapq.heappush(pq, (dist + weight + penalty, nr, nc))
        self.S_matrix = np.copy(raw_S) # Simplified for modularity

    def calculate_V_des(self):
        def get_val(r, c, default):
            return self.S_matrix[r, c] if (0 <= r < config.ROWS and 0 <= c < config.COLS and self.env.static_grid[r, c] != config.MODE_WALL) else default

        for r in range(config.ROWS):
            for c in range(config.COLS):
                if self.env.static_grid[r, c] != config.MODE_WALL:
                    vc = self.S_matrix[r, c]
                    vl = get_val(r, c-1, vc); vr = get_val(r, c+1, vc)
                    vu = get_val(r-1, c, vc); vd = get_val(r+1, c, vc)

                    dx = (vr - vl)/2.0 if vr != vc and vl != vc else (vr - vc if vr != vc else vc - vl)
                    dy = (vd - vu)/2.0 if vd != vc and vu != vc else (vd - vc if vd != vc else vc - vu)

                    vx, vy = -dx, -dy
                    magnitude = math.hypot(vx, vy)
                    if magnitude > 0: 
                        vx /= magnitude; vy /= magnitude
                    self.V_des[r, c, 0] = vy; self.V_des[r, c, 1] = vx 

    def run_step(self):
        if len(self.env.agents) == 0: return False

        # Fluid movement math mapped to Agent objects
        for agent in list(self.env.agents):
            r, c = agent.r, agent.c
            v_des = self.V_des[r, c]
            
            moves = [(r, c), (r-1, c), (r+1, c), (r, c-1), (r, c+1), (r-1, c-1), (r-1, c+1), (r+1, c-1), (r+1, c+1)]
            valid_moves = []
            scores = []
            
            for nr, nc in moves:
                if 0 <= nr < config.ROWS and 0 <= nc < config.COLS:
                    cell_val = self.env.get_cell(nr, nc)
                    if not self.env.is_occupied(nr, nc) or (nr == r and nc == c) or cell_val == config.MODE_EXIT:
                        move_vec = np.array([nr - r, nc - c])
                        if nr == r and nc == c: 
                            score = 0.0
                        else:
                            dist = math.hypot(move_vec[0], move_vec[1])
                            if dist > 0: move_vec = move_vec / dist
                            score = np.dot(v_des, move_vec)
                        valid_moves.append((nr, nc))
                        scores.append(score)
            
            if valid_moves:
                scores = np.array(scores)
                exp_scores = np.exp(self.ks * (scores - np.max(scores)))
                probs = exp_scores / np.sum(exp_scores)
                best_target = valid_moves[np.random.choice(len(valid_moves), p=probs)]
                
                # Check for exit
                if self.env.get_cell(best_target[0], best_target[1]) == config.MODE_EXIT:
                    self.env.remove_agent(agent)
                else:
                    agent.r, agent.c = best_target[0], best_target[1]
                    self.heatmap_matrix[agent.r, agent.c] += 0.5
                    
        self.heatmap_matrix *= 0.85 
        return True