# main.py
import numpy as np
from model import PlanetModel
from environment import Obstacle, Base, Crystal, MetalBlock, AncientStructure
from server import server

def visualize_grid_terminal(model):
    grid = np.full((model.height, model.width), ".")
    for x in range(model.width):
        for y in range(model.height):
            cell = model.grid.get_cell_list_contents((x, y))
            if cell:
                agent = cell[0]
                if isinstance(agent, Obstacle):
                    grid[y][x] = "O"
                elif isinstance(agent, Base):
                    grid[y][x] = "B"
                elif isinstance(agent, Crystal):
                    grid[y][x] = "C"
                elif isinstance(agent, MetalBlock):
                    grid[y][x] = "M"
                elif isinstance(agent, AncientStructure):
                    grid[y][x] = "S"
    for row in grid:
        print(" ".join(row))

if __name__ == "__main__":
    print("Abrindo o grid no navegador (http://localhost:8521)...")
    server.launch()