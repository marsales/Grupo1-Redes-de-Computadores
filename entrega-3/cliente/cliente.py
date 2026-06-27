from socket import *
from pathlib import Path
import random
import threading
import os


# ======================================= Definições =======================================

WfC0fA, WfA0, WfC1fA, WfA1 = 1, 2, 3, 4         # estados possíveis do transmissor RDT 3.0
Wf0fB, Wf1fB = 5, 6                             # estados possíveis do receptor RDT 3.0

# =================================== Funções do RDT 3.0 ===================================

pendingBuffer = []                     # Buffer de mensagens recebidas dos clientes que ainda não foram processadas pela aplicação
pendingBufferLock = threading.Lock()   # Lock para controlar o acesso ao buffer de mensagens recebidas dos clientes

# Envio de pacotes ao servidor
def rdtsend(message, socket, endAddressDst, bufferSize, txCurrState, lastPckg):
    
    # Obs1.: a variável 'count' é apenas para fins de debug, para indicar o número do pacote que estamos enviando
    # Obs2.: message é o conteúdo do pacote que queremos enviar do tamanho de messageSize (bufferSize - headerSize) e deve ser do tipo bytes
    # Obs3.: txCurrState e lastPckg não devem ser sobrescritos fora da função rdtsend a não ser pelo retorno da própria função rdtsend
    
    prob = 1                                # Probabilidade de pacote ser entregue com sucesso, para simular um canal não confiável
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

                else:

                    seqNum = ack[:1].decode(errors='ignore')

                    # Reenvia um ACK caso tenha recebido um pacote de dados perdido em vez de um ACK
                    if endAddress == endAddressDst and seqNum in ["0", "1"]:
                        socket.sendto(f"T: ACK; NUM: {seqNum};".encode(), endAddress)
                    
                    # Guarda o pacote no buffer de pendentes de forma segura com Lock
                    with pendingBufferLock:
                        pendingBuffer.append((ack, endAddress))

                    ready = False
                    txNextState = WfA0

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

                else:

                    seqNum = ack[:1].decode(errors='ignore')

                    if endAddress == endAddressDst and seqNum in ["0", "1"]:
                        socket.sendto(f"T: ACK; NUM: {seqNum};".encode(), endAddress)

                    with pendingBufferLock:
                        pendingBuffer.append((ack, endAddress))

                    ready = False
                    txNextState = WfA1

            # ...exceto se tiver ocorrido timeout
            except timeout:

                # Reenvio do pacote
                if(random.random() < prob):
                    socket.sendto(pckg, endAddressDst)

    # Retornar as novas variáveis
    return txNextState, pckg, ready


# Recebimento de pacotes do servidor
def receive(socket, bufferSize, rxCurrState, headerSize = 1):
    prob = 1                     # Probabilidade de pacote ser entregue com sucesso, para simular um canal não confiável [0 a 1]
    Wf0fB, Wf1fB = 5, 6             # Estados possíveis do receptor RDT 3.0
    message = None                  # Conteúdo do pacote recebido, caso ele seja válido
    endAddress = None               # Endereço do remetente dopacote recebido, caso ele seja válido
    valid = False                   # Se o pacote recebido é válido (ou seja, tem o SeqNum esperado e chegou algo)
    rxNextState = rxCurrState       # A priori, o estado se mantém o mesmo

    bufferedPack = None
    with pendingBufferLock:
        if socket is clientSocket and len(pendingBuffer) > 0:
            bufferedPack = pendingBuffer.pop(0)

    match rxCurrState:

        # Se está esperando pacote 0
        case 5: #Wf0fB

            # Timeout para esperar o pacote do destino
            socket.settimeout(None)      

            # Tenta receber mensagem do servidor...                           
            try:
                pckg, endAddress = bufferedPack if bufferedPack is not None else socket.recvfrom(bufferSize)

                # Extrair o SeqNum e o conteúdo
                seqNum = pckg[:headerSize].decode()                 
                content = pckg[headerSize:]    

                # Se recebeu pacote 0                 
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
            
            # ...exceto se tiver ocorrido timeout
            except timeout:
                pass

        # Se está esperando pacote 1
        case 6: #Wf1fB

            # Timeout para esperar o pacote do destino
            socket.settimeout(None)  

            # Tenta receber mensagem do servidor...                               
            try:
                pckg, endAddress = bufferedPack if bufferedPack is not None else socket.recvfrom(bufferSize)   

                # Extrair o SeqNum e o conteúdo 
                seqNum = pckg[:headerSize].decode()                 
                content = pckg[headerSize:]  

                # Se recebeu pacote 1                      
                if seqNum == "1":
                    if(random.random() < prob):
                        socket.sendto("T: ACK; NUM: 1;".encode(), endAddress)
                    message = content
                    endAddress = endAddress
                    valid = True
                    rxNextState = Wf0fB

                # Se recebeu pacote 0
                else:
                    # Reenviamos ACK 0
                    if(random.random() < prob):
                        socket.sendto("T: ACK; NUM: 0;".encode(), endAddress)
            
            # ...exceto se tiver ocorrido timeout
            except timeout:
                pass

    # Retornar as novas variáveis      
    return valid, message, endAddress, rxNextState


