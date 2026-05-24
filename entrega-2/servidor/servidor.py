from socket import *
from pathlib import Path
import random
# ======================================= Definições =======================================

WfC0fA, WfA0, WfC1fA, WfA1 = 1, 2, 3, 4         # estados possíveis do transmissor rdt3.0
Wf0fB, Wf1fB = 5, 6                             # estados possíveis do receptor rdt3.0

# =================================== Funções do rdt3.0 ===================================

# ATENÇÃO: Em WfA0 e WfA1, mesmo que o ack recebido seja o não esperado, recvfrom reseta o timeout, ou seja, quebra o paradigma do Kurose. Ver com os monitores
# se isso é um problema ou se é algo que pode ser ignorado, se for um problema, podemos utilizar a biblioteca time e fazer o controle do timeout manualmente

def rdtsend(message, socket, endName, endPort, bufferSize, a, txCurrState, lastPckg, userName = "Local"):
    # Obs.: a variável 'a' é apenas para fins de debug, para indicar o número do pacote que estamos enviando
    # Obs.: message é o conteúdo do pacote que queremos enviar do tamanho de messageSize (bufferSize - headerSize) e deve ser do tipo bytes
    # Obs.: txCurrState e lastPckg não devem ser sobrescritos fora da função rdtsend a não ser pelo retorno da própria função rdtsend
    prob = 0.9          # probabilidade de pacote ser entregue com sucesso, para simular um canal não confiável

    pckg = lastPckg     # variável que armazena o último pacote enviado, para que possamos reenviá-lo em caso de timeout
    ready = False       # variável booleana que indica se o cliente está pronto para enviar o próximo pacote (após receber o ACK do servidor)
    txNextState = txCurrState
    match txCurrState:
        case 1: #WfC0fA
            print(f'[{userName}]: Enviando pacote {a} de SeqNum 0 para o destino {endName}:{endPort}.')
            pckg = "0".encode() + message  # pacote que contém o nome do arquivo --UDP-> destino
            if(random.random() < prob):
                socket.sendto(pckg, (endName, endPort))
            a += 1
            txNextState = WfA0
        case 2: #WfA0
            try:
                ack, endAddress = socket.recvfrom(bufferSize)  # aguardamos o ACK do destino
                if ack.decode() == "ACK0":
                    print(f'[{userName}]: ACK0 recebido do destino {endAddress}.')
                    ready = True
                    txNextState = WfC1fA
            except timeout:
                print(f'[{userName}]: Timeout esperando ACK0. Reenviando pacote.')
                if(random.random() < prob):
                    socket.sendto(pckg, (endName, endPort))
        case 3: #WfC1fA
            print(f'[{userName}]: Enviando pacote {a} de SeqNum 1 para o destino {endName}:{endPort}.')
            pckg = "1".encode() + message  # pacote que contém o nome do arquivo --UDP-> destino
            if(random.random() < prob):
                socket.sendto(pckg, (endName, endPort))
            a += 1
            txNextState = WfA1   
        case 4: #WfA1
            try:
                ack, endAddress = socket.recvfrom(bufferSize)  # aguardamos o ACK do destino
                if ack.decode() == "ACK1":
                    print(f'[{userName}]: ACK1 recebido do destino {endAddress}.')
                    ready = True
                    txNextState = WfC0fA
            except timeout:
                print(f'[{userName}]: Timeout esperando ACK1. Reenviando pacote.')
                if(random.random() < prob):
                    socket.sendto(pckg, (endName, endPort))
    return txNextState, pckg, ready, a

def receive(socket, bufferSize, rxCurrState, userName = "Dedé", headerSize = 1):
    prob = 0.9                      # probabilidade de pacote ser entregue com sucesso, para simular um canal não confiável
    
    message = None                  # variavel que armazena o conteudo do pacote recebido, caso ele seja válido
    endAddress = None               # variavel que armazena o endereço do remetente do pacote recebido, caso ele seja válido
    valid = False                   # variavel booleana que indica se o pacote recebido é válido (ou seja, tem o SeqNum esperado e chegou algo)
    rxNextState = rxCurrState 
    match rxCurrState:
        case 5: #Wf0fB
            try:
                pckg, endAddress = socket.recvfrom(bufferSize)      # aguardamos o pacote do destino
                seqNum = pckg[:headerSize].decode()                 # extraímos o SeqNum do pacote do header
                content = pckg[headerSize:]                         # extraímos o conteúdo do pacote
                if seqNum == "0":
                    print(f'[{userName}]: Pacote {seqNum} recebido do destino {endAddress}. Enviando ACK0.')
                    if(random.random() < prob):
                        socket.sendto("ACK0".encode(), endAddress)      # enviamos o ACK0
                    message = content
                    endAddress = endAddress
                    valid = True
                    rxNextState = Wf1fB
                else:
                    print(f'[{userName}]: Pacote {seqNum} recebido do destino {endAddress}, mas SeqNum esperado era 0. Ignorando pacote e reenviando ACK1.')
                    if(random.random() < prob):
                        socket.sendto("ACK1".encode(), endAddress)      # reenviamos o ACK1, pois o pacote recebido é duplicado
            except timeout:
                pass
        case 6: #Wf1fB
            try:
                pckg, endAddress = socket.recvfrom(bufferSize)      # aguardamos o pacote do destino
                seqNum = pckg[:headerSize].decode()                 # extraímos o SeqNum do pacote do header
                content = pckg[headerSize:]                         # extraímos o conteúdo do pacote
                if seqNum == "1":
                    print(f'[{userName}]: Pacote {seqNum} recebido do destino {endAddress}. Enviando ACK1.')
                    if(random.random() < prob):
                        socket.sendto("ACK1".encode(), endAddress)      # enviamos o ACK1
                    message = content
                    endAddress = endAddress
                    valid = True
                    rxNextState = Wf0fB
                else:
                    print(f'[{userName}]: Pacote {seqNum} recebido do destino {endAddress}, mas SeqNum esperado era 1. Ignorando pacote e reenviando ACK0.')
                    if(random.random() < prob):
                        socket.sendto("ACK0".encode(), endAddress)      # reenviamos o ACK0, pois o pacote recebido é duplicado
            except timeout:
                pass
    return valid, message, endAddress, rxNextState


