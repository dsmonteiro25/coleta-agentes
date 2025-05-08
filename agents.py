
from mesa import Agent
from objetos import Recurso, BaseInicial

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
    """ Agente que usa memória curta para coletar informações e repassá-las ao BDI. """

    def __init__(self, unique_id, model, base_pos):
        super().__init__(unique_id, model)
        self.base_pos = base_pos  
        self.carregando_recurso = False  
        self.historico_movimento = set()  
        self.registros_locais = []  # Guarda descobertas antes de enviá-las ao BDI
        self.passou_pela_base = False  # Inicializa corretamente
        self.aguardando_ajuda = False  # Se encontrar uma estrutura, precisa de um agente cooperativo para transportar

    def step(self):
        
        if self.carregando_recurso:
            self.mover_para_base()
            return

        if self.aguardando_ajuda:  #Se encontrou uma estrutura, aguarda um agente cooperativo
            return  

        if self.tentar_coletar_recurso():  # Prioriza coletar um recurso antes de explorar
            return

        if self.passou_pela_base:  # Após passar pela base, decide a próxima ação
            self.definir_proxima_acao()
        else:
            self.explorar_ambiente()  # Se ainda não passou pela base, explora normalmente

    def tentar_coletar_recurso(self):
        objetos_na_posicao = self.model.grid.get_cell_list_contents(self.pos)
        
        for objeto in objetos_na_posicao:
            if isinstance(objeto, Recurso):
                if objeto.tipo in ["Cristal", "Metal"] and not self.carregando_recurso:
                    print(f"{self.unique_id} coletou {objeto.tipo} em {self.pos}") 
                    self.model.grid.remove_agent(objeto)  #Remove o recurso do ambiente
                    self.mover_para_base()
                    return True
                
                elif objeto.tipo == "Estrutura":
                    if objeto.agente_esperando is None and not isinstance(self, AgenteCooperativo):  
                        objeto.agente_esperando = self  #Apenas um agente não cooperativo pode marcar a espera
                        self.aguardando_ajuda = True  # Ativa espera até ser ajudado
                        print(f"{self.unique_id} marcou estrutura {objeto.tipo} em {objeto.pos} e está aguardando ajuda.")  
                        return True  
                    
                    # Se já houver um agente esperando, outros devem continuar explorando
                    print(f"{self.unique_id} encontrou {objeto.tipo} em {objeto.pos}, mas outro agente já está esperando. Continuando exploração.")
                    return False  

        return False  # Se não encontrou um recurso, retorna False para continuar explorando


    def explorar_ambiente(self):
        """ Explora e registra informações localmente antes de enviá-las ao BDI. """
        vizinhos = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        vizinhos_nao_visitados = [pos for pos in vizinhos if pos not in self.historico_movimento]

        if vizinhos_nao_visitados:
            nova_pos = self.random.choice(vizinhos_nao_visitados)  
        else:
            nova_pos = self.random.choice(vizinhos)  # Se todas posições já foram visitadas, continua se movendo

        self.model.grid.move_agent(self, nova_pos)
        self.historico_movimento.add(nova_pos)

        # Registra apenas dados essenciais, sem referenciar objetos diretamente
        objetos_na_posicao = self.model.grid.get_cell_list_contents(nova_pos)
        for objeto in objetos_na_posicao:
            if isinstance(objeto, Recurso):
                info_recurso = {
                    "tipo": objeto.tipo,
                    "posicao": objeto.pos,
                    "utilidade": objeto.utilidade
                }

                if info_recurso not in self.registros_locais:  # Evita registrar informações duplicadas
                    self.registros_locais.append(info_recurso)

    def mover_para_base(self):        
        if self.pos != self.base_pos:
            self.mover_em_direcao(self.base_pos)
        else:
            print(f"{self.unique_id} entregou um recurso na base e está pronto para explorar.") 
            self.carregando_recurso = False  # Recurso entregue
            self.passou_pela_base = True  # Agora pode consultar o BDI
            self.aguardando_ajuda = False  #Libera a espera por ajuda

            if self.registros_locais:  # Só envia dados ao BDI se houver descobertas novas
                self.model.bdi.atualizar_crencas(self.registros_locais, self)
                self.registros_locais.clear()

            self.historico_movimento.clear()  # Garante que o agente não fique preso explorando a mesma área
            self.explorar_ambiente()  # Continua explorando normalmente

    def definir_proxima_acao(self):
        """ Após entregar um recurso, decide se segue informações do BDI ou explora sozinho. """
        decisao = self.model.bdi.obter_decisao(self)

        if decisao in ["coletar_recurso", "transportar_estrutura", "retornar_base"]:
            print(f"{self.unique_id} seguindo decisão do BDI: {decisao}") 
            getattr(self, decisao)()  #Executa diretamente o método correspondente
        elif decisao == "explorar" and self.model.bdi.crencas.get("recursos"):
            recurso_alvo = min(self.model.bdi.crencas["recursos"], key=lambda r: self.distancia_ate(r["posicao"]))
            print(f"{self.unique_id} seguindo decisão do BDI para explorar recurso: {recurso_alvo}") 
            self.mover_em_direcao(recurso_alvo["posicao"])
        else:
            print(f"{self.unique_id} explorando sozinho, sem informações úteis do BDI.")  



    def mover_em_direcao(self, destino):
        """ Move o agente um passo na direção do destino. """
        delta_x = destino[0] - self.pos[0]
        delta_y = destino[1] - self.pos[1]
        nova_pos_x = self.pos[0] + (1 if delta_x > 0 else -1 if delta_x < 0 else 0)
        nova_pos_y = self.pos[1] + (1 if delta_y > 0 else -1 if delta_y < 0 else 0)
        self.model.grid.move_agent(self, (nova_pos_x, nova_pos_y))

