from mesa import Model
from mesa.space import MultiGrid
import random
from objetos import Recurso, BaseInicial
from agentes import (
    AgenteReativoSimples, 
    AgenteBaseadoEmEstado, 
    AgenteBaseadoEmObjetivos, 
    AgenteCooperativo,
    AgenteBDI 
)

class PlanetaModelo(Model):
    def __init__(self, width, height, num_recursos, num_agentes_reativos, 
                 num_agentes_estado, num_agentes_objetivos, num_agentes_cooperativos):
        super().__init__()
        self.grid = MultiGrid(width, height, False)
        self.width = width
        self.height = height

        # Base Inicial
        self.base_pos = (0, 0)
        self.base = BaseInicial("BASE", self)
        self.grid.place_agent(self.base, self.base_pos)

        # Agente BDI
        self.bdi = AgenteBDI("BDI", self, self.base_pos) 
        self.grid.place_agent(self.bdi, self.base_pos)

        # recursos
        for i in range(num_recursos):
            pos = self.gerar_posicao_valida()
            tipo_recurso = random.choice(["Cristal", "Metal", "Estrutura"])
            utilidade = {"Cristal": 10, "Metal": 20, "Estrutura": 50}[tipo_recurso]
            recurso = Recurso(f"R_{i}", self, tipo_recurso, utilidade)
            self.grid.place_agent(recurso, pos)

        # Agentes reativos simples
        self.agentes_reativos = []
        for i in range(num_agentes_reativos):
            pos = self.gerar_posicao_valida()
            agente = AgenteReativoSimples(f"A_{i}", self, self.base_pos)
            self.agentes_reativos.append(agente)
            self.grid.place_agent(agente, pos)

        # Agentes baseados em estado
        self.agentes_baseados_estado = []
        for i in range(num_agentes_estado):
            pos = self.gerar_posicao_valida()
            agente = AgenteBaseadoEmEstado(f"AE_{i}", self, self.base_pos)
            agente.model.bdi = self.bdi  # Associando o BDI ao agente
            self.agentes_baseados_estado.append(agente)
            self.grid.place_agent(agente, pos)

        # Agentes baseados em objetivos
        self.agentes_baseados_objetivos = []
        for i in range(num_agentes_objetivos):
            pos = self.gerar_posicao_valida()
            agente = AgenteBaseadoEmObjetivos(f"ABO_{i}", self, self.base_pos)
            agente.model.bdi = self.bdi  
            self.agentes_baseados_objetivos.append(agente)
            self.grid.place_agent(agente, pos)

        # Agentes cooperativos
        self.agentes_cooperativos = []
        for i in range(num_agentes_cooperativos):
            pos = self.gerar_posicao_valida()
            agente = AgenteCooperativo(f"AC_{i}", self, self.base_pos)
            agente.model.bdi = self.bdi  
            self.agentes_cooperativos.append(agente)
            self.grid.place_agent(agente, pos)

    def gerar_posicao_valida(self):
        """ Retorna uma posição aleatória disponível no grid. """
        while True:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            if (x, y) != self.base_pos and not self.grid.get_cell_list_contents((x, y)):
                return (x, y)

    def step(self):
        self.bdi.step()  #O BDI processa crenças primeiro
        
        for agente in self.agentes_reativos:
            agente.step()
        for agente in self.agentes_baseados_estado:
            agente.step()
        for agente in self.agentes_baseados_objetivos:
            agente.step()
        for agente in self.agentes_cooperativos:
            agente.step()
