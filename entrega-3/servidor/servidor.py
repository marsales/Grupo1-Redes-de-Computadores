from socket import *
from pathlib import Path
import ast
import random
import threading
import os
import time 

# Definição da estrutura de dados que representa um item no leilão
class Item:
    name = None
    id = None
    price = 0.0
    bidder_username = None
    content = None
    count = 5
    time = 60
    filepath = None 

# ======================================= Definições =======================================


WfC0fA, WfA0, WfC1fA, WfA1 = 1, 2, 3, 4         # estados possíveis do transmissor RDT 3.0
Wf0fB, Wf1fB = 5, 6                             # estados possíveis do receptor RDT 3.0


# =================================== Funções do RDT 3.0 ===================================


# Envio de pacotes aos clientes
def rdtsend(message, socket, endAddressDst, bufferSize, txCurrState, lastPckg):
    
    # Obs1.: a variável 'count' é apenas para fins de debug, para indicar o número do pacote que estamos enviando
    # Obs2.: message é o conteúdo do pacote que queremos enviar do tamanho de messageSize (bufferSize - headerSize) e deve ser do tipo bytes
    # Obs3.: txCurrState e lastPckg não devem ser sobrescritos fora da função rdtsend a não ser pelo retorno da própria função rdtsend
    
    prob = 1                                   # Probabilidade de pacote ser entregue com sucesso, para simular um canal não confiável
    timeoutSeconds = 1                         # Timeout de 1 segundo para o cliente esperar por um ACK do servidor
    WfC0fA, WfA0, WfC1fA, WfA1 = 1, 2, 3, 4    # Estados possíveis do transmissor RDT 3.0
    pckg = lastPckg                            # Último pacote enviado, para que possamos reenviá-lo em caso de timeout
    ready = False                              # Se o cliente está pronto para enviar o próximo pacote (após receber o ACK do servidor)
    txNextState = txCurrState                  # A priori, o estado se mantém o mesmo

    match txCurrState:

        # ----------- Se ele está esperando chamada 0 da aplicação -----------
        case 1: #WfC0fA

            # Envio do pacote
            pckg = "0".encode() + message  # pacote que contém o nome do arquivo ---UDP---> destino
            
            # Simulação de não-confiabilidade
            if (random.random() < prob):
                socket.sendto(pckg, endAddressDst)

            # Transição para o estado de esperar ACK 0
            txNextState = WfA0

        # ------------------- Se ele está esperando ACK 0 -------------------
        case 2: #WfA0

            # Timeout para esperar o ACK do servidor
            socket.settimeout(timeoutSeconds)  

            # Tenta receber ACK do servidor...
            try:
                ack, endAddress = socket.recvfrom(bufferSize)

                # Se recebeu ACK 0 do servidor
                if endAddress == endAddressDst and ack.decode() == "T: ACK; NUM: 0;":

                    # Cliente pronto para enviar novos pacotes, transiciona para estado de esperar chamada 1
                    ready = True
                    txNextState = WfC1fA

            # ...exceto se tiver ocorrido timeout
            except timeout:

                # Reenvio do pacote
                if(random.random() < prob):
                    socket.sendto(pckg, endAddressDst)

        # ----------- Se ele está esperando chamada 1 da aplicação -----------
        case 3: #WfC1fA

            # Envio do pacote
            pckg = "1".encode() + message  # pacote que contém o nome do arquivo --UDP-> destino
            
            # Simulação de não-confiabilidade
            if (random.random() < prob):
                socket.sendto(pckg, endAddressDst)

            # Transição para o estado de esperar ACK 1
            txNextState = WfA1   

        # ------------------- Se ele está esperando ACK 1 -------------------
        case 4: #WfA1

            # Timeout para esperar o ACK do servidor
            socket.settimeout(timeoutSeconds)
            
            # Tenta receber ACK do servidor...
            try:
                ack, endAddress = socket.recvfrom(bufferSize) 

                # Se recebeu ACK 1 do servidor
                if endAddress == endAddressDst and ack.decode() == "T: ACK; NUM: 1;":

                    # Cliente pronto para enviar novos pacotes, transiciona para estado de esperar chamada 0
                    ready = True
                    txNextState = WfC0fA

            # ...exceto se tiver ocorrido timeout
            except timeout:

                # Reenvio do pacote
                if(random.random() < prob):
                    socket.sendto(pckg, endAddressDst)

    # Retornar as novas variáveis
    return txNextState, pckg, ready


