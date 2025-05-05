# server.py
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid
from model import PlanetModel
from environment import Obstacle, Base, Crystal, MetalBlock, AncientStructure

def agent_portrayal(agent):
    portrayal = {"Shape": "rect", "Filled": "true", "w": 1, "h": 1}
    if isinstance(agent, Obstacle):
        portrayal["Color"] = "gray"
        portrayal["Layer"] = 0
    elif isinstance(agent, Base):
        portrayal["Color"] = "blue"
        portrayal["Layer"] = 1
    elif isinstance(agent, Crystal):
        portrayal["Color"] = "cyan"
        portrayal["Layer"] = 2
    elif isinstance(agent, MetalBlock):
        portrayal["Color"] = "silver"
        portrayal["Layer"] = 2
    elif isinstance(agent, AncientStructure):
        portrayal["Color"] = "gold"
        portrayal["Layer"] = 2
    return portrayal

# Configura o grid de visualização
grid = CanvasGrid(agent_portrayal, 20, 20, 500, 500)

# Configura o servidor
server = ModularServer(
    PlanetModel,
    [grid],
    "Planet Resource Collection",
    {"width": 20, "height": 20, "num_crystals": 30, "num_metals": 20, "num_structures": 10, "obstacle_ratio": 0.2}
)

# Define a porta (opcional, padrão é 8521)
server.port = 8521

if __name__ == "__main__":
    server.launch()