# editor/tools.py
import config

class ToolManager:
    def __init__(self, env):
        self.env = env
        self.current_mode = config.MODE_WALL

    def set_mode(self, mode):
        self.current_mode = mode

    def apply_tool(self, r, c):
        if not (0 <= r < self.env.rows and 0 <= c < self.env.cols): return False

        changed = False
        if self.current_mode == config.MODE_AGENT:
            if self.env.get_cell(r, c) not in [config.MODE_WALL, config.MODE_EXIT]:
                self.env.add_agent(r, c)
                changed = True
        elif self.current_mode == config.MODE_ERASE:
            self.env.set_cell(r, c, 0)
            self.env.remove_agent_at(r, c)
            changed = True
        else:
            if self.env.get_cell(r, c) != self.current_mode:
                self.env.set_cell(r, c, self.current_mode)
                self.env.remove_agent_at(r, c)
                changed = True
        return changed