# Recebimento de pacotes dos clientes
userListState = {}
def receive(socket, bufferSize, headerSize = 1):
    prob = 1                        # Probabilidade de pacote ser entregue com sucesso, para simular um canal não confiável [0 a 1]
    Wf0fB, Wf1fB = 5, 6             # Estados possíveis do receptor RDT 3.0
    message = None                  # Conteúdo do pacote recebido, caso ele seja válido
    endAddress = None               # Endereço do remetente do pacote recebido, caso ele seja válido
    valid = False                   # Se o pacote recebido é válido (ou seja, tem o SeqNum esperado e chegou algo)

    socket.settimeout(None)         # Remove o limite de tempo do socket para que ele bloqueie
    pckg, endAddress = socket.recvfrom(bufferSize)      # Recebe os dados e o IP/Porta do remetente
    rxCurrState = userListState[endAddress] if endAddress in userListState else Wf0fB   # Busca o estado atual do remetente no dicionário. Se for um usuário novo, assume que ele está esperando o pacote 0 
    userListState[endAddress] = rxCurrState     # Atualiza/Insere o usuário no dicionário com o estado atual
    rxNextState = rxCurrState       # Inicializa o próximo estado com o estado atual

    match rxCurrState:
        # Se está esperando pacote 0
        case 5: #Wf0fB
            seqNum = pckg[:headerSize].decode()                 
            content = pckg[headerSize:]    
                
            if seqNum == "0":
                if(random.random() < prob):
                    socket.sendto("T: ACK; NUM: 0;".encode(), endAddress)
                message = content
                endAddress = endAddress
                valid = True
                rxNextState = Wf1fB

                # Se recebeu pacote 1
            else:
                # Reenviamos ACK 1
                if(random.random() < prob):
                    socket.sendto("T: ACK; NUM: 1;".encode(), endAddress)

        # Se está esperando pacote 1
        case 6: #Wf1fB
            seqNum = pckg[:headerSize].decode()                 
            content = pckg[headerSize:]  
                    
            if seqNum == "1":
                if(random.random() < prob):
                    socket.sendto("T: ACK; NUM: 1;".encode(), endAddress)
                message = content
                endAddress = endAddress
                valid = True
                rxNextState = Wf0fB

            else:
                # Reenviamos ACK 0
                if(random.random() < prob):
                    socket.sendto("T: ACK; NUM: 0;".encode(), endAddress)

    userListState[endAddress] = rxNextState

    # Retornar as novas variáveis      
    return valid, message, endAddress


# =========================== Envio ativo de alertas do servidor ===========================

