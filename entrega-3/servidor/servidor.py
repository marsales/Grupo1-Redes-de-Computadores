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


# ================================== Configuração Inicial ==================================


bufferSize = 1024                             # Tamanho de um pacote
headerSize = 1                                # Tamanho do header do pacote, onde fica o SeqNum
messageSize = bufferSize - headerSize         # Tamanho do conteúdo do pacote
serverPort = 12000                            # Nº da porta utilizada
serverSocket = socket(AF_INET, SOCK_DGRAM)    # Socket do servidor, definido IPv4 e UDP
serverSocket.bind(('', serverPort))           # Registro de como contatar o servidor (qualquer formato + porta)

userList = {}                                 # Dicionário para armazenar os usuários logados, no formato {username: (ip, port)}

#TODO: ABSOLUTAMENTE TUDO!