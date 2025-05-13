from mesa import Model
from mesa.space import MultiGrid
import random
from objetos import Recurso, BaseInicial, Estrutura
from agentes import AgenteReativoSimples, AgenteBaseadoEmEstado, AgenteBaseadoEmObjetivos, AgenteCooperativo, AgenteBDI

class PlanetaModelo(Model):
    def __init__(self, width, height, num_recursos, num_estruturas, num_agentes_reativos, num_agentes_estado, num_agentes_objetivos, num_agentes_cooperativos):
        super().__init__()
        self.grid = MultiGrid(width, height, False)
        self.width = width
        self.height = height

        # Dicionário para acesso rápido aos objetos e agentes pelo ID
        self.agents_by_id = {}

        # Base Inicial
        self.base_pos = (0, 0)
        self.base = BaseInicial("BASE", self)
        self.grid.place_agent(self.base, self.base_pos)
        self.agents_by_id[self.base.unique_id] = self.base

        # Adiciona o Agente BDI na base
        self.agente_bdi = AgenteBDI("BDI", self)
        self.grid.place_agent(self.agente_bdi, self.base_pos)
        self.agents_by_id[self.agente_bdi.unique_id] = self.agente_bdi

        # Recursos leves (Cristal e Metal)
        for i in range(num_recursos):
            pos = self.gerar_posicao_valida()
            tipo_recurso = random.choice(["Cristal", "Metal"])
            utilidade = {"Cristal": 10, "Metal": 20}[tipo_recurso]
            recurso = Recurso(f"R_{i}", self, tipo_recurso, utilidade, pos)
            self.grid.place_agent(recurso, pos)
            self.agents_by_id[recurso.unique_id] = recurso

        # Estruturas
        self.estruturas = []
        for i in range(num_estruturas):
            pos = self.gerar_posicao_valida()
            estrutura = Estrutura(f"E_{i}", self, pos)
            self.estruturas.append(estrutura)
            self.grid.place_agent(estrutura, pos)
            self.agents_by_id[estrutura.unique_id] = estrutura

        # Agentes reativos simples
        self.agentes_reativos = []
        for i in range(num_agentes_reativos):
            pos = self.gerar_posicao_valida()
            agente = AgenteReativoSimples(f"A_{i}", self, self.base_pos)
            self.agentes_reativos.append(agente)
            self.grid.place_agent(agente, pos)
            self.agents_by_id[agente.unique_id] = agente

        # Agentes baseados em estado
        self.agentes_baseados_estado = []
        for i in range(num_agentes_estado):
            pos = self.gerar_posicao_valida()
            agente = AgenteBaseadoEmEstado(f"AE_{i}", self, self.base_pos)
            self.agentes_baseados_estado.append(agente)
            self.grid.place_agent(agente, pos)
            self.agents_by_id[agente.unique_id] = agente

        # Agentes baseados em objetivos
        self.agentes_baseados_objetivos = []
        for i in range(num_agentes_objetivos):
            pos = self.gerar_posicao_valida()
            agente = AgenteBaseadoEmObjetivos(f"ABO_{i}", self, self.base_pos)
            self.agentes_baseados_objetivos.append(agente)
            self.grid.place_agent(agente, pos)
            self.agents_by_id[agente.unique_id] = agente

        # Agentes cooperativos
        self.agentes_cooperativos = []
        for i in range(num_agentes_cooperativos):
            pos = self.gerar_posicao_valida()
            agente = AgenteCooperativo(f"AC_{i}", self, self.base_pos)
            self.agentes_cooperativos.append(agente)
            self.grid.place_agent(agente, pos)
            self.agents_by_id[agente.unique_id] = agente

    def gerar_posicao_valida(self):
        """ Retorna uma posição aleatória disponível no grid. """
        while True:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            if (x, y) != self.base_pos and not self.grid.get_cell_list_contents((x, y)):
                return (x, y)

    def get_agent_by_id(self, unique_id):
        """ Retorna um agente ou objeto pelo seu ID. """
        return self.agents_by_id.get(unique_id, None)

    def step(self):
        """ Executa um ciclo de simulação, processando informações dos agentes. """
        for agente in self.agentes_reativos + self.agentes_baseados_estado + self.agentes_baseados_objetivos + self.agentes_cooperativos:
            if agente.pos == self.base_pos:  # Apenas agentes na base enviam informações para o BDI
                self.agente_bdi.receber_informacoes(agente)
            agente.step()

        # BDI processa informações e direciona agentes estratégicos
        self.agente_bdi.step()