bidBuffer = []                     # Buffer de mensagens de alerta de lances recebidas dos clientes que ainda não foram processadas pela aplicação
bidBufferLock = threading.Lock()   # Lock para controlar o acesso ao buffer de mensagens de alerta de lances recebidas dos clientes
def alertSend(socket, headerSize, itensTimeList, itemsList, userList, bidBuffer, bidBufferLock, bufferSize):
    while True:
        # Verifica se há novos lances pendentes no buffer para fazer o broadcast
        if len(bidBuffer) > 0:
            with bidBufferLock:     # Trava o buffer temporariamente para evitar concorrência
                bid = bidBuffer.pop(0)
            # Extrai as informações da tupla guardada no buffer
            item_name = bid[0]      
            item_price = bid[1]     
            bidder_username = bid[2]
            itemsList[item_name].price = item_price     # Atualiza no objeto principal o novo preço
            itemsList[item_name].bidder_username = bidder_username      # Atualiza no objeto principal o novo ganhador parcial
            # Alerta desse novo lance para todos os usuários
            for user in userList.keys():
                alertAddress = userList[user][1]
                alertSeqNum = userList[user][3]
                endAddressDst = user
                response = f"T: ALERT_BID; BUN: {bidder_username}; IT: {item_name}; PR: {item_price}"
                txCurrState = WfC0fA if alertSeqNum == 0 else WfC1fA
                lastPkg = b''
                ready = False
                # Continua tentando enviar usando rdtSend até que o usuário responda o ACK
                while not ready:
                    txCurrState, lastPkg, ready = rdtsend(response.encode(), socket, alertAddress, bufferSize, txCurrState, lastPkg)
                # Salva o novo estado sequencial
                userList[endAddressDst] = [userList[user][0], userList[user][1], userList[user][2], 1 if alertSeqNum == 0 else 0]
        
        # Gerenciamento de tempo para todos os itens da lista
        for item_name in list(itensTimeList.keys()):
            itensTimeList[item_name] -= 1   # Subtrai 1 segundo do tempo restante do item atual
            if itensTimeList[item_name] % 20 == 0:      # A cada 20 segundos cheios, imprime o aviso 
                print(f"Tempo restante para o item {item_name}: {itensTimeList[item_name]} segundos")
            
            # Se o tempo deste item acabou 
            if itensTimeList[item_name] <= 0 or itemsList[item_name].count <= 0:
                del itensTimeList[item_name]
                item_namecurr = item_name
                item_content = itemsList[item_name].content
                item_price = itemsList[item_name].price
                winner_username = itemsList[item_name].bidder_username
                item_filepath = itemsList[item_name].filepath
                del itemsList[item_name]

                # Notifica os usiuários sobre o fim do leilão deste item
                for user in userList.keys():
                    alertAddress = userList[user][1]
                    alertSeqNum = userList[user][3]
                    endAddressDst = user
                    # Se ninguém deu lance
                    if winner_username == None:
                        response = f"T: ALERT_CL; IT: {item_namecurr}"
                    # Caso alguém deu lance
                    else:
                        response = f"T: ALERT_WIN; WUN: {winner_username}; IT: {item_namecurr}; PR: {item_price}"
                    
                    # Define estado do RDT
                    txCurrState = WfC0fA if alertSeqNum == 0 else WfC1fA
                    lastPkg = b''
                    ready = False   
                    
                    # Loop de envio via RDT até confirmação (ACK)
                    while not ready:
                        txCurrState, lastPkg, ready = rdtsend(response.encode(), socket, alertAddress, bufferSize, txCurrState, lastPkg)
                    
                    # Atualiza o histórico de sequências RDT para o usuário
                    userList[endAddressDst] = [userList[user][0], userList[user][1], userList[user][2], 1 if alertSeqNum == 0 else 0]
                    
                    # Entrega de prêmio
                    if userList[user][0] == winner_username:
                        print(f"Enviando item finalizado para o usuário {userList[user][0]}: {response}")
                        response = f"T: ITEM; NAME: {item_namecurr}; CTNT: {item_content}"
                        alertSeqNum = userList[user][3]
                        alertAddress = userList[user][1]
                        txCurrState = WfC0fA if alertSeqNum == 0 else WfC1fA
                        lastPkg = b''
                        ready = False

                        while not ready:
                            txCurrState, lastPkg, ready = rdtsend(response.encode(), socket, alertAddress, bufferSize, txCurrState, lastPkg)

                        userList[endAddressDst] = [userList[user][0], userList[user][1], userList[user][2], 1 if alertSeqNum == 0 else 0]

                        # NOVO: apaga o arquivo local somente depois que o conteúdo foi entregue ao vencedor
                        if item_filepath and os.path.exists(item_filepath):
                            os.remove(item_filepath)
                            print(f"Arquivo local removido após arremate: {item_filepath}")
                
                if winner_username is None and item_filepath and os.path.exists(item_filepath):
                    os.remove(item_filepath)
                    print(f"Arquivo local removido (leilão fechado sem lances): {item_filepath}")
        # Paralisa a thread por exatos 1 segundo e volta ao começo
        time.sleep(1)
            
