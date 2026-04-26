from socket import *
from pathlib import Path

bufferSize = 1024
serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))

print('The server is ready to receive')


while True:
    nome, clientAddrress = serverSocket.recvfrom(bufferSize)
    nomeAlterado = 'leilao_' + nome.decode()
    caminho = Path(nomeAlterado)

    with open(caminho, 'wb') as arquivoAlterado:
        message, clientAddress = serverSocket.recvfrom(bufferSize)
        while (message != b'EOF'):
            if (message != b'EOF'):
                arquivoAlterado.write(message)
            message, clientAddress = serverSocket.recvfrom(bufferSize)
            
        message = (nomeAlterado).encode()
        serverSocket.sendto(message, clientAddress)
        
    with open(caminho, 'rb') as arquivoAlterado:
        message = arquivoAlterado.read(bufferSize)
        while message:
            serverSocket.sendto(message, clientAddress)
            message = arquivoAlterado.read(bufferSize)
        serverSocket.sendto(b'EOF', clientAddress)

