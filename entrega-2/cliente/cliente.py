from socket import *
from pathlib import Path
import random

# ======================================= Definições =======================================


WfC0fA, WfA0, WfC1fA, WfA1 = 1, 2, 3, 4         # estados possíveis do transmissor rdt3.0
Wf0fB, Wf1fB = 5, 6                             # estados possíveis do receptor rdt3.0


# =================================== Funções do rdt3.0 ===================================


def rdtsend(message, socket, endAddressDst, bufferSize, count, txCurrState, lastPckg, userName = "Local"):
    # Obs.: a variável 'count' é apenas para fins de debug, para indicar o número do pacote que estamos enviando
    # Obs.: message é o conteúdo do pacote que queremos enviar do tamanho de messageSize (bufferSize - headerSize) e deve ser do tipo bytes
    # Obs.: txCurrState e lastPckg não devem ser sobrescritos fora da função rdtsend a não ser pelo retorno da própria função rdtsend
    prob = 0.9                                      # probabilidade de pacote ser entregue com sucesso, para simular um canal não confiável
    timeoutSeconds = 1                              # timeout de 1 segundo para o cliente esperar por um ACK do servidor
    WfC0fA, WfA0, WfC1fA, WfA1 = 1, 2, 3, 4         # estados possíveis do transmissor rdt3.0

    pckg = lastPckg     # variável que armazena o último pacote enviado, para que possamos reenviá-lo em caso de timeout
    ready = False       # variável booleana que indica se o cliente está pronto para enviar o próximo pacote (após receber o ACK do servidor)
    txNextState = txCurrState
    match txCurrState:
        case 1: #WfC0fA
            print(f'[{userName}]: Enviando pacote {count} de SeqNum 0 para o destino {endAddressDst}.')
            pckg = "0".encode() + message  # pacote que contém o nome do arquivo --UDP-> destino
            if(random.random() < prob):
                socket.sendto(pckg, endAddressDst)
            count += 1
            txNextState = WfA0
        case 2: #WfA0
            socket.settimeout(timeoutSeconds)  # definimos o timeout para esperar o ACK do servidor
            try:
                ack, endAddress = socket.recvfrom(bufferSize)  # aguardamos o ACK do destino
                if endAddress == endAddressDst and ack.decode() == "ACK0":
                    print(f'[{userName}]: ACK0 recebido do destino {endAddress}.')
                    ready = True
                    txNextState = WfC1fA
            except timeout:
                print(f'[{userName}]: Timeout esperando ACK0. Reenviando pacote.')
                if(random.random() < prob):
                    socket.sendto(pckg, endAddressDst)
        case 3: #WfC1fA
            print(f'[{userName}]: Enviando pacote {count} de SeqNum 1 para o destino {endAddressDst}.')
            pckg = "1".encode() + message  # pacote que contém o nome do arquivo --UDP-> destino
            if(random.random() < prob):
                socket.sendto(pckg, endAddressDst)
            count += 1
            txNextState = WfA1   
        case 4: #WfA1
            socket.settimeout(timeoutSeconds)  # definimos o timeout para esperar o ACK do destino
            try:
                ack, endAddress = socket.recvfrom(bufferSize)  # aguardamos o ACK do destino
                if endAddress == endAddressDst and ack.decode() == "ACK1":
                    print(f'[{userName}]: ACK1 recebido do destino {endAddress}.')
                    ready = True
                    txNextState = WfC0fA
            except timeout:
                print(f'[{userName}]: Timeout esperando ACK1. Reenviando pacote.')
                if(random.random() < prob):
                    socket.sendto(pckg, endAddressDst)
    return txNextState, pckg, ready, count

def receive(socket, bufferSize, rxCurrState, count, userName = "Local", headerSize = 1):
    prob = 0.9                      # probabilidade de pacote ser entregue com sucesso, para simular um canal não confiável [0 a 1]
    Wf0fB, Wf1fB = 5, 6             # estados possíveis do receptor rdt3.0

    message = None                  # variavel que armazena o conteudo do pacote recebido, caso ele seja válido
    endAddress = None               # variavel que armazena o endereço do remetente do pacote recebido, caso ele seja válido
    valid = False                   # variavel booleana que indica se o pacote recebido é válido (ou seja, tem o SeqNum esperado e chegou algo)
    rxNextState = rxCurrState 
    match rxCurrState:
        case 5: #Wf0fB
            socket.settimeout(None)                                 # definimos o timeout para esperar o pacote do destino
            try:
                pckg, endAddress = socket.recvfrom(bufferSize)      # aguardamos o pacote do destino
                seqNum = pckg[:headerSize].decode()                 # extraímos o SeqNum do pacote do header
                content = pckg[headerSize:]                         # extraímos o conteúdo do pacote
                if seqNum == "0":
                    print(f'[{userName}]: Pacote {count} de SeqNum {seqNum} recebido do destino {endAddress}. Enviando ACK0.')
                    count += 1
                    if(random.random() < prob):
                        socket.sendto("ACK0".encode(), endAddress)  # enviamos o ACK0
                    message = content
                    endAddress = endAddress
                    valid = True
                    rxNextState = Wf1fB
                else:
                    print(f'[{userName}]: Pacote {count} de SeqNum {seqNum} recebido do destino {endAddress}, mas SeqNum esperado era 0. Ignorando pacote e reenviando ACK1.')
                    if(random.random() < prob):
                        socket.sendto("ACK1".encode(), endAddress)  # reenviamos o ACK1, pois o pacote recebido é duplicado
            except timeout:
                pass
        case 6: #Wf1fB
            socket.settimeout(None)                                 # definimos o timeout para esperar o pacote do destino
            try:
                pckg, endAddress = socket.recvfrom(bufferSize)      # aguardamos o pacote do destino
                seqNum = pckg[:headerSize].decode()                 # extraímos o SeqNum do pacote do header
                content = pckg[headerSize:]                         # extraímos o conteúdo do pacote
                if seqNum == "1":
                    print(f'[{userName}]: Pacote {count} de SeqNum {seqNum} recebido do destino {endAddress}. Enviando ACK1.')
                    count += 1
                    if(random.random() < prob):
                        socket.sendto("ACK1".encode(), endAddress)  # enviamos o ACK1
                    message = content
                    endAddress = endAddress
                    valid = True
                    rxNextState = Wf0fB
                else:
                    print(f'[{userName}]: Pacote {count} de SeqNum {seqNum} recebido do destino {endAddress}, mas SeqNum esperado era 1. Ignorando pacote e reenviando ACK0.')
                    if(random.random() < prob):
                        socket.sendto("ACK0".encode(), endAddress)  # reenviamos o ACK0, pois o pacote recebido é duplicado
            except timeout:
                pass
    return valid, message, endAddress, rxNextState, count


