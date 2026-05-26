from socket import *
from pathlib import Path
import random

# ======================================= Definições =======================================


WfC0fA, WfA0, WfC1fA, WfA1 = 1, 2, 3, 4         # estados possíveis do transmissor RDT 3.0
Wf0fB, Wf1fB = 5, 6                             # estados possíveis do receptor RDT 3.0


# =================================== Funções do RDT 3.0 ===================================

# Envio de pacotes ao servidor
def rdtsend(message, socket, endAddressDst, bufferSize, count, txCurrState, lastPckg, userName = "Local"):
    
    # Obs1.: a variável 'count' é apenas para fins de debug, para indicar o número do pacote que estamos enviando
    # Obs2.: message é o conteúdo do pacote que queremos enviar do tamanho de messageSize (bufferSize - headerSize) e deve ser do tipo bytes
    # Obs3.: txCurrState e lastPckg não devem ser sobrescritos fora da função rdtsend a não ser pelo retorno da própria função rdtsend
    
    prob = 0.9                                 # Probabilidade de pacote ser entregue com sucesso, para simular um canal não confiável
    timeoutSeconds = 1                         # Timeout de 1 segundo para o cliente esperar por um ACK do servidor
    WfC0fA, WfA0, WfC1fA, WfA1 = 1, 2, 3, 4    # Estados possíveis do transmissor RDT 3.0

    pckg = lastPckg                            # Último pacote enviado, para que possamos reenviá-lo em caso de timeout
    ready = False                              # Se o cliente está pronto para enviar o próximo pacote (após receber o ACK do servidor)
    txNextState = txCurrState                  # A priori, o estado se mantém o mesmo

    match txCurrState:

        # ----------- Se ele está esperando chamada 0 da aplicação -----------
        case 1: #WfC0fA

            # Envio do pacote
            print(f'[{userName}]: Enviando pacote {count} de SeqNum 0 para o destino {endAddressDst}.')
            pckg = "0".encode() + message  # pacote que contém o nome do arquivo ---UDP---> destino
            
            # Simulação de não-confiabilidade
            if (random.random() < prob):
                socket.sendto(pckg, endAddressDst)
            count += 1

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
                if endAddress == endAddressDst and ack.decode() == "ACK0":
                    print(f'[{userName}]: ACK0 recebido do destino {endAddress}.')

                    # Cliente pronto para enviar novos pacotes, transiciona para estado de esperar chamada 1
                    ready = True
                    txNextState = WfC1fA

            # ...exceto se tiver ocorrido timeout
            except timeout:

                # Reenvio do pacote
                print(f'[{userName}]: Timeout esperando ACK0. Reenviando pacote.')
                if(random.random() < prob):
                    socket.sendto(pckg, endAddressDst)

        # ----------- Se ele está esperando chamada 1 da aplicação -----------
        case 3: #WfC1fA

            # Envio do pacote
            print(f'[{userName}]: Enviando pacote {count} de SeqNum 1 para o destino {endAddressDst}.')
            pckg = "1".encode() + message  # pacote que contém o nome do arquivo --UDP-> destino
            
            # Simulação de não-confiabilidade
            if(random.random() < prob):
                socket.sendto(pckg, endAddressDst)
            count += 1

            # Transição para o estado de esperar ACK 1
            txNextState = WfA1   

        # ------------------- Se ele está esperando ACK 1 -------------------
        case 4: #WfA1

            # Timeout para esperar o ACK do servidor
            socket.settimeout(timeoutSeconds)
            
            # Tenta receber ACK do servidor...
            try:
                ack, endAddress = socket.recvfrom(bufferSize) 

                # Se recebeu ACK 0 do servidor
                if endAddress == endAddressDst and ack.decode() == "ACK1":
                    print(f'[{userName}]: ACK1 recebido do destino {endAddress}.')

                    # Cliente pronto para enviar novos pacotes, transiciona para estado de esperar chamada 0
                    ready = True
                    txNextState = WfC0fA

            # ...exceto se tiver ocorrido timeout
            except timeout:

                # Reenvio do pacote
                print(f'[{userName}]: Timeout esperando ACK1. Reenviando pacote.')
                if(random.random() < prob):
                    socket.sendto(pckg, endAddressDst)

    # Retornar as novas variáveis
    return txNextState, pckg, ready, count



# Recebimento de pacotes do servidor
def receive(socket, bufferSize, rxCurrState, count, userName = "Local", headerSize = 1):
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
                    print(f'[{userName}]: Pacote {count} de SeqNum {seqNum} recebido do destino {endAddress}. Enviando ACK0.')
                    count += 1
                    if(random.random() < prob):
                        socket.sendto("ACK0".encode(), endAddress)  # enviamos o ACK0
                    message = content
                    endAddress = endAddress
                    valid = True
                    rxNextState = Wf1fB

                # Se recebeu pacote 1
                else:
                    # Reenviamos ACK 1 e 
                    print(f'[{userName}]: Pacote {count} de SeqNum {seqNum} recebido do destino {endAddress}, mas SeqNum esperado era 0. Ignorando pacote e reenviando ACK1.')
                    if(random.random() < prob):
                        socket.sendto("ACK1".encode(), endAddress)  # reenviamos o ACK1, pois o pacote recebido é duplicado
            
            # ...exceto se tiver ocorrido timeout
            except timeout:
                pass

        # Se está esperando pacote 1
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

