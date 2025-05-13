from mesa import Agent

class Recurso(Agent):
    """Representa um recurso disponível no ambiente."""
    def __init__(self, unique_id, model, tipo, utilidade, pos):
        super().__init__(unique_id, model)
        self.tipo = tipo
        self.utilidade = utilidade
        self.pos = pos
        self.transportado = False

class Estrutura(Agent):
    """Representa uma estrutura que requer múltiplos agentes para transporte."""
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)
        self.tipo = "Estrutura"
        self.utilidade = 50
        self.pos = pos
        self.agentes_transportando = set()
        self.sendo_transportada = False

    def adicionar_agente_transportador(self, agente):
        self.agentes_transportando.add(agente)
        if len(self.agentes_transportando) >= 2:
            self.sendo_transportada = True

class BaseInicial(Agent):
    """Representa a base onde os recursos são entregues."""
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.recursos_entregues = []

    def registrar_recurso(self, recurso):
        if not recurso.transportado:
            self.recursos_entregues.append({
                "tipo": recurso.tipo,
                "utilidade": recurso.utilidade,
                "pos": recurso.pos
            })
            self.model.grid.remove_agent(recurso)
            recurso.transportado = True

    def utilidade_total(self):
        return sum(r["utilidade"] for r in self.recursos_entregues)