def generateItems():
    caminho = Path(__file__).parent
    extensoes = [".txt"]
    delay = 5  # Delay de 10 segundos entre a adição de cada item
    counter = 1
    while True:
        arquivos_detectados = []
        for extensao in extensoes:
            arquivos_detectados.extend(caminho.glob(f"*{extensao}"))
        for arquivo in arquivos_detectados:
            nome_arquivo = arquivo.stem
            if nome_arquivo not in itemsList:
                preco_inicial = random.randint(10, 10000)//100
                tempo_leilao = 60
                setForAuction(nome_arquivo, counter, arquivo.read_text(), preco_inicial, tempo_leilao, str(arquivo))
                counter += 1
        time.sleep(delay)  # Aguarda o tempo inicial antes de começar a adicionar itens
    

# =================================== Funções auxiliares ===================================


# Função para fazer o parse das strings recebidas
def splitCall(call):
    command = call.split(";")[0].strip()
    args = call.split(";")[1:]
    match command:
        
        # Solicitação de login
        case "T: LGN":                      # T: LGN; UN: <username>; AP: <alert_port>; SQ: <seqNum>; ASQ: <alertSeqNum>;
            if len(args) == 4:
                username = args[0].strip()
                username = username.split(":")[1].strip()
                alertPort = args[1].strip()
                alertPort = alertPort.split(":")[1].strip()
                seqNum = args[2].strip()
                seqNum = seqNum.split(":")[1].strip()
                alertSeqNum = args[3].strip()
                alertSeqNum = alertSeqNum.split(":")[1].strip()
                return command, [username, alertPort, seqNum, alertSeqNum]
            else:
                return command, []
        
        # Comando para repassar um erro de login
        case "T: LGN_FAIL":                 # T: LGN_FAIL; RSN: <reason>;
            if len(args) == 1:
                reason = args[0].strip()
                reason = reason.split(":")[1].strip()
                return command, [reason]
            else:
                return command, []

        # Solicitação de saída (logout)
        case "T: LGO":                      # T: LGO;
            if len(args) == 0:
                return command, []
            else:
                return command, []

        # Confirmação de que o logout foi bem sucedido 
        case "T: LGO_OK":                   # T: LGO_OK;
            if len(args) == 0:
                return command, []
            else:
                return command, []

        # Erro caso logout falhe (retorna motivo) 
        case "T: LGO_FAIL":                 # T: LGO_FAIL; RSN: <reason>;
            if len(args) == 1:
                reason = args[0].strip()
                reason = reason.split(":")[1].strip()
                return command, [reason]
            else:
                return command, []

        # Comando requisitando o status de um item específico
        case "T: STS":                      # T: STS; IT: <item_name>;
            if len(args) == 0:
                return command, []
            if len(args) == 1:
                name = args[0].strip()
                name = name.split(":")[1].strip()
                return command, [name]
            else:
                return command, []

        # Retorno de consulta de status com quem está ganhando, que item é, e o preço atual  
        case "T: STS_RT":                   # T: STS_OK; BUN: <bid_username>; IT: <item_name>; PR: <price>;
            if len(args) == 3:
                bid_username = args[0].strip()
                bid_username = bid_username.split(":")[1].strip()
                name = args[1].strip()
                name = name.split(":")[1].strip()
                price = args[2].strip()
                price = float(price.split(":")[1].strip())
                return command, [bid_username, name, price]
            else:
                return command, []
            
        # Cliente efetuando um lance (bid) sobre um item
        case "T: BID":                      # T: BID; ITI: <item_id>; PR: <price>;
            if len(args) == 2:
                item_id = args[0].strip()
                item_id = int(item_id.split(":")[1].strip())
                price = args[1].strip()
                price = float(price.split(":")[1].strip())
                return command, [item_id, price]
            else:
                return command, []

        # Retorno de sucesso num lance efetuado
        case "T: BID_OK":                   # T: BID_OK; IT: <item_name>; PR: <price>;
            if len(args) == 2:
                name = args[0].strip()
                name = name.split(":")[1].strip()
                price = args[1].strip()
                price = float(price.split(":")[1].strip())
                return command, [name, price]
            else:
                return command, []
            
        # Erro num lance efetuado, falhou ou valor foi inferior, retornando razão
        case "T: BID_FAIL":                 # T: BID_FAIL; RSN: <reason>;
            if len(args) == 1:
                reason = args[0].strip()
                reason = reason.split(":")[1].strip()
                return command, [reason]
            else:
                return command, []

        # Pedido do cliente para receber lista com todos os itens disponíveis
        case "T: LST":                      # T: LST;
            if len(args) == 0:
                return command, []
            else:
                return command, []

        # Mensagem do servidor contendo os dados de UM item contido na lista solicitada
        case "T: LST_ITEM":                 # T: LST_ITEM; NAME: <item_name>; ID: <item_id>; PR: <price>; RST_L: <remaining_lots>; TM: <time_remaining>;
            if len(args) == 5:
                name = args[0].strip()
                name = name.split(":")[1].strip()
                id = args[1].strip()
                id = int(id.split(":")[1].strip())
                price = args[2].strip()
                price = float(price.split(":")[1].strip())
                remaining_lots = args[3].strip()
                remaining_lots = int(remaining_lots.split(":")[1].strip())
                time_remaining = args[4].strip()
                time_remaining = int(time_remaining.split(":")[1].strip())
                return command, [name, id, price, remaining_lots, time_remaining]
            else:   
                return command, []
        
        # Servidor marcando que terminou de enviar os itens da lista
        case "T: LST_END":                  # T: LST_END;
            if len(args) == 0:
                return command, []
            else:
                return command, []

        # Pacote de alerta do servidor para todos dizendo que houve um lance válido em um item
        case "T: ALERT_BID":                # T: ALERT_BID; BUN: <bid_username>; IT: <item_name>; PR: <price>;
            if len(args) == 3:
                bid_username = args[0].strip()
                bid_username = bid_username.split(":")[1].strip()
                name = args[1].strip()
                name = name.split(":")[1].strip()
                price = args[2].strip()
                price = float(price.split(":")[1].strip())
                return command, [bid_username, name, price]
            else:
                return command, []

        # Pacote de alerta do servidor para todos indicando quem foi o ganhador ao final do tempo 
        case "T: ALERT_WIN":                # T: ALERT_WIN; WUN: <winner_username>; IT: <item_name>; PR: <price>;
            if len(args) == 3:
                winner_username = args[0].strip()
                winner_username = winner_username.split(":")[1].strip()
                name = args[1].strip()
                name = name.split(":")[1].strip()
                price = args[2].strip()
                price = float(price.split(":")[1].strip())
                return command, [winner_username, name, price]
            else:
                return command, []
            
        # Pacote de alerta dizendo que o leilão acabou mas fechou vazio
        case "T: ALERT_CL":                 # T: ALERT_CL; IT: <item_name>;
            if len(args) == 1:
                name = args[0].strip()
                name = name.split(":")[1].strip()
                return command, [name]
            else:
                return command, []
            
        # Transmissão final do prêmio/conteúdo para o ganhador
        case "T: ITEM":                     # T: ITEM; WUN: <winner_username>; NAME: <item_name>; CTNT: <item_content>; 
            if len(args) == 2:
                name = args[0].strip()
                name = name.split(":")[1].strip()
                content = args[1].strip()
                content = content.split(":")[1].strip()
                return command, [name, content]
            else:
                return command, []
            
        # Marca o fim do conteúdo recebido de uma transmissão de item 
        case "T: ITEM_EOF":                 # T: ITEM_EOF; NAME: <item_name>;
            if len(args) == 1:
                name = args[0].strip()
                name = name.split(":")[1].strip()
                return command, [name]
            else:
                return command, [] 
            
        case _:
            return "", []
        
