
from mesa import Agent
from objetos import Recurso

class AgenteReativoSimples(Agent):
    def __init__(self, unique_id, model, base_pos):
        super().__init__(unique_id, model)
        self.base_pos = base_pos
        self.carregando_recurso = False  

    def step(self):
        # Executa uma ação por ciclo. Se estiver carregando um recurso, vai para a base. Caso contrário, explora.
        if self.carregando_recurso:
            self.mover_para_base()
        else:
            self.explorar_ambiente()

    def explorar_ambiente(self):
        # Move-se aleatoriamente e tenta coletar um recurso.
        vizinhos = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        nova_pos = self.random.choice(vizinhos)
        self.model.grid.move_agent(self, nova_pos)

        # Verifica se há um recurso na nova posição e coleta se for possível
        objetos_na_posicao = self.model.grid.get_cell_list_contents(nova_pos)
        for objeto in objetos_na_posicao:
            if isinstance(objeto, Recurso) and objeto.tipo == "Cristal":
                self.carregando_recurso = True
                self.model.grid.remove_agent(objeto)  # Remove o recurso do ambiente
                return

    def mover_para_base(self):
        # Se estiver carregando um recurso, vai direto para a base e reinicia a exploração após entregar. #
        if self.pos != self.base_pos:
            self.mover_em_direcao(self.base_pos)
        else:
            self.carregando_recurso = False  # Recurso entregue, volta a explorar normalmente
            self.explorar_ambiente()

    def mover_em_direcao(self, destino):
        # Move o agente um passo na direção do destino.
        delta_x = destino[0] - self.pos[0]
        delta_y = destino[1] - self.pos[1]
        nova_pos_x = self.pos[0] + (1 if delta_x > 0 else -1 if delta_x < 0 else 0)
        nova_pos_y = self.pos[1] + (1 if delta_y > 0 else -1 if delta_y < 0 else 0)
        self.model.grid.move_agent(self, (nova_pos_x, nova_pos_y))


# ---------------------------------------------------------
# Agente Baseado em Estado
# ---------------------------------------------------------

class AgenteBaseadoEmEstado(Agent):
    """ Agente que usa memória curta para tomar decisões ao explorar e coletar recursos. """
    def __init__(self, unique_id, model, base_pos):
        super().__init__(unique_id, model)
        self.base_pos = base_pos  
        self.carregando_recurso = False  
        self.historico_movimento = set()  # Guarda posições recentemente visitadas para evitar repetição
        self.aguardando_ajuda = False  

    def step(self):
        if self.aguardando_ajuda:
            return  # Se está esperando ajuda, não faz nada até ser ajudado
        
        # Se está carregando um recurso, deve ir diretamente para a base
        if self.carregando_recurso:
            self.mover_para_base()
            return

        # Se há agentes aguardando ajuda, verifica se pode ajudar
        if self.model.agentes_aguardando_ajuda:
            agente_destino = next(iter(self.model.agentes_aguardando_ajuda))  # Pega o primeiro que precisa de ajuda
            if isinstance(self, AgenteCooperativo):  
                self.model.remover_espera(agente_destino)  
                self.iniciar_transporte(agente_destino)
                return  
        
        # Se não está aguardando ajuda e não está carregando um recurso, continua explorando
        self.explorar_ambiente()


    def explorar_ambiente(self):
        """ Explora o ambiente de forma estratégica e coleta recursos. """
        vizinhos = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        vizinhos_nao_visitados = [pos for pos in vizinhos if pos not in self.historico_movimento]

        if vizinhos_nao_visitados:
            nova_pos = self.random.choice(vizinhos_nao_visitados)  # Escolhe uma posição nova
        else:
            nova_pos = self.random.choice(vizinhos)  # Se todas já foram visitadas, continua se movendo

        # Move o agente e registra a nova posição
        self.model.grid.move_agent(self, nova_pos)
        self.historico_movimento.add(nova_pos)

        # Verifica recursos na nova posição
        objetos_na_posicao = self.model.grid.get_cell_list_contents(nova_pos)
        for objeto in objetos_na_posicao:
            if isinstance(objeto, Recurso):
                if objeto.tipo == "Estrutura" and objeto.agente_esperando is None:
                    objeto.agente_esperando = self  # Marca que está esperando ajuda
                    self.aguardando_ajuda = True  # Fica parado até ser ajudado
                    return  # Não continua explorando após marcar espera
                
                elif objeto.tipo in ["Cristal", "Metal"]:
                    self.carregando_recurso = True  
                    self.model.grid.remove_agent(objeto)  # Remove o recurso do grid
                    self.mover_para_base()
                    return  # Não continua explorando depois de coletar um recurso

    def mover_para_base(self):
        """ Se estiver carregando um recurso, move-se para a base e depois volta à exploração. """
        if self.pos != self.base_pos:
            self.mover_em_direcao(self.base_pos)
        else:
            self.carregando_recurso = False
            self.aguardando_ajuda = False  # Libera a espera por ajuda após a entrega
            self.historico_movimento.clear()
            self.explorar_ambiente()  # Volta à exploração

    def mover_em_direcao(self, destino):
        delta_x = destino[0] - self.pos[0]
        delta_y = destino[1] - self.pos[1]
        nova_pos_x = self.pos[0] + (1 if delta_x > 0 else -1 if delta_x < 0 else 0)
        nova_pos_y = self.pos[1] + (1 if delta_y > 0 else -1 if delta_y < 0 else 0)
        self.model.grid.move_agent(self, (nova_pos_x, nova_pos_y))


