from mesa import Agent

class Recurso(Agent):
    def __init__(self, unique_id, model, tipo, pos, utilidade=1):
        super().__init__(unique_id, model)
        self.tipo = tipo  # "Cristal", "Metal" ou "Estrutura"
        self.pos = pos  # A posição (tupla) deve ser passada
        self.utilidade = utilidade
        self.sendo_transportado = False
        self.agente_esperando = None  # Apenas para Estrutura

    def step(self):
        pass 


    def iniciar_transporte(self):
        """ O BDI define quando o recurso está sendo carregado. """
        self.sendo_transportado = True

class BaseInicial(Agent):
    """ Representa a base central onde os recursos são entregues. """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.recursos_entregues = []  # Lista de recursos entregues

    def registrar_recurso(self, recurso):
        """ Registra um recurso entregue na base. """
        if recurso.sendo_transportado:  # Apenas recursos carregados podem ser entregues
            self.recursos_entregues.append(recurso.utilidade)

    def utilidade_total(self):
        """ Retorna a soma total da utilidade dos recursos coletados. """
        return sum(self.recursos_entregues)
