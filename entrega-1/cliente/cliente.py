from socket import *
from pathlib import Path



# ================================== Configuração Inicial ==================================


serverName = 'localhost'       # localhost -> cliente e servidor rodam na mesma máquina
bufferSize = 1024              # tamanho de um pacote
serverPort = 12000             # definição da porta utilizada
clientSocket = socket(AF_INET, SOCK_DGRAM)           # socket do cliente, definido IPv4 e UDP



# ============================== Enviando Arquivo ao Servidor ==============================


nome = 'assubiu.ogg'  # nome do arquivo que queremos abrir
arquivo = Path(nome)  # caminho para o arquivo que queremos abrir
a = 1                 # variável contadora que indica o número do pacote


with open(arquivo, 'rb') as f:  # abrimos o arquivo e lemos o conteúdo em formato de bytes (leitura binária)
    message = (str(arquivo)).encode()  # nome do arquivo em bytes, para que possamos enviá-lo
    clientSocket.sendto(message, (serverName, serverPort))  # pacote que contém o nome do arquivo --UDP-> servidor

    message = f.read(bufferSize)  # leitura do primeiro pacote armazenado no arquivo
    while (message):
        print(a)  # enquanto estivermos lendo o conteúdo do arquivo, printamos o número do pacote
        a+=1
        #print(message)
        clientSocket.sendto(message, (serverName, serverPort))  # envia o pacote lido ao servidor
        message = f.read(bufferSize)  # leitura do próximo pacote para a nova iteração do loop
    
    clientSocket.sendto(b'EOF', (serverName, serverPort)) # como o UDP não fecha a conexão automaticamente, enviamos o EOF para indicar que devemos finalziar



# ============================= Recebendo Arquivo do Servidor =============================


# cliente aguarda o servidor responder 
nome, serverAddress = clientSocket.recvfrom(bufferSize)  # guardará: nome <- novo nome | serverAdress <- IP + porta do servidor
nomeAlterado = nome.decode()  # converte o novo nome de byte para string
caminho = Path(nomeAlterado)  # caminho para o novo arquivo com nome modificado

message, serverAddress = clientSocket.recvfrom(bufferSize)  # aguarda receber o primeiro pacote do servidor
with open(caminho, 'wb') as arquivoAlterado:  # abre/cria o arquivo com o nome modificado para escrita em binário
    while (message != b'EOF'):  
        if (message != b'EOF'):  # verificação para não escrever o EOF no novo arquivo
            arquivoAlterado.write(message)  # escreve o pacote no novo arquivo

        message, serverAddress = clientSocket.recvfrom(bufferSize)  # leitura do próximo pacote para a nova iteração do loop