# Função para inicializar o leilão com itens antes ou durante as operações
def setForAuction(name, id, content, price, time, filepath=None):
    item = Item()
    item.name = name
    item.id = id
    item.bidder_username = None
    item.content = content
    item.price = price
    item.time = time
    item.filepath = filepath

    itemsList[name] = item
    itemsTimeList[name] = time
    print(f"Item adicionado: {name}, preço: {price}, tempo: {time} segundos")


# ================================== Configuração Inicial ==================================


bufferSize = 1024                             # Tamanho de um pacote
headerSize = 1                                # Tamanho do header do pacote, onde fica o SeqNum
messageSize = bufferSize - headerSize         # Tamanho do conteúdo do pacote
serverPort = 12000                            # Nº da porta utilizada
serverSocket = socket(AF_INET, SOCK_DGRAM)    # Socket do servidor, definido IPv4 e UDP
serverSocket.bind(('', serverPort))           # Registro de como contatar os clientes (qualquer formato + porta)

callsBuffer = []                     # Buffer de mensagens recebidas dos clientes que ainda não foram processadas pela aplicação
callsBufferLock = threading.Lock()   # Lock para controlar o acesso ao buffer de mensagens recebidas dos clientes

userList = {}  # Usuários logados{username: (ip, port)}
itemsList = {} # Itens do leilão, no formato
itemsTimeList = {} # Tempo restante para cada item do leilão, no formato {item_name: time_remaining}