# ================================== Configuração Inicial ==================================


bufferSize = 1024   # tamanho de um pacote
serverPort = 12000  # definição da porta utilizada
serverSocket = socket(AF_INET, SOCK_DGRAM)  # socket do servidor, definido IPv4 e UDP
serverSocket.bind(('', serverPort))  # faz o registro de como contatar o servidor (qualquer formato + porta)
serverSocket.settimeout(360)  # timeout de 1 segundo para o servidor esperar por um pacote do cliente
userName = "Servidor"  # nome do usuário para fins de debug

txCurrState = 1
rxCurrState = 5

print('[Servidor]: Pronto para receber arquivos!')

valid = False   # flag de mensagem válida - SeqNum correto ✓
message = None   # variável de mensagem
endAddress = None   # andre lima joao


# ============================= Recebendo Arquivo do Cliente =============================
while True:
    valid, message, endAddress, rxCurrState = receive(serverSocket, bufferSize, rxCurrState, userName)
    while not valid:
        valid, message, endAddress, rxCurrState = receive(serverSocket, bufferSize, rxCurrState, userName)
    if message.decode().startswith("NAME_OF_FILE: "):
        message = message.decode()
        nome = message[14:]
        nome_alterado = 'leilao_' + nome
        caminho = Path(nome_alterado)
    else:
        print(f'[Servidor]: Pacote recebido do destino {endAddress}, mas conteúdo do pacote não é o nome do arquivo. DEU MUITO ERRADO!')
        exit(1)
    with open(caminho, 'wb') as arquivo_alterado:
        while True:
            valid, message, endAddress, rxCurrState = receive(serverSocket, bufferSize, rxCurrState, userName = "Servidor")
            while not valid:
                valid, message, endAddress, rxCurrState = receive(serverSocket, bufferSize, rxCurrState, userName = "Servidor")
            if message == b'EOF':
                print(f'[{userName}]: Pacote EOF recebido do destino {endAddress}. Arquivo "{nome}" recebido e finalizado!')
                break
            else:
                arquivo_alterado.write(message)
                print(f'[{userName}]: Pacote de conteúdo recebido do destino {endAddress}. Escrevendo conteúdo no arquivo "{nome_alterado}".')
            
'''
    while True:  # while true pois o servidor nunca deve fechar após atender um cliente
        nome, clientAddrress = serverSocket.recvfrom(bufferSize)  # recebe do cliente o pacote contendo o nome do arquivo que será enviado e guarda o endereço do cliente para respondê-lo
        nomeAlterado = 'leilao_' + nome.decode()  # pegamos a string do nome enviado pelo cliente e adicionamos leilão na frente
        print(f'[Servidor]: Recebendo arquivo "{nome.decode()}" do cliente {clientAddrress}.') 
        caminho = Path(nomeAlterado)  # definimos o caminho para o novo arquivo (leilão + nome)

        with open(caminho, 'wb') as arquivoAlterado:  # cria/abre o novo arquivo para escrita binária
            message, clientAddress = serverSocket.recvfrom(bufferSize)  # recebe o primeiro pacote do arquivo
            while (message != b'EOF'):
                if (message != b'EOF'):  # verificação para não escrever o EOF no novo arquivo
                    arquivoAlterado.write(message) # escreve o pacote no novo arquivo

                message, clientAddress = serverSocket.recvfrom(bufferSize)  # leitura do próximo pacote para a nova iteração do loop

            print(f'[Servidor]: Arquivo "{nome.decode()}" recebido!')
            # enviamos ao cliente o nome do novo arquivo
            # fizemos isso dentro desse bloco dado que era aqui onde estavam armazenadas as informações necessárias
            message = (nomeAlterado).encode()
            serverSocket.sendto(message, clientAddress)
            print(f'[Servidor]: Enviando nome do novo arquivo "{nomeAlterado}" para o cliente {clientAddress}.')
'''

# ============================== Enviando Arquivo ao Cliente ==============================
'''

    with open(caminho, 'rb') as arquivoAlterado:   # o servidor abre para leitura binária o novo arquivo que ele recém salvou
        message = arquivoAlterado.read(bufferSize)  # leitura do primeiro pacote do novo arquivo
        while message:
            serverSocket.sendto(message, clientAddress)  # envia o pacote ao cliente
            message = arquivoAlterado.read(bufferSize)  # leitura do próximo pacote para continuar a iterar o loop

        serverSocket.sendto(b'EOF', clientAddress)   # como o UDP não fecha a conexão automaticamente, enviamos o EOF para indicar que devemos finalizar
        print(f'[Servidor]: Arquivo "{nomeAlterado}" enviado para o cliente {clientAddress}.')

'''