# ================================== Threads ==================================

# Buffers
alertBuffer = []    # Buffer para armazenar alertas recebidos do servidor
commandBuffer = []  # Buffer para armazenar comandos do usuário
itemBuffer = []     # Buffer para armazenar informações de item arrematados recebidas do servidor

# Locks
alertLock = threading.Lock()   # Lock para controlar a permissão para alertas do servidor serem processadas pela aplicação
commandLock = threading.Lock() # Lock para controlar a permissão para comandos do usuário serem processados pela aplicação
itemLock = threading.Lock()    # Lock para controlar a permissão para informações de item arrematados serem processadas pela aplicação

# Thread para ouvir mensagens do servidor
def alertListener(alertSocket, bufferSize, headerSize):
    alertRxCurrState = Wf0fB
    while True:
        valid, call, endAddress, alertRxCurrState = receive(alertSocket, bufferSize, alertRxCurrState, headerSize)
        if valid:
            call = splitCall(call.decode())
            if call[0] in ["T: ALERT_BID", "T: ALERT_WIN", "T: ALERT_CL"]:
                with alertLock:
                    alertBuffer.append(call)
            if call[0] in ["T: ITEM", "T: ITEM_EOF"]:
                with itemLock:
                    itemBuffer.append(call)

# Thread para enviar comandos para o servidor
def activeUserInputListener():
    while True:
        command = input().strip()
        with commandLock:
            commandBuffer.append(command)


# =================================== Funções auxiliares ===================================

# Função que converte as strings digitadas no terminal pelo usuário para strings padronizadas
def commandToCall(command, alert_port):
    parts = command.split()

    if len(parts) == 0:
        return None

    # Formata a mensagem de login
    if parts[0].lower() == "login":
        if len(parts) < 2:
            return None
        username = " ".join(parts[1:])
        return f"T: LGN; UN: {username}; AP: {alert_port}; SQ: 1; ASQ: 0"

    # Formata a mensagem de lance
    elif parts[0].lower() == "bid":
        if len(parts) != 3:
            return None
        id_item = parts[1]
        val = parts[2]
        return f"T: BID; IT: {id_item}; PR: {val}"

    # Formata a mensagem de listagem
    elif parts[0].lower() == "list":
        if len(parts) != 1:
            return None
        return "T: LST"

    # Formata a mensagem de verificação de status
    elif parts[0].lower() == "status":
        if len(parts) == 2:
            id_item = parts[1]
            return f"T: STS; IT: {id_item}"
        return None

    # Formata a mensagem de logout
    elif parts[0].lower() == "logout":
        if len(parts) != 1:
            return None
        return "T: LGO"

    return None

# Função que recebe uma string e extrai os parâmetros.
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
        case "T: ITEM":                     # T: ITEM; NAME: <item_name>; CTNT: <item_content>; 
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

# Envia uma string em protocolo garantindo a entrega (rdtsend)
def sendCallAndWaitResponse(call):
    global txCurrState
    global rxCurrState

    ready = False
    lastPckg = b""

    # Laço de envio confiável RDT
    while not ready:
        txCurrState, lastPckg, ready = rdtsend(
            call.encode(),
            clientSocket,
            serverAddress,
            bufferSize,
            txCurrState,
            lastPckg
        )

    valid = False
    messageRx = None

    # Laço de recepção confiável RDT
    while not valid:
        valid, messageRx, endAddress, rxCurrState = receive(
            clientSocket,
            bufferSize,
            rxCurrState,
            headerSize
        )
    return splitCall(messageRx.decode())