# Inicializa o loop de controle de tempo e lances paralelos e a thread de geração de itens
threadAlertSend = threading.Thread(target=alertSend, args=(serverSocket, headerSize, itemsTimeList, itemsList, userList, bidBuffer, bidBufferLock, bufferSize))
threadItemGenerator = threading.Thread(target=generateItems)
threadItemGenerator.start()
threadAlertSend.start()

# Loop principal
while True:
    valid = False
    # Cria uma cópia de segurança do estado dos usuários para reverter em caso de falha
    copyUserListState = userListState.copy()
    # Fica travado aguardando na função de recebimento
    while not valid:
        valid, message, endAddress = receive(serverSocket, bufferSize, headerSize)
    
    # Processa os argumentos da mensagem que acabou de chegar
    call = splitCall(message.decode().strip())
    lastPkg = b''   # Prepara um pacote vazio

    # Verifica o comando lido da mensagem
    match call[0]:
        # --- CASO CLIENTE ESTEJA LOGANDO ---
        case "T: LGN":
            print(f"Mensagem de login recebida do destino {endAddress}: {message.decode().strip()}")
            txCurrState = WfC0fA
            # Desempacota as variáveis de formatação
            username, alertPort, sSeqNum, alertSeqNum = call[1]
            # Avalia e resolve a porta convertendo a string num formato aceito
            if isinstance(alertPort, str):
                alertPort = ast.literal_eval(alertPort) if alertPort.startswith("(") else (endAddress[0], int(alertPort))
            
            # Tratativa de erro caso já exista um cliente com esse nome cadastrado no userList
            if username in [user[0] for user in userList.values()]:
                response = f"T: LGN_FAIL; RSN: NAME_TAKEN"
                # Restaura os estados anteriores do receive
                userListState = copyUserListState.copy()
                ready = False
                # Dispara a mensagem de erro para o cliente
                while not ready:
                    txCurrState, lastPkg, ready = rdtsend(response.encode(), serverSocket, endAddress, bufferSize, txCurrState, lastPkg)
            
            # Se o nome estiver disponível (login correto)
            else:
                # Adiciona os dados do novo usuário
                userList[endAddress] = [username, alertPort, int(sSeqNum), int(alertSeqNum)]
                response = f"T: LGN_OK"
                ready = False
                # Dispara ACK do OK
                while not ready:
                    txCurrState, lastPkg, ready = rdtsend(response.encode(), serverSocket, endAddress, bufferSize, txCurrState, lastPkg)
        
        # --- CASO CLIENTE ESTEJA DESLOGANDO ---
        case "T: LGO":
            print(f"Mensagem de logout recebida do destino {endAddress}: {message.decode().strip()}")
            # Confere se ele realmente é um cliente ativo
            if endAddress in userList:
                username = userList[endAddress][0]
                txCurrState = WfC0fA if userList[endAddress][2] == 1 else WfC1fA
                # Exclui todos os dados dele
                del userList[endAddress]
                response = f"T: LGO_OK"
                ready = False
                # Confirma via RDT que a saída foi processada
                while not ready:
                    txCurrState, lastPkg, ready = rdtsend(response.encode(), serverSocket, endAddress, bufferSize, txCurrState, lastPkg)
        
        # --- CASO CLIENTE FAÇA UM LANCE (BID) ---
        case "T: BID":
            print(f"Mensagem de lance recebida do destino {endAddress}: {message.decode().strip()}")
            txCurrState = WfC0fA if userList[endAddress][2] == 1 else WfC1fA
            
            # Extrai nome e valor alvo mandados pelo usuário
            item_id, item_price = call[1]
            username = userList[endAddress][0]

            # Encontra o item pelo ID
            item_name = None
            for name, item in itemsList.items():
                if item.id == item_id:
                    item_name = name
                    break

            if item_name in itemsList:
                # O lance TEM que ser estritamente maior que o bid vigente
                if item_price > itemsList[item_name].price and itemsList[item_name].count > 0 and itemsTimeList[item_name] > 0:
                    itemsList[item_name].price = item_price
                    itemsList[item_name].bidder_username = username
                    itemsList[item_name].count -= 1
                    response = f"T: BID_OK; IT: {item_name}; PR: {item_price}"

                    # Usa o Lock para introduzir na lista o Broadcast sem causar colisão de thread
                    with bidBufferLock:
                        bidBuffer.append((item_name, item_price, username))
                
                # Se o lance for menor -> FAIL
                else:
                    response = f"T: BID_FAIL; RSN: PRICE_TOO_LOW"
            # Se tentar apostar num item que não existe
            else:
                response = f"T: BID_FAIL; RSN: ITEM_NOT_FOUND"
            ready = False
            while not ready:
                txCurrState, lastPkg, ready = rdtsend(response.encode(), serverSocket, endAddress, bufferSize, txCurrState, lastPkg)
            # Atualiza sequencial RDT
            userList[endAddress] = [userList[endAddress][0], userList[endAddress][1], txCurrState, userList[endAddress][3]]
        
        # --- CASO CLIENTE PEÇA STATUS ESPECÍFICO DE UM ITEM ---
        case "T: STS":
            print(f"Mensagem de status recebida do destino {endAddress}: {message.decode().strip()}")
            txCurrState = WfC0fA if userList[endAddress][2] == 1 else WfC1fA
            id = int(call[1][0])
            item_name = None
            for name in itemsList.keys():
                if itemsList[name].id == id:
                    item_name = name
                    break

            # Se encontrar o item solicitado
            if item_name in itemsList:
                item_price = itemsList[item_name].price
                response = f"T: STS_RT; BUN: {itemsList[item_name].bidder_username}; IT: {item_name}; PR: {item_price}"
            # Se não encontrar
            else:
                response = f"T: STS_FAIL; RSN: ITEM_NOT_FOUND"
            ready = False
            while not ready:
                txCurrState, lastPkg, ready = rdtsend(response.encode(), serverSocket, endAddress, bufferSize, txCurrState, lastPkg)
            userList[endAddress] = [userList[endAddress][0], userList[endAddress][1], txCurrState, userList[endAddress][3]]
        
        # --- CASO CLIENTE SOLICITE A LISTAGEM DO LEILÃO ATIVO ---
        case "T: LST":
            print(f"Mensagem de lista recebida do destino {endAddress}: {message.decode().strip()}")
            txCurrState = WfC0fA if userList[endAddress][2] == 1 else WfC1fA
            for item_name in list(itemsList.keys()):
                item_price = itemsList[item_name].price
                item_id = itemsList[item_name].id
                response = f"T: LST_ITEM; NAME: {item_name}; ID: {item_id}; PR: {item_price}; RST_L: {itemsList[item_name].count}; TM: {itemsTimeList[item_name]}"
                ready = False
                # Processo rdt
                while not ready:
                    txCurrState, lastPkg, ready = rdtsend(response.encode(), serverSocket, endAddress, bufferSize, txCurrState, lastPkg)
                userList[endAddress] = [userList[endAddress][0], userList[endAddress][1], txCurrState, userList[endAddress][3]]
            # Se todos os ítens foram enviados, sinaliza pro cliente que não virão mais listagens por agora
            response = f"T: LST_END"
            ready = False
            while not ready:
                txCurrState, lastPkg, ready = rdtsend(response.encode(), serverSocket, endAddress, bufferSize, txCurrState, lastPkg)
            userList[endAddress] = [userList[endAddress][0], userList[endAddress][1], txCurrState, userList[endAddress][3]]
            