# ---------------------------------------------------------
# Agente Baseado em Objetivos
# ---------------------------------------------------------
class AgenteBaseadoEmObjetivos(Agent):
    """ Agente que planeja sua rota e precisa de ajuda para transportar estruturas. """
    def __init__(self, unique_id, model, base_pos):
        super().__init__(unique_id, model)
        self.base_pos = base_pos
        self.carregando_recurso = False
        self.alvo = None  
        self.aguardando_ajuda = False  

    def step(self):
        if self.aguardando_ajuda:
            return  # Se está esperando ajuda, aguarda parado
        
        if self.carregando_recurso:
            self.mover_para_base()
            return
        
        if self.alvo is None:
            self.definir_alvo()

        if self.alvo:
            self.mover_para_alvo()
        else:
            self.explorar_ambiente()

    def definir_alvo(self):
        """ Escolhe o recurso mais próximo e com maior valor. Se não houver, continua explorando. """
        recursos = [obj for cell in self.model.grid.coord_iter() for obj in cell[0] if isinstance(obj, Recurso)]

        if not recursos:
            print("Nenhum recurso encontrado! Explorando ambiente...")
            self.alvo = None 
            return  
        
        recurso_escolhido = min(recursos, key=lambda r: (self.distancia_ate(r.pos), -r.utilidade))
        if recurso_escolhido:
            self.alvo = recurso_escolhido
            print(f"Novo alvo definido: {self.alvo.tipo} na posição {self.alvo.pos}")

    def mover_para_alvo(self):
        """ Move-se na direção do alvo apenas se ele existir. Caso contrário, explora o ambiente. """
        if self.alvo is None:
            self.explorar_ambiente()
            return 

        self.mover_em_direcao(self.alvo.pos)
        objetos_na_posicao = self.model.grid.get_cell_list_contents(self.pos)

        for objeto in objetos_na_posicao:
            if isinstance(objeto, Recurso):
                if objeto.tipo == "Estrutura":
                    objeto.agente_esperando = self  
                    self.aguardando_ajuda = True  # Ele fica parado até um cooperativo vir ajudar
                    return
                else:
                    self.carregando_recurso = True
                    self.model.grid.remove_agent(objeto)
                    self.mover_para_base()
                    return

    def explorar_ambiente(self):
        """ Explora o ambiente aleatoriamente quando não tem um alvo. """
        vizinhos = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        nova_pos = self.random.choice(vizinhos)
        self.model.grid.move_agent(self, nova_pos)

    def mover_para_base(self):
        """ Ao chegar na base, reseta e volta a buscar novos recursos. """
        if self.pos != self.base_pos:
            self.mover_em_direcao(self.base_pos)
        else:
            self.carregando_recurso = False
            self.aguardando_ajuda = False  # Libera o modo de espera
            self.alvo = None  # Limpa o alvo antes de reiniciar a busca
            self.definir_alvo()  # Reinicia a busca por novos recursos

    def mover_em_direcao(self, destino):
        delta_x = destino[0] - self.pos[0]
        delta_y = destino[1] - self.pos[1]
        nova_pos_x = self.pos[0] + (1 if delta_x > 0 else -1 if delta_x < 0 else 0)
        nova_pos_y = self.pos[1] + (1 if delta_y > 0 else -1 if delta_y < 0 else 0)
        self.model.grid.move_agent(self, (nova_pos_x, nova_pos_y))

    def distancia_ate(self, pos):
        """ Calcula a distância entre a posição atual e um destino. """
        return abs(self.pos[0] - pos[0]) + abs(self.pos[1] - pos[1])


# ---------------------------------------------------------
# Agente Cooperativo - Com memória de exploração
# ---------------------------------------------------------

