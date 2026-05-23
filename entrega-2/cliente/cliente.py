from socket import *
from pathlib import Path

# ======================================= Definições =======================================

WfC0fA, WfA0, WfC1fA, WfA1 = 1, 2, 3, 4         # estados possíveis do transmissor rdt3.0
Wf0fB, Wf1fB = 5, 6                             # estados possíveis do receptor rdt3.0

# =================================== Funções do rdt3.0 ===================================

# ATENÇÃO: Em WfA0 e WfA1, mesmo que o ack recebido seja o não esperado, recvfrom reseta o timeout, ou seja, quebra o paradigma do Kurose, ver com os monitores
# se isso é um problema ou se é algo que pode ser ignorado, se for, podemos utilizar a biblioteca time e fazer o controle do timeout manualmente

def rdtsend(message, clientSocket, serverName, serverPort, bufferSize, a, txCurrState, lastPckg):
    # Obs.: a variável 'a' é apenas para fins de debug, para indicar o número do pacote que estamos enviando
    # Obs.: message é o conteúdo do pacote que queremos enviar do tamanho de messageSize (bufferSize - headerSize) e deve ser do tipo bytes
    # Obs.: txCurrState e lastPckg não devem ser sobrescritos fora da função rdtsend a não ser pelo retorno da própria função rdtsend
    txNextState = txCurrState
    pckg = lastPckg
    ready = False
    match txCurrState:
        case 1: #WfC0fA
            print(f'[Cliente]: Enviando pacote {a} de SeqNum 0 para o servidor {serverName}:{serverPort}.')
            pckg = "0".encode() + message  # pacote que contém o nome do arquivo --UDP-> servidor
            clientSocket.sendto(pckg, (serverName, serverPort))
            a += 1
            txNextState = WfA0
        case 2: #WfA0
            try:
                ack, serverAddress = clientSocket.recvfrom(bufferSize)  # aguardamos o ACK do servidor
                if ack.decode() == "ACK0":
                    print(f'[Cliente]: ACK0 recebido do servidor {serverAddress}.')
                    ready = True
                    txNextState = WfC1fA
            except timeout:
                print(f'[Cliente]: Timeout esperando ACK0. Reenviando pacote.')
                clientSocket.sendto(pckg, (serverName, serverPort))
        case 3: #WfC1fA
            print(f'[Cliente]: Enviando pacote {a} de SeqNum 1 para o servidor {serverName}:{serverPort}.')
            pckg = "1".encode() + message  # pacote que contém o nome do arquivo --UDP-> servidor
            clientSocket.sendto(pckg, (serverName, serverPort))
            a += 1
            txNextState = WfA1
        case 4: #WfA1
            try:
                ack, serverAddress = clientSocket.recvfrom(bufferSize)  # aguardamos o ACK do servidor
                if ack.decode() == "ACK1":
                    print(f'[Cliente]: ACK1 recebido do servidor {serverAddress}.')
                    ready = True
                    txNextState = WfC0fA
            except timeout:
                print(f'[Cliente]: Timeout esperando ACK1. Reenviando pacote.')
                clientSocket.sendto(pckg, (serverName, serverPort))
    return txNextState, pckg, ready, a

def receive(clientSocket, bufferSize, rxCurrState):
    message = None
    valid = False
    rxNextState = rxCurrState
    try:
        pckg, serverAddress = clientSocket.recvfrom(bufferSize)     # aguardamos o pacote do servidor
        seqNum = pckg[:headerSize].decode()                         # extraímos o SeqNum do pacote do header
        content = pckg[headerSize:].decode()                        # extraímos o conteúdo do pacote
        match rxCurrState:
            case 5: #Wf0fB
                if seqNum == "0":
                    print(f'[Cliente]: Pacote {seqNum} recebido do servidor {serverAddress}. Enviando ACK0.')
                    clientSocket.sendto("ACK0".encode(), serverAddress)  # enviamos o ACK0
                    message = content
                    valid = True
                    rxNextState = Wf1fB
                else:
                    print(f'[Cliente]: Pacote {seqNum} recebido do servidor {serverAddress}, mas SeqNum esperado era 0. Ignorando pacote e reenviando ACK1.')
                    clientSocket.sendto("ACK1".encode(), serverAddress)  # reenviamos o ACK1, pois o pacote recebido é duplicado
            case 6: #Wf1fB
                if seqNum == "1":
                    print(f'[Cliente]: Pacote {seqNum} recebido do servidor {serverAddress}. Enviando ACK1.')
                    clientSocket.sendto("ACK1".encode(), serverAddress)  # enviamos o ACK1
                    message = content
                    valid = True
                    rxNextState = Wf0fB
                else:
                    print(f'[Cliente]: Pacote {seqNum} recebido do servidor {serverAddress}, mas SeqNum esperado era 1. Ignorando pacote e reenviando ACK0.')
                    clientSocket.sendto("ACK0".encode(), serverAddress)  # reenviamos o ACK0, pois o pacote recebido é duplicado
    except timeout:
        pass
    return valid, message, rxNextState

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

try:
    arquivo = open(nomePath, 'rb')              # abrimos o arquivo e lemos o conteúdo em formato de bytes (leitura binária)
except FileNotFoundError:
    print(f'[Cliente]: Arquivo "{nome}" não encontrado. Encerrando o cliente.')
    hasMessageToSend = False

while hasMessageToSend:
    if hasMessageToSend:
       txCurrState, lastPckg, ready, a = rdtsend(message, clientSocket, serverName, serverPort, bufferSize, a, txCurrState, lastPckg)
