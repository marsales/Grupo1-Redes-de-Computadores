from socket import *
from pathlib import Path

# ======================================= Definições =======================================

WfC0fA, WfA0, WfC1fA, WfA1 = 1, 2, 3, 4         # estados possíveis do transmissor rdt3.0
Wf0fB, Wf1fB = 5, 6                             # estados possíveis do receptor rdt3.0

# =================================== Funções do rdt3.0 ===================================

# ATENÇÃO: Em WfA0 e WfA1, mesmo que o ack recebido seja o não esperado, recvfrom reseta o timeout, ou seja, quebra o paradigma do Kurose. Ver com os monitores
# se isso é um problema ou se é algo que pode ser ignorado, se for um problema, podemos utilizar a biblioteca time e fazer o controle do timeout manualmente

def rdtsend(message, socket, endName, endPort, bufferSize, a, txCurrState, lastPckg, userName):
    # Obs.: a variável 'a' é apenas para fins de debug, para indicar o número do pacote que estamos enviando
    # Obs.: message é o conteúdo do pacote que queremos enviar do tamanho de messageSize (bufferSize - headerSize) e deve ser do tipo bytes
    # Obs.: txCurrState e lastPckg não devem ser sobrescritos fora da função rdtsend a não ser pelo retorno da própria função rdtsend
    txNextState = txCurrState
    pckg = lastPckg
    ready = False
    match txCurrState:
        case 1: #WfC0fA
            print(f'[{userName}]: Enviando pacote {a} de SeqNum 0 para o servidor {endName}:{endPort}.')
            pckg = "0".encode() + message  # pacote que contém o nome do arquivo --UDP-> servidor
            socket.sendto(pckg, (endName, endPort))
            a += 1
            txNextState = WfA0
        case 2: #WfA0
            try:
                ack, endAddress = socket.recvfrom(bufferSize)  # aguardamos o ACK do servidor
                if ack.decode() == "ACK0":
                    print(f'[{userName}]: ACK0 recebido do servidor {endAddress}.')
                    ready = True
                    txNextState = WfC1fA
            except timeout:
                print(f'[{userName}]: Timeout esperando ACK0. Reenviando pacote.')
                socket.sendto(pckg, (endName, endPort))
        case 3: #WfC1fA
            print(f'[{userName}]: Enviando pacote {a} de SeqNum 1 para o servidor {endName}:{endPort}.')
            pckg = "1".encode() + message  # pacote que contém o nome do arquivo --UDP-> servidor
            socket.sendto(pckg, (endName, endPort))
            a += 1
            txNextState = WfA1
        case 4: #WfA1
            try:
                ack, endAddress = socket.recvfrom(bufferSize)  # aguardamos o ACK do servidor
                if ack.decode() == "ACK1":
                    print(f'[{userName}]: ACK1 recebido do servidor {endAddress}.')
                    ready = True
                    txNextState = WfC0fA
            except timeout:
                print(f'[{userName}]: Timeout esperando ACK1. Reenviando pacote.')
                socket.sendto(pckg, (endName, endPort))
    return txNextState, pckg, ready, a

def receive(socket, bufferSize, rxCurrState, userName):
    message = None
    endAddress = None
    valid = False
    rxNextState = rxCurrState
    try:
        pckg, endAddress = socket.recvfrom(bufferSize)     # aguardamos o pacote do servidor
        seqNum = pckg[:headerSize].decode()                         # extraímos o SeqNum do pacote do header
        content = pckg[headerSize:].decode()                        # extraímos o conteúdo do pacote
        match rxCurrState:
            case 5: #Wf0fB
                if seqNum == "0":
                    print(f'[{userName}]: Pacote {seqNum} recebido do servidor {endAddress}. Enviando ACK0.')
                    socket.sendto("ACK0".encode(), endAddress)  # enviamos o ACK0
                    message = content
                    endAddress = endAddress
                    valid = True
                    rxNextState = Wf1fB
                else:
                    print(f'[{userName}]: Pacote {seqNum} recebido do servidor {endAddress}, mas SeqNum esperado era 0. Ignorando pacote e reenviando ACK1.')
                    socket.sendto("ACK1".encode(), endAddress)  # reenviamos o ACK1, pois o pacote recebido é duplicado
            case 6: #Wf1fB
                if seqNum == "1":
                    print(f'[{userName}]: Pacote {seqNum} recebido do servidor {endAddress}. Enviando ACK1.')
                    socket.sendto("ACK1".encode(), endAddress)  # enviamos o ACK1
                    message = content
                    endAddress = endAddress
                    valid = True
                    rxNextState = Wf0fB
                else:
                    print(f'[{userName}]: Pacote {seqNum} recebido do servidor {endAddress}, mas SeqNum esperado era 1. Ignorando pacote e reenviando ACK0.')
                    socket.sendto("ACK0".encode(), endAddress)  # reenviamos o ACK0, pois o pacote recebido é duplicado
    except timeout:
        pass
    return valid, message, endAddress, rxNextState

# ================================== Configuração Inicial ==================================

serverName = 'localhost'                        # localhost -> cliente e servidor rodam na mesma máquina
bufferSize = 1024                               # tamanho de um pacote
headerSize = 1                                  # tamanho do header do pacote (número do pacote)
messageSize = bufferSize - headerSize           # tamanho do conteúdo do pacote
serverPort = 12000                              # definição da porta utilizada
timeout = 1                                     # timeout de 1 segundo para o cliente esperar por um ACK do servidor

clientSocket = socket(AF_INET, SOCK_DGRAM)      # socket do cliente, definido IPv4 e UDP
clientSocket.settimeout(timeout)                # definimos o timeout para o socket do cliente

txCurrState = WfC0fA
rxCurrState = WfA0

# ============================== Enviando Arquivo ao Servidor ==============================

nome = 'texto.txt'                              # nome do arquivo que queremos abrir
nomePath = Path(nome)                           # caminho para o arquivo que queremos abrir
message = f"FileName: {str(nome)}\n"            # nome do arquivo em bytes, para que possamos enviá-lo
message = message[:messageSize]                 # garantimos que o nome do arquivo caiba em um pacote (bufferSize - headerSize)
lastPckg = None                                 # variável que armazena o último pacote enviado, para que possamos reenviá-lo em caso de timeout
a = 1                                           # variável contadora que indica o número do pacote
hasMessageToSend = True                         # variável booleana que indica se ainda temos mensagens para enviar
ready = True                                    # variável booleana que indica se o cliente está pronto para enviar o próximo pacote (após receber o ACK do servidor)

# Carrego em message a primeira parte da mensagem
while hasMessageToSend:
    txCurrState, lastPckg, ready, a = rdtsend(message, clientSocket, serverName, serverPort, bufferSize, a, txCurrState)
    if ready:
        #carrego em message as proximas partes da mensagem
        #se deu EOF na leitura do arquivo, hasMessageToSend = False