class AgenteCooperativo(Agent):
    """ Agente que auxilia no transporte de estruturas e coleta recursos de maneira estratégica. """
    def __init__(self, unique_id, model, base_pos):
        super().__init__(unique_id, model)
        self.base_pos = base_pos
        self.carregando_recurso = False
        self.carregando_estrutura = False
        self.parceiro = None  
        self.memoria_posicoes = set()  # Guarda locais visitados para otimizar a exploração

    def step(self):        
        if self.esta_ajudando():
            return  # Se está ajudando alguém, aguarda
        
        # Se está carregando um recurso ou estrutura, vai para a base
        if self.carregando_recurso or self.carregando_estrutura:
            self.mover_para_base()
            return

        # Se encontrar agentes esperando ajuda, prioriza o transporte
        if self.verificar_agentes_esperando():
            return

        # Se encontrar um recurso, coleta sozinho
        if self.coletar_recurso():
            return

        # Se não houver ações prioritárias, continua explorando
        self.explorar_estrategicamente()

    def coletar_recurso(self):
        """ Coleta Cristais e Metais sozinho e marca estruturas para transporte conjunto. """
        
        objetos_na_posicao = self.model.grid.get_cell_list_contents(self.pos)
        for objeto in objetos_na_posicao:
            if isinstance(objeto, Recurso):
                if objeto.tipo in ["Cristal", "Metal"]: 
                    self.carregando_recurso = True
                    self.model.grid.remove_agent(objeto)
                    self.mover_para_base()
                    return True

                if objeto.tipo == "Estrutura" and objeto.agente_esperando is None:  # Aguarda ajuda para transportar
                    objeto.agente_esperando = self  
                    self.aguardando_ajuda = True  
                    return True
        
        return False  # Não encontrou nenhum recurso na posição


    def esta_ajudando(self):
        """ Retorna True se está ajudando um agente no transporte. """
        return self.parceiro is not None

    def verificar_agentes_esperando(self):
        """ Apenas ajuda agentes que realmente precisam de ajuda. """
        for cell in self.model.grid.coord_iter():
            objetos_na_posicao = cell[0]
            for objeto in objetos_na_posicao:
                if isinstance(objeto, Recurso) and objeto.tipo == "Estrutura":
                    agente_esperando = objeto.agente_esperando
                    if agente_esperando and agente_esperando.aguardando_ajuda:
                        self.iniciar_transporte(agente_esperando, objeto)
                        return True  
        return False  

    def explorar_estrategicamente(self):
        """ Explora o ambiente de maneira eficiente, evitando locais já visitados. """
        vizinhos = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        melhores_opcoes = [pos for pos in vizinhos if pos not in self.memoria_posicoes]  
        nova_posicao = self.random.choice(melhores_opcoes) if melhores_opcoes else self.random.choice(vizinhos)
        self.model.grid.move_agent(self, nova_posicao)
        self.memoria_posicoes.add(nova_posicao)  

    def iniciar_transporte(self, parceiro, estrutura):
        """ Inicia o transporte conjunto da estrutura até a base, garantindo sincronização correta. """
        
        # Verifica se ambos estão na estrutura antes de iniciar
        if self.pos != estrutura.pos or parceiro.pos != estrutura.pos:
            if self.pos != estrutura.pos:
                self.mover_em_direcao(estrutura.pos)
            if parceiro.pos != estrutura.pos:
                parceiro.mover_em_direcao(estrutura.pos)
            return  

        # Ambos estão prontos para transportar a estrutura
        self.carregando_estrutura = True
        parceiro.carregando_estrutura = True
        self.parceiro = parceiro
        parceiro.parceiro = self

        # Transporta a estrutura passo a passo com os agentes
        while self.pos != self.base_pos:
            self.mover_em_direcao(self.base_pos)
            parceiro.mover_em_direcao(self.base_pos)
            self.model.grid.move_agent(estrutura, self.pos)  # Mantém a estrutura na posição dos agentes

        # Ao chegar na base, remove a estrutura e redefine os estados corretamente
        if estrutura in self.model.grid.get_cell_list_contents(self.base_pos):
            self.model.grid.remove_agent(estrutura)

        self.carregando_estrutura = False
        parceiro.carregando_estrutura = False
        self.parceiro = None
        parceiro.parceiro = None

        # Ambos os agentes voltam à exploração
        parceiro.step()  # Deixa que o próprio parceiro continue sua lógica normal
        self.step()  # O cooperativo volta ao seu ciclo de busca por agentes esperando ajuda


    def mover_para_base(self):
        """ Move-se para a base após coletar um recurso ou transportar uma estrutura. """
        if self.pos != self.base_pos:
            self.mover_em_direcao(self.base_pos)
            if self.parceiro:
                self.parceiro.mover_em_direcao(self.base_pos)
        else:
            self.carregando_recurso = False
            self.carregando_estrutura = False
            if self.parceiro:
                self.parceiro.carregando_estrutura = False
                self.parceiro = None       
            if self.verificar_agentes_esperando():
                return
            self.explorar_estrategicamente()

    def mover_em_direcao(self, destino):
        delta_x = destino[0] - self.pos[0]
        delta_y = destino[1] - self.pos[1]
        nova_pos_x = self.pos[0] + (1 if delta_x > 0 else -1 if delta_x < 0 else 0)
        nova_pos_y = self.pos[1] + (1 if delta_y > 0 else -1 if delta_y < 0 else 0)
        self.model.grid.move_agent(self, (nova_pos_x, nova_pos_y))