# ================================== Configuração Inicial ==================================


serverName = 'localhost'                                    # localhost -> cliente e servidor rodam na mesma máquina
serverPort = 12000                                          # definição da porta utilizada
serverAddress = (gethostbyname(serverName), serverPort)     # tupla que representa o endereço do servidor
bufferSize = 1024                                           # tamanho de um pacote
headerSize = 1                                              # tamanho do header do pacote (número de sequencia), que é 1 byte
messageSize = bufferSize - headerSize                       # tamanho do conteúdo do pacote
userName = "Cliente"                                        # nome do cliente, para fins de debug
a = 1                                                       # variável de controle de envio (debug)
b = 1                                                       # variável de controle de recebimento (debug)

clientSocket = socket(AF_INET, SOCK_DGRAM)                  # socket do cliente, definido IPv4 e UDP

txCurrState = WfC0fA
rxCurrState = Wf0fB


# ================================= Enviando Arquivo ao Servidor =================================


lastPckg = None                                 # variável que armazena o último pacote enviado, para que possamos reenviá-lo em caso de timeout
hasMessageToSend = True                         # variável booleana que indica se ainda temos mensagens para enviar
ready = True                                    # variável booleana que indica se o cliente está pronto para enviar o próximo pacote (após receber o ACK do servidor)

nome = 'canario.webp'                   # nome do arquivo que queremos abrir
arquivo = Path(__file__).parent / nome  # caminho para o arquivo que queremos abrir
if not arquivo.is_file():
    print(f'[{userName}]: O arquivo "{nome}" não existe. Verifique se o nome do arquivo e o caminho estão corretos.')
    exit(1)
message = f"NAME_OF_FILE: {nome}".encode()  

with open(arquivo, 'rb') as f:  # abrimos o arquivo e lemos o conteúdo em formato de bytes (leitura binária)
    print(f'[{userName}]: Preparando para enviar o arquivo "{nome}" para o destino {serverAddress}.')
    while message:
        txCurrState, lastPckg, ready, a = rdtsend(message, clientSocket, serverAddress, bufferSize, a, txCurrState, lastPckg, userName)
        if ready:
            message = f.read(messageSize)
    message = "EOF".encode()
    txCurrState, lastPckg, ready, a = rdtsend(message, clientSocket, serverAddress, bufferSize, a, txCurrState, lastPckg, userName)
    while ready == False:
        txCurrState, lastPckg, ready, a = rdtsend(message, clientSocket, serverAddress, bufferSize, a, txCurrState, lastPckg, userName)
    print(f'[{userName}]: Arquivo "{nome}" enviado para o destino {serverAddress} e finalizado!')


# ================================= Recebendo Arquivo do Servidor =================================


while True:
    valid, message, endAddress, rxCurrState, b = receive(clientSocket, bufferSize, rxCurrState, b, userName)
    while not valid:
        valid, message, endAddress, rxCurrState, b = receive(clientSocket, bufferSize, rxCurrState, b, userName)
    if message.decode().startswith("NAME_OF_FILE: "):
        message = message.decode()
        nome = message[14:]
        caminho = Path(__file__).parent / nome
        print(f'[{userName}]: Pacote recebido do destino {endAddress} com nome do arquivo "{nome}". Preparando para receber o conteúdo do arquivo e escrevê-lo no arquivo "{nome}".')
    else:
        print(f'[{userName}]: Pacote recebido do destino {endAddress}, mas conteúdo do pacote não é o nome do arquivo. DEU MUITO ERRADO!')
        exit(1)
    with open(caminho, 'wb') as arquivo_alterado:
        while True:
            valid, message, endAddress, rxCurrState, b = receive(clientSocket, bufferSize, rxCurrState, b, userName)
            while not valid:
                valid, message, endAddress, rxCurrState, b = receive(clientSocket, bufferSize, rxCurrState, b, userName)
            if message == b'EOF':
                print(f'[{userName}]: Pacote EOF recebido do destino {endAddress}. Arquivo "{nome}" recebido e finalizado!')
                break
            else:
                arquivo_alterado.write(message)
                print(f'[{userName}]: Pacote de conteúdo recebido do destino {endAddress}. Escrevendo conteúdo no arquivo "{nome}".')
    break

clientSocket.close()
