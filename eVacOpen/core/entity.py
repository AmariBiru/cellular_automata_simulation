# core/entity.py

class Agent:
    def __init__(self, agent_id, r, c):
        self.id = agent_id
        self.r = r
        self.c = c
        self.speed = 1.0  # Ready for UI programmability later!