# ---------------------------------------------------------
# Agente Baseado em Objetivos
# ---------------------------------------------------------
class AgenteBaseadoEmObjetivos(Agent):
    def __init__(self, unique_id, model, base_pos):
        super().__init__(unique_id, model)
        self.base_pos = base_pos
        self.carregando_recurso = False
        self.alvo = None
        self.registros_locais = []
        self.passou_pela_base = False
        self.aguardando_ajuda = False
        self.memoria_exploracao = set()  # Memória dos locais já visitados

    def step(self):
        """ Executa ações a cada rodada, garantindo que o agente explore por conta própria se o BDI não fornecer informações. """
        
        if self.carregando_recurso:
            self.mover_para_base()
            return

        if self.aguardando_ajuda:  
            return  

        if self.tentar_coletar_recurso(): 
            return

        # Se passou pela base, consulta o BDI, mas age autonomamente se não houver dados
        if self.passou_pela_base:
            decisao = self.model.bdi.obter_decisao(self)
            print(f"{self.unique_id} - Decisão do BDI: {decisao}")

            if decisao == "coletar_recurso":
                self.definir_alvo()
                self.mover_para_alvo()
            elif decisao == "transportar_estrutura":
                self.aguardando_ajuda = True
            elif decisao in ["explorar", None]:  # Se o BDI não tiver informações, explora normalmente
                print(f"{self.unique_id} - Nenhuma decisão do BDI, explorando por conta própria.")
                self.explorar_ambiente()
            elif decisao == "retornar_base":
                self.mover_para_base()
        else:
            self.explorar_ambiente()  # Explora sem interferência do BDI no início



    def definir_alvo(self):
        """ Escolhe o recurso mais próximo, considerando primeiro a memória de exploração antes das crenças do BDI. """
        recursos_memorizados = [r for r in self.memoria_exploracao.values() if not r.get("agente_coletando")]
        recursos_bdi = [r for r in self.model.bdi.crencas["recursos"] if "agente_coletando" not in r]
        recursos_disponiveis = recursos_memorizados + recursos_bdi  

        if not recursos_disponiveis:
            print(f"{self.unique_id}: Nenhum recurso registrado! Explorando ambiente...")
            self.alvo = None 
            self.explorar_ambiente()  # Se não houver recursos, inicia exploração
            return  

        recurso_escolhido = min(recursos_disponiveis, key=lambda r: (self.distancia_ate(r["pos"]), -r["utilidade"]))  
        self.alvo = recurso_escolhido
        print(f"{self.unique_id}: Novo alvo definido: {self.alvo['tipo']} na posição {self.alvo['pos']}")

    def mover_para_alvo(self):
        if not self.alvo:
            self.explorar_ambiente()
            return

        self.mover_em_direcao(self.alvo.pos)

    def tentar_coletar_recurso(self):
        if self.carregando_recurso:  # Se já estiver carregando, não pode pegar outro recurso
            return False

        objetos = self.model.grid.get_cell_list_contents(self.pos)
        for obj in objetos:
            if isinstance(obj, Recurso):
                if obj.tipo in ["Cristal", "Metal"] and not obj.sendo_transportado:
                    self.carregando_recurso = True
                    obj.sendo_transportado = True
                    self.model.grid.remove_agent(obj)
                    print(f"{self.unique_id}: Coletou {obj.tipo} em {self.pos}")
                    self.alvo = obj  # Definir o alvo para o recurso coletado
                    self.mover_para_base()
                    return True
                elif obj.tipo == "Estrutura":
                    if obj.agente_esperando is None and not isinstance(self, AgenteCooperativo):
                        obj.agente_esperando = self
                        self.aguardando_ajuda = True
                        self.model.bdi.registrar_estrutura(obj, self)
                        print(f"{self.unique_id}: Marcou estrutura em {self.pos}")
                        return True
        return False

    def explorar_ambiente(self):
        """ Explora o ambiente evitando locais já visitados para continuar avançando. """
        vizinhos = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        vizinhos_nao_visitados = [pos for pos in vizinhos if pos not in self.memoria_exploracao]

        if vizinhos_nao_visitados:
            nova_pos = self.random.choice(vizinhos_nao_visitados) 
        else:
            nova_pos = self.random.choice(vizinhos)

        self.model.grid.move_agent(self, nova_pos)
        self.memoria_exploracao.add(nova_pos)  # Marca o local como explorado

        objetos_na_posicao = self.model.grid.get_cell_list_contents(nova_pos)
        for objeto in objetos_na_posicao:
            if isinstance(objeto, Recurso):
                info_recurso = {
                    "tipo": objeto.tipo,
                    "pos": objeto.pos,
                    "utilidade": objeto.utilidade
                }

                if info_recurso not in self.registros_locais:  
                    self.registros_locais.append(info_recurso)

        print(f"{self.unique_id}: Explorando a posição {nova_pos}") 


    def mover_para_base(self):
        if self.pos != self.base_pos:
            self.mover_em_direcao(self.base_pos)
        else:
            print(f"{self.unique_id}: Entregou um recurso na base.") 
            self.carregando_recurso = False  
            self.passou_pela_base = True  
            self.aguardando_ajuda = False  

            if self.registros_locais: 
                self.model.bdi.atualizar_crencas(self.registros_locais, self)
                self.registros_locais.clear()

            self.memoria_exploracao.clear()   

    
            decisao = self.model.bdi.obter_decisao(self)
            if decisao == "coletar_recurso":
                self.definir_alvo()
                self.mover_para_alvo()
            else:
                print(f"{self.unique_id}: Nenhuma decisão do BDI. Iniciando exploração.")  
                self.explorar_ambiente()  

    def mover_em_direcao(self, destino):
        dx = destino[0] - self.pos[0]
        dy = destino[1] - self.pos[1]
        nova_x = self.pos[0] + (1 if dx > 0 else -1 if dx < 0 else 0)
        nova_y = self.pos[1] + (1 if dy > 0 else -1 if dy < 0 else 0)
        self.model.grid.move_agent(self, (nova_x, nova_y))

    def distancia_ate(self, pos):
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
        self.memoria_posicoes = set()  
        self.registros_locais = []  
        self.passou_pela_base = False  
        self.aguardando_parceiro = False  # Se encontrar uma estrutura, precisa de um parceiro para transporte

    def step(self):        
        if self.carregando_recurso or self.carregando_estrutura:
            self.mover_para_base()
            return

        if self.aguardando_parceiro:
            self.ajudar_agente_esperando()
            return  

        if self.tentar_coletar_recurso():  
            return

        
        if self.passou_pela_base:
            decisao = self.model.bdi.obter_decisao(self)
            print(f"{self.unique_id} - Decisão do BDI: {decisao}")

            if decisao == "coletar_recurso":
                self.coletar_recurso()
            elif decisao == "transportar_estrutura":
                self.iniciar_transporte()
            elif decisao == "ajudar_agente":
                self.ajudar_agente_esperando()
            elif decisao in ["explorar", None]:  
                print(f"{self.unique_id} - Nenhuma decisão do BDI, explorando por conta própria.")  
            elif decisao == "retornar_base":
                self.mover_para_base()
        else:
            self.explorar_estrategicamente()  # Explora sem interferência do BDI no início


    def tentar_coletar_recurso(self):
        objetos_na_posicao = self.model.grid.get_cell_list_contents(self.pos)
        
        for objeto in objetos_na_posicao:
            if isinstance(objeto, Recurso):
                if objeto.tipo in ["Cristal", "Metal"] and not self.carregando_recurso and not objeto.sendo_transportado:
                    print(f"{self.unique_id} coletou {objeto.tipo} em {self.pos}")  
                    self.carregando_recurso = True
                    objeto.sendo_transportado = True  # Marca como sendo transportado pelo BDI
                    self.model.grid.remove_agent(objeto)  #  Remove o recurso do ambiente
                    self.mover_para_base()
                    return True
                
                elif objeto.tipo == "Estrutura":
                    if objeto.agente_esperando is None:  
                        objeto.agente_esperando = self  
                        self.aguardando_parceiro = True  
                        print(f"{self.unique_id} marcou estrutura {objeto.tipo} em {objeto.pos} e está aguardando ajuda.") 
                        return True  

                    print(f"{self.unique_id} encontrou {objeto.tipo} em {objeto.pos}, mas outro agente já está esperando. Continuando exploração.")
                    return False  

        return False  #Se não encontrou um recurso, retorna False para continuar explorando


    def ajudar_agente_esperando(self):
        parceiro_esperando = self.model.bdi.obter_agente_esperando_transporte()
        if parceiro_esperando:
            self.mover_em_direcao(parceiro_esperando.pos)
            if self.pos == parceiro_esperando.pos:
                self.iniciar_transporte()
        else:
            print(f"{self.unique_id}: Nenhum parceiro aguardando. Continuando exploração.")
            self.explorar_estrategicamente()

    def iniciar_transporte(self):
        """ Inicia transporte de estrutura conforme definido pelo BDI. """
        estrutura = self.model.bdi.obter_estrutura_para_transporte(self)
        if estrutura:
            self.carregando_estrutura = True
            while self.pos != self.base_pos:
                self.mover_em_direcao(self.base_pos)
                self.model.grid.move_agent(estrutura, self.pos)  

            # Após a entrega, informa ao BDI e redefine estado
            self.carregando_estrutura = False
            self.model.bdi.registrar_entrega(self)
            self.step()  

    def explorar_estrategicamente(self):
        vizinhos = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        vizinhos_nao_visitados = [pos for pos in vizinhos if pos not in self.memoria_posicoes]

        if vizinhos_nao_visitados:
            nova_pos = self.random.choice(vizinhos_nao_visitados)  
        else:
            nova_pos = self.random.choice(vizinhos)  

        self.model.grid.move_agent(self, nova_pos)
        self.memoria_posicoes.add(nova_pos)  

        objetos_na_posicao = self.model.grid.get_cell_list_contents(nova_pos)
        for objeto in objetos_na_posicao:
            if isinstance(objeto, Recurso):
                info_recurso = {
                    "tipo": objeto.tipo,
                    "pos": objeto.pos,
                    "utilidade": objeto.utilidade
                }
                if info_recurso not in self.registros_locais:  
                    self.registros_locais.append(info_recurso)

        print(f"{self.unique_id}: Explorando a posição {nova_pos}")  

    def mover_para_base(self):
        
        while self.pos != self.base_pos:
            self.mover_em_direcao(self.base_pos)

        self.carregando_recurso = False
        self.carregando_estrutura = False
        self.passou_pela_base = True  
        self.aguardando_parceiro = False  

        if self.registros_locais:  
            self.model.bdi.atualizar_crencas(self.registros_locais, self)
            self.registros_locais.clear()

        self.memoria_posicoes.clear()  

        # Garante que uma nova ação seja tomada imediatamente
        if not self.coletar_recurso():
            print(f"{self.unique_id}: Nenhum recurso disponível. Explorando por conta própria.")  
            self.explorar_estrategicamente()

    def mover_em_direcao(self, destino):
        delta_x = destino[0] - self.pos[0]
        delta_y = destino[1] - self.pos[1]
        nova_pos = (self.pos[0] + (1 if delta_x > 0 else -1 if delta_x < 0 else 0),
                    self.pos[1] + (1 if delta_y > 0 else -1 if delta_y < 0 else 0))
        self.model.grid.move_agent(self, nova_pos)



