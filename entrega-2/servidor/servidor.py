from socket import *
from pathlib import Path
import random


# ======================================= Definições =======================================


WfC0fA, WfA0, WfC1fA, WfA1 = 1, 2, 3, 4         # estados possíveis do transmissor RDT 3.0
Wf0fB, Wf1fB = 5, 6                             # estados possíveis do receptor RDT 3.0


# =================================== Funções do RDT 3.0 ===================================


# Envio de pacotes ao cliente
def rdtsend(message, socket, endAddressDst, bufferSize, count, txCurrState, lastPckg, userName = "Local"):
    
    # Obs1.: a variável 'count' é apenas para fins de debug, para indicar o número do pacote que estamos enviando
    # Obs2.: message é o conteúdo do pacote que queremos enviar do tamanho de messageSize (bufferSize - headerSize) e deve ser do tipo bytes
    # Obs3.: txCurrState e lastPckg não devem ser sobrescritos fora da função rdtsend a não ser pelo retorno da própria função rdtsend
    
    prob = 0.9                                  # Probabilidade de pacote ser entregue com sucesso, para simular um canal não confiável
    timeoutSeconds = 1                          # Timeout de 1 segundo para o cliente esperar por um ACK do servidor
    WfC0fA, WfA0, WfC1fA, WfA1 = 1, 2, 3, 4     # Estados possíveis do transmissor RDT 3.0
    pckg = lastPckg                             # Último pacote enviado, para que possamos reenviá-lo em caso de timeout
    ready = False                               # Se o cliente está pronto para enviar o próximo pacote (após receber o ACK do servidor)
    txNextState = txCurrState                   # A priori, o estado se mantém o mesmo

    match txCurrState:

        # ----------- Se ele está esperando chamada 0 da aplicação -----------
        case 1: #WfC0fA

            # Envio do pacote
            print(f'[{userName}]: Enviando pacote {count} de SeqNum 0 para o destino {endAddressDst}.')
            pckg = "0".encode() + message  # pacote que contém o nome do arquivo --UDP-> destino
            
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
                ack, endAddress = socket.recvfrom(bufferSize)  # aguardamos o ACK do destino
                
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
            if (random.random() < prob):
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
                ack, endAddress = socket.recvfrom(bufferSize)  # aguardamos o ACK do destino
                
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
                if (random.random() < prob):
                    socket.sendto(pckg, endAddressDst)

    # Retornar as novas variáveis
    return txNextState, pckg, ready, count


# Recebimento de pacotes do servidor
def receive(socket, bufferSize, rxCurrState, count, userName = "Local", headerSize = 1):
    prob = 0.9                     # Probabilidade de pacote ser entregue com sucesso, para simular um canal não confiável [0 a 1]
    Wf0fB, Wf1fB = 5, 6            # Estados possíveis do receptor RDT 3.0
    message = None                 # Conteúdo do pacote recebido, caso ele seja válido
    endAddress = None              # Endereço do remetente do pacote recebido, caso ele seja válido
    valid = False                  # Se o pacote recebido é válido (ou seja, tem o SeqNum esperado e chegou algo)
    rxNextState = rxCurrState      # A priori, o estado se mantém o mesmo

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
                    print(f'[{userName}]: Pacote {count} de SeqNum {seqNum} recebido do destino {endAddress}, mas SeqNum esperado era 0. Ignorando pacote e reenviando ACK1.')
                    if(random.random() < prob):
                        socket.sendto("ACK1".encode(), endAddress)  # reenviamos o ACK1, pois o pacote recebido é duplicado
            
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
                    print(f'[{userName}]: Pacote {count} de SeqNum {seqNum} recebido do destino {endAddress}. Enviando ACK1.')
                    count += 1
                    if(random.random() < prob):
                        socket.sendto("ACK1".encode(), endAddress)  # enviamos o ACK1
                    message = content
                    endAddress = endAddress
                    valid = True
                    rxNextState = Wf0fB

                # Se recebeu pacote 0
                else:
                    # Reenviamos ACK 0
                    print(f'[{userName}]: Pacote {count} de SeqNum {seqNum} recebido do destino {endAddress}, mas SeqNum esperado era 1. Ignorando pacote e reenviando ACK0.')
                    if(random.random() < prob):
                        socket.sendto("ACK0".encode(), endAddress)  # reenviamos o ACK0, pois o pacote recebido é duplicado
            
            # ...exceto se tiver ocorrido timeout
            except timeout:
                pass
    
    # Retornar as novas variáveis
    return valid, message, endAddress, rxNextState, count


# ================================== Configuração Inicial ==================================


