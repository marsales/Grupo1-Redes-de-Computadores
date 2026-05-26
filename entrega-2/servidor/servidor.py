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


bufferSize = 1024                               # tamanho de um pacote
headerSize = 1                                  # tamanho do header do pacote, onde fica o SeqNum, definido como 1 byte para podermos codificar o SeqNum como "0" ou "1"
messageSize = bufferSize - headerSize           # tamanho do conteúdo do pacote, ou seja, o tamanho máximo de message que podemos enviar em um pacote
serverPort = 12000                              # definição da porta utilizada
serverSocket = socket(AF_INET, SOCK_DGRAM)      # socket do servidor, definido IPv4 e UDP
serverSocket.bind(('', serverPort))             # faz o registro de como contatar o servidor (qualquer formato + porta)
userName = "Servidor"                           # nome do usuário para fins de debug
a = 1                                           # variável de controle de envio (debug)
b = 1                                           # variável de controle de recebimento (debug)

txCurrState = WfC0fA
rxCurrState = Wf0fB

print('[Servidor]: Pronto para receber arquivos!')

valid = False                                   # flag de mensagem válida - SeqNum correto ✓
message = None                                  # variável de mensagem
endAddress = None                               # endereço do destinatário
nome_alterado = None


# ============================= Recebendo Arquivo do Cliente =============================


while True:
    valid, message, endAddress, rxCurrState, b = receive(serverSocket, bufferSize, rxCurrState, b, userName)
    while not valid:
        valid, message, endAddress, rxCurrState, b = receive(serverSocket, bufferSize, rxCurrState, b, userName)
    if message.decode().startswith("NAME_OF_FILE: "):
        message = message.decode()
        nome = message[14:]
        nome_alterado = 'leilao_' + nome
        caminho = Path(__file__).parent / nome_alterado
    else:
        print(f'[Servidor]: Pacote recebido do destino {endAddress}, mas conteúdo do pacote não é o nome do arquivo. DEU MUITO ERRADO!')
        exit(1)
    with open(caminho, 'wb') as arquivo_alterado:
        while True:
            valid, message, endAddress, rxCurrState, b = receive(serverSocket, bufferSize, rxCurrState, b, userName)
            while not valid:
                valid, message, endAddress, rxCurrState, b = receive(serverSocket, bufferSize, rxCurrState, b, userName)
            if message == b'EOF':
                print(f'[{userName}]: Pacote EOF recebido do destino {endAddress}. Arquivo "{nome}" recebido e finalizado!')
                break
            else:
                arquivo_alterado.write(message)
                print(f'[{userName}]: Pacote de conteúdo recebido do destino {endAddress}. Escrevendo conteúdo no arquivo "{nome_alterado}".')


# ================================= Enviando Arquivo ao Cliente =================================    

    endAddress = (gethostbyname(endAddress[0]), endAddress[1])  # garantimos que o endereço do destino esteja no formato (IP, porta)
    with open(caminho, 'rb') as arquivo_alterado:
        message = f"NAME_OF_FILE: {nome_alterado}".encode()
        while message:
            txCurrState, lastPckg, ready, a = rdtsend(message, serverSocket, endAddress, bufferSize, a, txCurrState, None, userName)
            while not ready:
                txCurrState, lastPckg, ready, a = rdtsend(message, serverSocket, endAddress, bufferSize, a, txCurrState, lastPckg, userName)
            print(f'[{userName}]: Pacote de conteúdo enviado para o cliente {endAddress}.')
            message = arquivo_alterado.read(messageSize)
        message = "EOF".encode()
        txCurrState, lastPckg, ready, a = rdtsend(message, serverSocket, endAddress, bufferSize, a, txCurrState, None, userName)
        while not ready:
            txCurrState, lastPckg, ready, a = rdtsend(message, serverSocket, endAddress, bufferSize, a, txCurrState, lastPckg, userName)
        print(f'[{userName}]: Arquivo "{nome_alterado}" enviado para o cliente {endAddress}.')
