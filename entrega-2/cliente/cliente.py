from socket import *
from pathlib import Path

# ======================================= Definições =======================================

WfC0fA, WfA0, WfC1fA, WfA1 = 1, 2, 3, 4         # estados possíveis do transmissor rdt3.0
Wf0fB, Wf1fB = 5, 6                             # estados possíveis do receptor rdt3.0

# =================================== Funções do rdt3.0 ===================================

def rdtsend(message, clientSocket, serverName, serverPort, bufferSize, a, txCurrState, lastPckg):
    pckg = lastPckg
    txNextState = txCurrState
    ready = False
    match txCurrState:
        case 1: #WfC0fA
            print(f'[Cliente]: Enviando pacote {a} de SeqNum {0} para o servidor {serverName}:{serverPort}.')
            pckg = "0".encode() + message.encode()  # pacote que contém o nome do arquivo --UDP-> servidor
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
                print(f'[Cliente]: Timeout esperando ACK0. Reenviando nome do arquivo "{nome}".')
                clientSocket.sendto(pckg, (serverName, serverPort))
        case 3: #WfC1fA
            print(f'[Cliente]: Enviando pacote {a} de SeqNum {1} para o servidor {serverName}:{serverPort}.')
            pckg = "1".encode() + message.encode()  # pacote que contém o nome do arquivo --UDP-> servidor
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
                print(f'[Cliente]: Timeout esperando ACK1. Reenviando nome do arquivo "{nome}".')
                clientSocket.sendto(pckg, (serverName, serverPort))
    return txNextState, pckg, ready, a

# def rdtrecv(clientSocket, bufferSize, rxCurrState):

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
