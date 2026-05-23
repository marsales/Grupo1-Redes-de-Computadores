from socket import *
from pathlib import Path

# ================================== Configuração Inicial ==================================


bufferSize = 1024   # tamanho de um pacote
serverPort = 12000  # definição da porta utilizada
serverSocket = socket(AF_INET, SOCK_DGRAM)  # socket do servidor, definido IPv4 e UDP
serverSocket.bind(('', serverPort))  # faz o registro de como contatar o servidor (qualquer formato + porta)

print('[Servidor]: Pronto para receber arquivos!')



# ============================= Recebendo Arquivo do Cliente ==============================


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


# ============================== Enviando Arquivo ao Cliente ==============================


    with open(caminho, 'rb') as arquivoAlterado:   # o servidor abre para leitura binária o novo arquivo que ele recém salvou
        message = arquivoAlterado.read(bufferSize)  # leitura do primeiro pacote do novo arquivo
        while message:
            serverSocket.sendto(message, clientAddress)  # envia o pacote ao cliente
            message = arquivoAlterado.read(bufferSize)  # leitura do próximo pacote para continuar a iterar o loop

        serverSocket.sendto(b'EOF', clientAddress)   # como o UDP não fecha a conexão automaticamente, enviamos o EOF para indicar que devemos finalziar
        print(f'[Servidor]: Arquivo "{nomeAlterado}" enviado para o cliente {clientAddress}.')