# Função para apenas aguardar uma mensagem do servidor
def waitReturnResponse():
    global rxCurrState

    valid = False
    messageRx = None

    # Laço de recepção bloqueante
    while not valid:
        valid, messageRx, endAddress, rxCurrState = receive(
            clientSocket,
            bufferSize,
            rxCurrState,
            headerSize
        )
    return splitCall(messageRx.decode())


# ================================== Configuração Inicial ==================================

# Criação dos Sockets UDP para comunicação geral e de alertas
clientSocket = socket(AF_INET, SOCK_DGRAM)
alertSocket = socket(AF_INET, SOCK_DGRAM)
serverAddress = (gethostbyname("localhost"), 12000)
headerSize = 1
bufferSize = 1024
messageSize = bufferSize - headerSize
txCurrState = WfC0fA
rxCurrState = Wf0fB
userName = None
logedIn = False

# Amarração dos Sockets em portas efêmeras aleatórias cedidas pelo S.O
try:
    clientSocket.bind(('', 0))
    alertSocket.bind(('', 0))
    socketPort = clientSocket.getsockname()[1]
    alertPort = alertSocket.getsockname()[1]
    alertAddress = (gethostbyname("localhost"), alertPort)
except:
    print("Erro ao criar o socket. Encerrando o cliente.")
    exit(1)

# Início das threads para manter recebimento em tempo real e não travar o cliente
alertListenerThread = threading.Thread(target=alertListener, args=(alertSocket, bufferSize, headerSize))
alertListenerThread.start()
activeUserInputListenerThread = threading.Thread(target=activeUserInputListener, args=())
activeUserInputListenerThread.start()

print("Bem-vindo ao AuctionCin!")

