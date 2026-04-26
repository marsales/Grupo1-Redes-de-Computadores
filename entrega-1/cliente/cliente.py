from socket import *
from pathlib import Path

serverName = 'localhost'
bufferSize = 1024
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_DGRAM)

nome = 'assubiu.ogg'  # arquivo que queremos abrir
arquivo = Path(nome)
a = 1
with open(arquivo, 'rb') as f:
    message = (str(arquivo)).encode()
    clientSocket.sendto(message, (serverName, serverPort))

    message = f.read(bufferSize)
    while (message):
        print(a)
        a+=1
        #print(message)
        clientSocket.sendto(message, (serverName, serverPort))
        message = f.read(bufferSize)
    clientSocket.sendto(b'EOF', (serverName, serverPort))


nome, serverAddress = clientSocket.recvfrom(bufferSize)
nomeAlterado = nome.decode()
caminho = Path(nomeAlterado)

message, serverAddress = clientSocket.recvfrom(bufferSize)
with open(caminho, 'wb') as arquivoAlterado:
    while (message != b'EOF'):
        if (message != b'EOF'):
            arquivoAlterado.write(message)
        message, serverAddress = clientSocket.recvfrom(bufferSize)