bufferSize = 1024                             # Tamanho de um pacote
headerSize = 1                                # Tamanho do header do pacote, onde fica o SeqNum
messageSize = bufferSize - headerSize         # Tamanho do conteúdo do pacote
serverPort = 12000                            # Nº da porta utilizada
serverSocket = socket(AF_INET, SOCK_DGRAM)    # Socket do servidor, definido IPv4 e UDP
serverSocket.bind(('', serverPort))           # Registro de como contatar o servidor (qualquer formato + porta)
userName = "Servidor"                         # [DEBUG] Nome do usuário
a = 1                                         # [DEBUG] Variável de controle de envio
b = 1                                         # [DEBUG] Variável de controle de recebimento
txCurrState = WfC0fA                          # Estado atual de transmissão
rxCurrState = Wf0fB                           # Estado atual de recepção

print('[Servidor]: Pronto para receber arquivos!')

valid = False                                 # Flag de mensagem válida - SeqNum correto ✓
message = None                                # Variável de mensagem
endAddress = None                             # Endereço do destinatário
nome_alterado = None                          # 'leilao_' + Nome do arquivo recebido


# ============================= Recebendo Arquivo do Cliente =============================


while True:

    # O servidor ficará tentando receber dados do cliente
    # Quando receber algo, valid = true
    valid, message, endAddress, rxCurrState, b = receive(serverSocket, bufferSize, rxCurrState, b, userName)
    while not valid:
        valid, message, endAddress, rxCurrState, b = receive(serverSocket, bufferSize, rxCurrState, b, userName)
    
    # Se recebeu o nome do arquivo, o extrai e cria um arquivo com esse nome em sua pasta
    if message.decode().startswith("NAME_OF_FILE: "):
        message = message.decode()
        nome = message[14:]
        nome_alterado = 'leilao_' + nome
        caminho = Path(__file__).parent / nome_alterado
    
    # Se não, é porque recebeu conteúdo do arquivo antes de receber o nome (comportamento não esperado)
    else:
        print(f'[Servidor]: Pacote recebido do destino {endAddress}, mas conteúdo do pacote não é o nome do arquivo. DEU MUITO ERRADO!')
        exit(1)

    # Após receber o nome e ter criado o arquivo novo em brando,
    # o abrimos no modo de escrita para construí-lo a medida que 
    # recebemos mensagens do cliente
    with open(caminho, 'wb') as arquivo_alterado:
        while True:

            # Tentar receber mensagens do cliente, da mesma forma que antes
            valid, message, endAddress, rxCurrState, b = receive(serverSocket, bufferSize, rxCurrState, b, userName)
            while not valid:
                valid, message, endAddress, rxCurrState, b = receive(serverSocket, bufferSize, rxCurrState, b, userName)
            
            # Se recebeu um "EOF", é porque acabou o arquivo -> podemos parar de receber
            if message == b'EOF':
                print(f'[{userName}]: Pacote EOF recebido do destino {endAddress}. Arquivo "{nome}" recebido e finalizado!')
                break
            
            # Se não, é porque recebeu conteúdo do arquivo -> escrevê-lo no endereço criado
            else:
                arquivo_alterado.write(message)
                print(f'[{userName}]: Pacote de conteúdo recebido do destino {endAddress}. Escrevendo conteúdo no arquivo "{nome_alterado}".')


# ================================= Enviando Arquivo ao Cliente =================================    
    

    # Garantimos que o endereço do destino esteja no formato (IP, porta)
    endAddress = (gethostbyname(endAddress[0]), endAddress[1])

    # Abrir o arquivo no modo leitura binária 
    with open(caminho, 'rb') as arquivo_alterado:
        message = f"NAME_OF_FILE: {nome_alterado}".encode()
        
        # Enquanto há mensagem a enviar, enviamos e obtemos a próxima mensagem
        while message:
            txCurrState, lastPckg, ready, a = rdtsend(message, serverSocket, endAddress, bufferSize, a, txCurrState, None, userName)
            while not ready:
                txCurrState, lastPckg, ready, a = rdtsend(message, serverSocket, endAddress, bufferSize, a, txCurrState, lastPckg, userName)
            print(f'[{userName}]: Pacote de conteúdo enviado para o cliente {endAddress}.')
            message = arquivo_alterado.read(messageSize)
        
        # Quando acabarem as mensagens, enviamos "EOF" para sinalizar o fim do arquivo
        message = "EOF".encode()
        txCurrState, lastPckg, ready, a = rdtsend(message, serverSocket, endAddress, bufferSize, a, txCurrState, None, userName)
        
        # Reenvio do EOF até ready ser true
        while not ready:
            txCurrState, lastPckg, ready, a = rdtsend(message, serverSocket, endAddress, bufferSize, a, txCurrState, lastPckg, userName)
        
        # Envio com sucesso
        print(f'[{userName}]: Arquivo "{nome_alterado}" enviado para o cliente {endAddress}.')
