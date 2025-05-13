from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from planet_model import PlanetaModelo
from objetos import Recurso, BaseInicial, Estrutura
from agentes import AgenteReativoSimples, AgenteBaseadoEmEstado, AgenteBaseadoEmObjetivos, AgenteCooperativo, AgenteBDI 

def agent_portrayal(agent):
    """ Define a aparência dos objetos e agentes no grid. """
    if isinstance(agent, BaseInicial):
        return {"Shape": "circle", "Filled": "true", "Color": "black", "Layer": 1, "r": 0.9}

    elif isinstance(agent, Recurso):
        color_map = {"Cristal": "lightblue", "Metal": "grey", "Estrutura": "orange"}
        size_map = {"Cristal": 0.3, "Metal": 0.6, "Estrutura": 0.8}  
        if agent.tipo in color_map and agent.tipo in size_map:  
            return {"Shape": "rect", "Filled": "true", "Color": color_map[agent.tipo], "Layer": 2, "w": size_map[agent.tipo], "h": size_map[agent.tipo]}
        else:
            return {"Shape": "rect", "Filled": "true", "Color": "gray", "Layer": 2, "w": 0.5, "h": 0.5}

    elif isinstance(agent, Estrutura):
        return {"Shape": "rect", "Filled": "true", "Color": "orange", "Layer": 3, "w": 0.9, "h": 0.9}

    elif isinstance(agent, AgenteReativoSimples):
        return {"Shape": "circle", "Filled": "true", "Color": "red", "Layer": 4, "r": 0.3}

    elif isinstance(agent, AgenteBaseadoEmEstado):
        return {"Shape": "circle", "Filled": "true", "Color": "green", "Layer": 5, "r": 0.6}

    elif isinstance(agent, AgenteBaseadoEmObjetivos):
        return {"Shape": "circle", "Filled": "true", "Color": "blue", "Layer": 6, "r": 0.6}

    elif isinstance(agent, AgenteCooperativo):
        return {"Shape": "circle", "Filled": "true", "Color": "purple", "Layer": 7, "r": 0.6}

    elif isinstance(agent, AgenteBDI):  
        return {"Shape": "circle", "Filled": "true", "Color": "yellow", "Layer": 8, "r": 0.9}  # Define cor para o Agente BDI

    return {"Shape": "circle", "Filled": "true", "Color": "gray", "Layer": 2, "r": 0.3}

# Criando o grid
grid = CanvasGrid(agent_portrayal, 20, 20, 500, 500)

# Servidor da simulação
server = ModularServer(
    PlanetaModelo,
    [grid],
    "Simulação de Planeta",
    {
        "width": 20,
        "height": 20,
        "num_recursos": 30,
        "num_estruturas": 5,
        "num_agentes_reativos": 2,
        "num_agentes_estado": 2,
        "num_agentes_objetivos": 2,
        "num_agentes_cooperativos": 2,  
    }
)
