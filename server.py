from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid
from mesa.visualization import Slider, NumberInput, Choice  #Importação direta de componentes interativos
import random
from model import PlanetModel
from environment import Obstacle, Base, Crystal, MetalBlock, AncientStructure

def agent_portrayal(agent):
    """
    Define como cada tipo de agente é representado na visualização.
    """
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

def create_server():
    """
    NOVO: Função criada para encapsular a construção do servidor.
    Isso permite recriar ou reconfigurar facilmente o servidor em tempo de execução.
    """
    #Sliders foram adicionados para permitir controle dos parâmetros pela interface web
    model_params = {
        "width": Slider("Largura do Grid", 20, 10, 20, 1),
        "height": Slider("Altura do Grid", 20, 10, 20, 1),
        "num_crystals": Slider("Número de Cristais", 30, 5, 50, 1),
        "num_metals": Slider("Número de Blocos de Metal", 20, 5, 30, 1),
        "num_structures": Slider("Número de Estruturas Antigas", 2, 1, 10, 1)
    }

    #Largura e altura do grid agora são dinâmicas, baseadas nos sliders
    server = ModularServer(
        PlanetModel,
        [CanvasGrid(agent_portrayal, model_params["width"].value, model_params["height"].value, 500, 500)],
        "Planet Resource Collection",
        model_params
    )
    server.port = 8521
    return server

#Criação do servidor agora fora da raiz do script, utilizando a função create_server
server = create_server()

if __name__ == "__main__":
    server.launch()