# Loop principal de execução do cliente
while True:
    print("Digite o comando 'login <nome_do_usuario>' para se conectar ao servidor e participar dos leilões.")
    
    # Garante que as ações só ocorram logadas
    while not logedIn:
        while not userName:
            command = None
            userName = None
            # Verifica se o usuário digitou algum comando
            if len(commandBuffer) > 0:
                with commandLock:
                    command = commandBuffer.pop(0) if commandBuffer else None
                parts = command.split(" ", 1)
                if len(parts) == 2 and parts[0].lower() == "login":
                    userName = parts[1]
                else:
                    print("Comando inválido. Por favor, use o formato 'login <nome_do_usuario>'.")

        # Procedimento de envio do Login
        messageTx = f"T: LGN; UN: {userName}; AP: {alertAddress}; SQ: 0; ASQ: 0"
        messageRx = None
        ready = False
        lastPckg = b""

        # Envia usando RDT
        while not ready:
            txCurrState, lastPckg, ready = rdtsend(messageTx.encode(), clientSocket, serverAddress, bufferSize, txCurrState, lastPckg)
        valid = False

        # Recebe resposta usando RDT
        while not valid:
            valid, messageRx, endAddress, rxCurrState = receive(clientSocket, bufferSize, rxCurrState, headerSize)
        messageRx = (messageRx.decode()).strip().split(";")
        
        # Tratamento da resposta de Login
        if messageRx[0] == "T: LGN_FAIL":
            if messageRx[1].strip() == "RSN: NAME_TAKEN":
                print(f'[{userName}]: Login falhou. O nome de usuário "{userName}" já está em uso. Por favor, escolha outro nome de usuário.')
            else:
                print(f'[{userName}]: Login falhou. Motivo desconhecido.')
            userName = None
            # Reseta estado do RDT caso falhe
            txCurrState = WfC0fA
            rxCurrState = Wf0fB
        elif messageRx[0] == "T: LGN_OK":
            print(f'[{userName}]: Você está online!')
            logedIn = True

    # Criação de pasta individual no OS baseada no username para guardar os arquivos que ele arrematar
    os.makedirs(f"cliente_{userName}", exist_ok=True)

    # Loop de Sessão Ativa
    while logedIn:

        # ======= PROCESSAMENTO DE ITENS VENCIDOS =======
        item = None
        # Desempilha itens que foram enviados para essa thread
        if len(itemBuffer) > 0:
            with itemLock:
                item = itemBuffer.pop(0) if itemBuffer else None

        # Se tem item a salvar, cria e escreve o .txt no diretório do usuário
        if item:
            itemName, content = item[1]

            pastaCliente = Path(__file__).parent / f"cliente_{userName}"
            caminho = pastaCliente / f'{itemName}.txt'


            with open(caminho, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"[{userName}] Item {itemName} recebido e salvo em: {caminho}")
        item = None

        # ======= PROCESSAMENTO DE ALERTAS DE LEILÃO =======
        # Se tem alerta para soltar no console para o usuário ler
        alert = None
        if len(alertBuffer) > 0:
            with alertLock:
                alert = alertBuffer.pop(0) if alertBuffer else None
        if alert:
            if alert[0] == "T: ALERT_BID":
                print(f"Novo Lance: {alert[1][0]} deu R$ {alert[1][2]:.2f} no item {alert[1][1]}")

            if alert[0] == "T: ALERT_WIN":
                print(f"Item vendido: {alert[1][0]} arrematou {alert[1][1]} por R$ {alert[1][2]:.2f}")

            if alert[0] == "T: ALERT_CL":
                print(f"Leilão de {alert[1][0]} encerrado sem lances")
            if alert[0] == "T: ITEM":
                print(f"Recebendo {alert[1][0]}")

        alert = None

        # ======= PROCESSAMENTO DE COMANDOS DO USUÁRIO =======
        # Se tem comando digitado que foi desempilhado do buffer da thread de input
        command = None
        if len(commandBuffer) > 0:
            with commandLock:
                command = commandBuffer.pop(0) if commandBuffer else None
        if command:
            # Formata a string do usuário pro formato do protocolo
            callText = commandToCall(command, alertPort)

            if callText is None:
                print("Comando inválido. Use: list, status <id_item>, bid <id_item> <valor> ou logout.")
                continue

            call = splitCall(callText)

            # Evita novo login caso já logado
            if call[0] == "T: LGN":
                print("Você já está logado.")

            # Ação: LANCE
            elif call[0] == "T: BID":
                response = sendCallAndWaitResponse(callText)

                # Confirma sucesso e atualiza display
                if response[0] == "T: BID_OK":
                    itemName, price = response[1]
                    print(f"Lance registrado: item {itemName}, valor R$ {price:.2f}")

                # Informa qual foi o erro do lance ao usuário
                elif response[0] == "T: BID_FAIL":
                    reason = response[1][0]
                    if reason == "ITEM_NOT_FOUND":
                        print(f"Lance recusado. Motivo: Item indisponível.")
                    if reason == "PRICE_TOO_LOW":
                        print(f"Lance recusado. Motivo: Seu lance foi muito baixo.")


                else:
                    print("Resposta inesperada do servidor:", response)


            # Ação: LISTAR ITENS
            elif call[0] == "T: LST":

                response = sendCallAndWaitResponse(callText)
                itens = []

                # Recebe continuamente pacotes até o servidor dizer LST_END
                while response[0] != 'T: LST_END':
                    nome = response[1][0]
                    id = response[1][1]
                    preco = response[1][2]
                    restante = response[1][3]
                    tempo = response[1][4]
                    text = f"Item: {nome} | ID: {id} | Valor Atual: R$ {preco:.2f} | Lances antes de encerrar: {restante} | Tempo Restante: {tempo} segundos"
                    itens.append(text)
                    response = waitReturnResponse()

                for item in itens:
                    print(item)


            # Ação: STATUS INDIVIDUAL DO ITEM
            elif call[0] == "T: STS":
                response = sendCallAndWaitResponse(callText)

                if response[0] == "T: STS_RT":
                    bidUser, itemName, price = response[1]
                    if bidUser == "None":
                        print(f"Item: {itemName} | Sem Lances Ainda | Valor Inicial: R$ {price:.2f} ")
                    else:
                        print(f"Item: {itemName} | Maior lance: R$ {price:.2f} | Usuário: {bidUser}")
                else:
                    print("Resposta inesperada do servidor:", response)


            # Ação: DESLOGAR
            elif call[0] == "T: LGO":
                response = sendCallAndWaitResponse(callText)

                if response[0] == "T: LGO_OK":
                    # Limpa buffers de alertas residuais e reseta as máquinas de estado RDT pro próximo login
                    alertBuffer.clear()
                    commandBuffer.clear()
                    itemBuffer.clear()
                    txCurrState = WfC0fA
                    rxCurrState = Wf0fB
                    print(f"[{userName}]: Logout realizado com sucesso. Você saiu do sistema.")
                    userName = None
                    logedIn = False
                else:
                    print("Falha no logout:", response)

            else:
                print("Comando inválido.")
