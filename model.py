from mesa import Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
import random
from environment import Obstacle, Base, Crystal, MetalBlock, AncientStructure

class PlanetModel(Model):
    def __init__(self, width=20, height=20, num_crystals=30, num_metals=20, num_structures=10):
        super().__init__()
        self.width = width
        self.height = height
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = RandomActivation(self)
        self.num_crystals = num_crystals
        self.num_metals = num_metals
        self.num_structures = num_structures
        self.base_pos = (width // 2, height // 2)  # Base no centro

        self.setup_environment()

    def setup_environment(self):
        # Obstáculos foram removidos

        # Coloca a base
        base = Base(self.next_id(), self)
        self.grid.place_agent(base, self.base_pos)

        # Coloca recursos
        self.place_resources(self.num_crystals, Crystal, utility=10)
        self.place_resources(self.num_metals, MetalBlock, utility=20)
        self.place_resources(self.num_structures, AncientStructure, utility=50)

    def place_resources(self, num, resource_class, utility):
        placed = 0
        while placed < num:
            x = random.randrange(self.width)
            y = random.randrange(self.height)
            pos = (x, y)
            if pos != self.base_pos and not any(isinstance(a, (Base, Crystal, MetalBlock, AncientStructure))
                                               for a in self.grid.get_cell_list_contents(pos)):
                resource = resource_class(self.next_id(), self, utility)
                self.grid.place_agent(resource, pos)
                placed += 1

    def step(self):
        self.schedule.step()
