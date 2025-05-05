# model.py
from mesa import Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
import random
from environment import Obstacle, Base, Crystal, MetalBlock, AncientStructure

class PlanetModel(Model):
    def __init__(self, width=20, height=20, num_crystals=30, num_metals=20, num_structures=10, obstacle_ratio=0.2):
        super().__init__()
        self.width = width
        self.height = height
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = RandomActivation(self)
        self.num_crystals = num_crystals
        self.num_metals = num_metals
        self.num_structures = num_structures
        self.obstacle_ratio = obstacle_ratio
        self.base_pos = (width // 2, height // 2)  # Base no centro (10, 10) para 20x20

        # Configura o ambiente
        self.setup_environment()

    def setup_environment(self):
        # Coloca obstáculos (montanhas e rios)
        num_obstacles = int(self.width * self.height * self.obstacle_ratio)
        for _ in range(num_obstacles):
            x = random.randrange(self.width)
            y = random.randrange(self.height)
            if (x, y) != self.base_pos:  # Evita obstáculos na base
                obstacle = Obstacle(self.next_id(), self)
                self.grid.place_agent(obstacle, (x, y))

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
            # Verifica se a posição está vazia e não é a base
            if pos != self.base_pos and not any(isinstance(a, (Obstacle, Base, Crystal, MetalBlock, AncientStructure))
                                               for a in self.grid.get_cell_list_contents(pos)):
                resource = resource_class(self.next_id(), self, utility)
                self.grid.place_agent(resource, pos)
                placed += 1

    def step(self):
        self.schedule.step()