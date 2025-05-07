from mesa import Agent
from objetos import Recurso

class AgenteReativoSimples(Agent):
    """ Move-se aleatoriamente e coleta clistais. """
    def __init__(self, unique_id, model, base_pos):
        super().__init__(unique_id, model)
        self.base_pos = base_pos
        self.carregando_recurso = False

    def step(self):
        # Obtém a lista de recursos restantes no ambiente
        recursos_restantes = [obj for cell in self.model.grid.coord_iter() for obj in cell[0] if isinstance(obj, Recurso)]

        if not recursos_restantes:
            # Se não há mais recursos disponíveis, retorna à base
            self.mover_para_base()
        else:
            # Se ainda há recursos, executa sua lógica normal de decisão
            self.mover_aleatorio()


    def mover_aleatorio(self):
        """ Movimenta-se para uma célula vizinha aleatória. """
        vizinhos = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        nova_pos = self.random.choice(vizinhos)
        self.model.grid.move_agent(self, nova_pos)

        # Verifica se há um recurso na nova posição
        objetos_na_posicao = self.model.grid.get_cell_list_contents(nova_pos)
        for objeto in objetos_na_posicao:
            if isinstance(objeto, Recurso) and objeto.tipo == "Cristal":
                self.carregando_recurso = True
                self.model.grid.remove_agent(objeto)
                break

    def mover_para_base(self):
        """ Move-se diretamente para a base ao coletar um recurso. """
        if self.pos != self.base_pos:
            delta_x = self.base_pos[0] - self.pos[0]
            delta_y = self.base_pos[1] - self.pos[1]
            nova_pos_x = self.pos[0] + (1 if delta_x > 0 else -1 if delta_x < 0 else 0)
            nova_pos_y = self.pos[1] + (1 if delta_y > 0 else -1 if delta_y < 0 else 0)
            self.model.grid.move_agent(self, (nova_pos_x, nova_pos_y))
        else:
            self.carregando_recurso = False

#------------------------------------------------------------------------

# Agente baseado em estado
class AgenteBaseadoEmEstado(Agent):
    """ Agente que usa memória curta para tomar decisões. """
    def __init__(self, unique_id, model, base_pos):
        super().__init__(unique_id, model)
        self.base_pos = base_pos  
        self.carregando_recurso = False  
        self.historico_movimento = []  # Armazena posições visitadas recentemente
        self.aguardando_ajuda = False  

    def step(self):
    # Define o comportamento do agente baseado em estado. """
        # Obtém a lista de recursos restantes no ambiente
        recursos_restantes = [obj for cell in self.model.grid.coord_iter() for obj in cell[0] if isinstance(obj, Recurso)]

        if not recursos_restantes:
            # Se não há mais recursos disponíveis, retorna à base
            self.mover_para_base()
        else:
            # Se ainda há recursos, executa sua lógica normal de decisão
            self.explorar_ambiente()

    def explorar_ambiente(self):
        """ Explora o ambiente e coleta recursos quando encontra. """
        if self.aguardando_ajuda:
            return  # Se está esperando um cooperativo, não se move

        vizinhos = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        vizinhos_nao_visitados = [pos for pos in vizinhos if pos not in self.historico_movimento]
        
        nova_pos = self.random.choice(vizinhos_nao_visitados) if vizinhos_nao_visitados else self.random.choice(vizinhos)
        self.model.grid.move_agent(self, nova_pos)
        self.historico_movimento.append(nova_pos)

        # Verifica se há um recurso na nova posição e coleta se for possível
        objetos_na_posicao = self.model.grid.get_cell_list_contents(nova_pos)
        for objeto in objetos_na_posicao:
            if isinstance(objeto, Recurso) and objeto.tipo != "Estrutura":  # Apenas coleta cristais e metais
                self.carregando_recurso = True
                self.model.grid.remove_agent(objeto)
                break
            elif isinstance(objeto, Recurso) and objeto.tipo == "Estrutura":
                continue

    def mover_para_base(self):
        """ Move-se diretamente para a base ao coletar um recurso. """
        if self.pos != self.base_pos:
            delta_x = self.base_pos[0] - self.pos[0]
            delta_y = self.base_pos[1] - self.pos[1]
            nova_pos_x = self.pos[0] + (1 if delta_x > 0 else -1 if delta_x < 0 else 0)
            nova_pos_y = self.pos[1] + (1 if delta_y > 0 else -1 if delta_y < 0 else 0)
            self.model.grid.move_agent(self, (nova_pos_x, nova_pos_y))
        else:
            self.carregando_recurso = False
            self.historico_movimento.clear()
