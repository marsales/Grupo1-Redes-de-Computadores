from socket import *
from pathlib import Path
import random
import threading


# ======================================= Definições =======================================


WfC0fA, WfA0, WfC1fA, WfA1 = 1, 2, 3, 4         # estados possíveis do transmissor RDT 3.0
Wf0fB, Wf1fB = 5, 6                             # estados possíveis do receptor RDT 3.0


# =================================== Funções do RDT 3.0 ===================================


# Envio de pacotes ao servidor
def rdtsend(message, socket, endAddressDst, bufferSize, txCurrState, lastPckg):
    
    # Obs1.: a variável 'count' é apenas para fins de debug, para indicar o número do pacote que estamos enviando
    # Obs2.: message é o conteúdo do pacote que queremos enviar do tamanho de messageSize (bufferSize - headerSize) e deve ser do tipo bytes
    # Obs3.: txCurrState e lastPckg não devem ser sobrescritos fora da função rdtsend a não ser pelo retorno da própria função rdtsend
    
    prob = 1.1                                 # Probabilidade de pacote ser entregue com sucesso, para simular um canal não confiável
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


# Recebimento de pacotes do servidor
def receive(socket, bufferSize, rxCurrState, headerSize = 1):
    prob = 0.9                      # Probabilidade de pacote ser entregue com sucesso, para simular um canal não confiável [0 a 1]
    Wf0fB, Wf1fB = 5, 6             # Estados possíveis do receptor RDT 3.0
    message = None                  # Conteúdo do pacote recebido, caso ele seja válido
    endAddress = None               # Endereço do remetente do pacote recebido, caso ele seja válido
    valid = False                   # Se o pacote recebido é válido (ou seja, tem o SeqNum esperado e chegou algo)
    rxNextState = rxCurrState       # A priori, o estado se mantém o mesmo

    match rxCurrState:

        # Se está esperando pacote 0
        case 5: #Wf0fB

            # Timeout para esperar o pacote do destino
            socket.settimeout(None)      

            # Tenta receber mensagem do servidor...                           
            try:
                pckg, endAddress = socket.recvfrom(bufferSize)

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
                pckg, endAddress = socket.recvfrom(bufferSize)   

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


# ======================== Ouvinte ativo para mensagens do servidor ========================


def activeAlertListener(alertSocket, bufferSize, headerSize):
    alertRxCurrState = Wf0fB
    while True:
        try:
            valid, alert, endAddress, alertRxCurrState = receive(alertSocket, bufferSize, alertRxCurrState, headerSize)
            if valid:
                #TODO: Processar a mensagem de alerta recebida do servidor
                mensagem_alerta = alert.decode().strip()
                with alertLock:
                    print(f"\r[ALERTA DO SERVIDOR]: {mensagem_alerta}\n>> ", end="", flush=True)
        except:
            pass


# =================================== Funções auxiliares ===================================


def splitCall(call):
    command = call.split(";")[0].strip()
    args = call.split(";")[1:]
    match command:
        case "T: LGN":
            if len(args) == 2:
                username = args[0].strip()
                username = username.split(":")[1].strip()
                seqNum = args[1].strip()
                seqNum = seqNum.split(":")[1].strip()
                return command, [username, seqNum]
        case "T: ALERT_BID":
            if len(args) == 2:
                name = args[0].strip()
                name = name.split(":")[1].strip()
                price = args[1].strip()
                price = price.split(":")[1].strip()
                return command, [name, price]
        case "T: ALERT_WIN":
            if len(args) == 2:
                name = args[0].strip()
                name = name.split(":")[1].strip()
                price = args[1].strip()
                price = price.split(":")[1].strip()
                return command, [name, price]
        case _:
            return "", []


# ================================== Configuração Inicial ==================================


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

try:
    clientSocket.bind(('', 0))
    alertSocket.bind(('', 0))
    socketPort = clientSocket.getsockname()[1]
    alertPort = alertSocket.getsockname()[1]
except:
    print("Erro ao criar o socket. Encerrando o cliente.")
    exit(1)

alertLock = threading.Lock()  # Lock para controlar a permissão para alertas do servidor serem processadas pela aplicação

print("Bem-vindo ao AuctionCin!")

while not logedIn:
    print("Digite o comando 'login <nome_do_usuario>' para se conectar ao servidor e participar dos leilões.")
    while not userName:
        command = input(">> ").strip()
        parts = command.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "login":
            userName = parts[1]
        else:
            print("Comando inválido. Por favor, use o formato 'login <nome_do_usuario>'.")

    messageTx = f"T: LGN; UN: {userName}; AP: {alertPort}; SQ: 0"
    messageRx = None
    ready = False
    lastPckg = b""
    while not ready:
        txCurrState, lastPckg, ready = rdtsend(messageTx.encode(), clientSocket, serverAddress, bufferSize, txCurrState, lastPckg)
    valid = False
    while not valid:
        valid, messageRx, endAddress, rxCurrState = receive(clientSocket, bufferSize, rxCurrState, headerSize)
    messageRx = (messageRx.decode()).strip().split(";")
    if messageRx[0] == "T: LGN_FAIL":
        if messageRx[1].strip() == "RSN: NAME_TAKEN":
            print(f'[{userName}]: Login falhou. O nome de usuário "{userName}" já está em uso. Por favor, escolha outro nome de usuário.')
        else:
            print(f'[{userName}]: Login falhou. Motivo desconhecido.')
        userName = None
    elif messageRx[0] == "T: LGN_OK":
        print(f'[{userName}]: Login bem-sucedido. Bem-vindo ao AuctionCin!')
        logedIn = True

activeAlertListenerThread = threading.Thread(target=activeAlertListener, args=(alertSocket, bufferSize, headerSize))
activeAlertListenerThread.daemon = True
activeAlertListenerThread.start()

while logedIn:
    command = input(">> ").strip()
    with alertLock:
        pass
    #TODO: FAZER TODO O RESTO DEPOIS! TO CANSADO!


#DONE: Funções do RDT 3.0 (rdtsend e receive), thread de ouvinte ativo para mensagens do servidor (activeListener), configuração inicial do cliente, comando de login e tratamento de resposta do servidor ao login (incluindo casos de falha)