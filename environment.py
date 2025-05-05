# environment.py
from mesa import Agent

class Obstacle(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.type = "obstacle"

class Base(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.type = "base"
        self.resources = {"crystals": 0, "metals": 0, "structures": 0}
        self.total_utility = 0

    def receive_resource(self, resource_type, utility):
        self.resources[resource_type] += 1
        self.total_utility += utility

class Crystal(Agent):
    def __init__(self, unique_id, model, utility):
        super().__init__(unique_id, model)
        self.type = "crystal"
        self.utility = utility

class MetalBlock(Agent):
    def __init__(self, unique_id, model, utility):
        super().__init__(unique_id, model)
        self.type = "metal"
        self.utility = utility

class AncientStructure(Agent):
    def __init__(self, unique_id, model, utility):
        super().__init__(unique_id, model)
        self.type = "structure"
        self.utility = utility
        self.requires_two_agents = True