serverName = 'localhost'                                    # Cliente e servidor rodam na mesma máquina
serverPort = 12000                                          # Nº da porta utilizada
serverAddress = (gethostbyname(serverName), serverPort)     # Endereço do servidor
bufferSize = 1024                                           # Tamanho de um pacote
headerSize = 1                                              # Tamanho do header do pacote (número de sequência)
messageSize = bufferSize - headerSize                       # Tamanho do conteúdo do pacote
userName = "Cliente"                                        # [DEBUG] Nome do cliente
a = 1                                                       # [DEBUG] Variável de controle de envio
b = 1                                                       # [DEBUG] Variável de controle de recebimento

clientSocket = socket(AF_INET, SOCK_DGRAM)                  # Socket do cliente, definido IPv4 e UDP

txCurrState = WfC0fA                                        # Estado atual de transmissão
rxCurrState = Wf0fB                                         # Estado atual de recepção



# ================================= Enviando Arquivo ao Servidor =================================

lastPckg = None             # Último pacote enviado, para que possamos reenviá-lo em caso de timeout
hasMessageToSend = True     # Se ainda temos mensagens para enviar
ready = True                # Se o cliente está pronto para enviar o próximo pacote (após receber o ACK do servidor)

# ALTERAR NOME DO ARQUIVO AQUI vvvvvvv
nome = 'canario.webp'

# Caminho para o arquivo
arquivo = Path(__file__).parent / nome  

# Verificação de erro
if not arquivo.is_file():
    print(f'[{userName}]: O arquivo "{nome}" não existe. Verifique se o nome do arquivo e o caminho estão corretos.')
    exit(1)

# A primeira mensagem enviada sempre será o nome do arquivo -> Indicado por "NAME_OF_FILE"
message = f"NAME_OF_FILE: {nome}".encode()  

# Abrir o arquivo no modo leitura binária
with open(arquivo, 'rb') as f:
    print(f'[{userName}]: Preparando para enviar o arquivo "{nome}" para o destino {serverAddress}.')
    
    # Enquanto há mensagem a enviar, enviamos e obtemos a próxima mensagem
    while message:
        txCurrState, lastPckg, ready, a = rdtsend(message, clientSocket, serverAddress, bufferSize, a, txCurrState, lastPckg, userName)
        if ready:
            message = f.read(messageSize)

    # Quando acabarem as mensagens, enviamos "EOF" para sinalizar o fim do arquivo
    message = "EOF".encode()
    txCurrState, lastPckg, ready, a = rdtsend(message, clientSocket, serverAddress, bufferSize, a, txCurrState, lastPckg, userName)

    # Reenvio do EOF até ready ser true
    while ready == False:
        txCurrState, lastPckg, ready, a = rdtsend(message, clientSocket, serverAddress, bufferSize, a, txCurrState, lastPckg, userName)

    # Envio com sucesso
    print(f'[{userName}]: Arquivo "{nome}" enviado para o destino {serverAddress} e finalizado!')



# ================================= Recebendo Arquivo do Servidor =================================

while True:

    # O cliente ficará tentando receber dados do servidor
    # Quando receber algo, valid = true
    valid, message, endAddress, rxCurrState, b = receive(clientSocket, bufferSize, rxCurrState, b, userName)
    while not valid:
        valid, message, endAddress, rxCurrState, b = receive(clientSocket, bufferSize, rxCurrState, b, userName)

    # Se recebeu o nome do arquivo, o extrai e cria um arquivo com esse nome em sua pasta
    if message.decode().startswith("NAME_OF_FILE: "):
        message = message.decode()
        nome = message[14:]
        caminho = Path(__file__).parent / nome
        print(f'[{userName}]: Pacote recebido do destino {endAddress} com nome do arquivo "{nome}". Preparando para receber o conteúdo do arquivo e escrevê-lo no arquivo "{nome}".')
    
    # Se não, é porque recebeu conteúdo do arquivo antes de receber o nome (comportamento não esperado)
    else:
        print(f'[{userName}]: Pacote recebido do destino {endAddress}, mas conteúdo do pacote não é o nome do arquivo. DEU MUITO ERRADO!')
        exit(1)

    # Após receber o nome e ter criado o arquivo novo em brando,
    # o abrimos no modo de escrita para construí-lo a medida que 
    # recebemos mensagens do servidor
    with open(caminho, 'wb') as arquivo_alterado:
        while True:

            # Tentar receber mensagens do servidor, da mesma forma que antes
            valid, message, endAddress, rxCurrState, b = receive(clientSocket, bufferSize, rxCurrState, b, userName)
            while not valid:
                valid, message, endAddress, rxCurrState, b = receive(clientSocket, bufferSize, rxCurrState, b, userName)
            
            # Se recebeu um "EOF", é porque acabou o arquivo -> podemos parar de receber
            if message == b'EOF':
                print(f'[{userName}]: Pacote EOF recebido do destino {endAddress}. Arquivo "{nome}" recebido e finalizado!')
                break

            # Se não, é porque recebeu conteúdo do arquivo -> escrevê-lo no endereço criado
            else:
                arquivo_alterado.write(message)
                print(f'[{userName}]: Pacote de conteúdo recebido do destino {endAddress}. Escrevendo conteúdo no arquivo "{nome}".')
    
    # Quando acabar de escrever no endereço criado, pode finalizar a recepção
    break


# Fechamento do socket do cliente
clientSocket.close()