# ---------------------------------------------------------
# Agente BDI - Administrador
# ---------------------------------------------------------

class AgenteBDI(Agent):
    """ Agente BDI que gerencia a lógica de decisão dos outros agentes. """

    def __init__(self, unique_id, model, base_pos):
        super().__init__(unique_id, model)
        self.base_pos = base_pos
        self.crencas = {
            "recursos": [],
            "estruturas": [],
            "agentes_descobertas": {},
            "movimentos_agentes": {},
            "agentes_esperando_ajuda": [],
            "prioridade_global": "explorar"
        }

    def step(self):
        self.processar_crencas()

    def processar_crencas(self):
        if self.crencas["agentes_esperando_ajuda"]:
            self.definir_prioridade("ajudar_agente")
        elif len(self.crencas["estruturas"]) > len(self.crencas["recursos"]):
            self.definir_prioridade("transportar_estrutura")
        else:
            self.definir_prioridade("tentar_coletar_recurso")

    def definir_prioridade(self, prioridade):
        self.crencas["prioridade_global"] = prioridade

    def atualizar_crencas(self, dados, agente):
        if agente.unique_id not in self.crencas["agentes_descobertas"]:
            self.crencas["agentes_descobertas"][agente.unique_id] = []

        for item in dados:
            if isinstance(item, dict):
                if item["tipo"] in ["Cristal", "Metal"]:
                    if item not in self.crencas["recursos"]:
                        self.crencas["recursos"].append(item)
                elif item["tipo"] == "Estrutura":
                    if item not in self.crencas["estruturas"]:
                        self.crencas["estruturas"].append(item)

                if item not in self.crencas["agentes_descobertas"][agente.unique_id]:
                    self.crencas["agentes_descobertas"][agente.unique_id].append(item)

    def registrar_estrutura(self, estrutura, agente):
        info_estrutura = {
            "tipo": estrutura.tipo,
            "posicao": estrutura.pos,
            "agente": agente.unique_id
        }

        if info_estrutura not in self.crencas["estruturas"]:
            self.crencas["estruturas"].append(info_estrutura)
            self.crencas["agentes_esperando_ajuda"].append(agente)
            print(f"BDI: Estrutura registrada na posição {estrutura.pos} pelo agente {agente.unique_id}")

    def liberar_estrutura(self, estrutura):
        estrutura.agente_esperando = None
        print(f"BDI: Estrutura em {estrutura.posicao} agora está disponível para outros agentes.")

    def obter_agente_esperando_transporte(self):
        if self.crencas["agentes_esperando_ajuda"]:
            return self.crencas["agentes_esperando_ajuda"].pop(0)
        return None

    def obter_decisao(self, agente):
        if agente.carregando_recurso:
            return "retornar_base"

        descobertas = self.crencas["agentes_descobertas"].get(agente.unique_id, [])

        # Verificar se tem estruturas para transportar
        for item in descobertas:
            if item["tipo"] == "Estrutura":
                return "transportar_estrutura"

        # Verificar se há recursos disponíveis para coletar
        for item in descobertas:
            if item["tipo"] in ["Cristal", "Metal"] and "agente_coletando" not in item:
                item["agente_coletando"] = agente.unique_id  # Marcar recurso como em processo
                return "tentar_coletar_recurso"

        return self.crencas.get("prioridade_global", "explorar")
