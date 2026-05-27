# [CIN0018] Fundamentos de Redes de Computadores - Grupo 1
## Equipe
- André Lima Jordão {alj}
- Ludmila Cabral Lopes Magnani {lclm}
- Marina Rodas Sales {mrs5}
- Fernando Luis Campelo dos Anjos {flca}

## Entrega 1
A pasta "entrega-1" corresponde à primeira entrega do projeto da disciplina de Fundamentos de Redes de Computadores. Ele contém duas pastas respectivas ao programa do cliente e servidor. O programa do cliente possui uma variável de nome de arquivo a ser transmitido (nome = ''), fora quatro exemplos de arquivos (um texto, duas imagens e um de som) que podem ser escolhidos para testar a conexão.
O cliente enviará somente o pacote especificado na variavel de caminho (nome = ''), para testar cada um dos arquivos modelos é necessário especificar seu nome e executar novamente o código do cliente.
Espera-se do programa:
1. Entre, no terminal, até a pasta servidor, execute o programa do servidor.py na pasta servidor e aguarde a mensagem de inicialização;
2. Entre, no terminal, até a pasta cliete, abra o código de cliente.py na pasta cliente e especifique o nome e a extensão do arquivo (e.g.: nome = texto.txt) a ser enviado;
3. Execute o programa cliente.py com o programa servidor.py ainda em execução;
4. Cliente irá enviar o nome do arquivo e o arquivo em si em pacotes, finalizando a transmissão com um especificador de final de arquivo EOF;
5. Cliente irá esperar o retorno do servidor com o novo título do arquivo;
6. Servidor irá receber o nome do arquivo, criar localmente um arquivo com o prefixo "leilao_" e o nome do arquivo recebido e escrever os dados recebidos em ordem;
7. Servidor, ao detectar EOF, irá fechar o arquivo e reenviar a nova versão com o título alterado na seguinte ordem: irá enviar o nome do arquivo e o arquivo em si em pacotes, finalizando a transmissão com um especificador de final de arquivo EOF;
8. Cliente irá receber o nome do arquivo criar localmente um arquivo com nome do arquivo recebido e escrever os dados recebidos em ordem;
9. Cliente irá fechar o socket, para executar novamente é necessário reiniciar o programa do Cliente.

Pode-se executar o programa através do comando:
```make run```, se a ferramenta make estiver disponível na máquina.

## Entrega 2
### Explicação
A implementação do rdt3.0 é feito através de 2 funções que são idênticas entre o Cliente e Servidor: rtdsend e receive.
- ```rdtsend(message, socket, endAddressDst, bufferSize, count, txCurrState, lastPckg, userName = "Local")```: É a função que abstrai a transmissão para uma transmissão confiável. Ela opera emulando a máquina de estados, descrita pelo Kurose, do transmissor rdt3.0. O estado inicial é o WfC0fA (Wait from Call 0 from Above) e aguarda qualquer chamada da função e encapsula a mensagem fornecida (message, de tamanho de messageSize = bufferSize - headerSize) com o número de sequência, enviando para o endereço de destino (endAddressDst) o pacote e transiciona para o estado WfA0 (Wait for Ack 0) com a flag ready = False. Em WfA0 a máquina configura o timeout e aguarda o recebimento de qualquer mensagem, se a mensagem for o ACK 0 esperado, retorna um ready = True notificando a aplicação a possibilidade de uma nova transmissão e transiciona para o estado WfC1fA, senão faz nada. O funcionamento de WfC1fA e WfC1fA é análogo com o ACK 1.

- ```def receive(socket, bufferSize, rxCurrState, count, userName = "Local", headerSize = 1)```: É a função que abstrai o recebimento de pacotes de uma transmissão confiável. Ela opera emulando a máquina de estados, descrita pelo Kurose, do receptor rdt3.0. O estado inicial é o Wf0fB (Wait from 0 from Below), aguarda qualquer pacote chegando que tenha o cabeçalho (message[:headerSize]) igual a 0 (indicando número de sequência 0). Se sim, aciona valid, indicando para a aplicação a chegada de um pacote correto, envia para o mesmo remetente um ACK 0 e transiciona para o estado Wf1fB (Wait from 1 from Below), senão reenvia o ACK 1. O funcionamento de Wf1fB é análogo com o ACK 1 e número de sequência 1.

- Configurações: Cada função tem uma variável ```prob = 0.9```, ela é responsável por indicar a probabilidade de cada função enviar com sucesso um pacote, editar o valor, entre os valores 0 e 1, indica a taxa de envio correto entre 0% e 100%.

- Cabeçalho ```"NAME_OF_FILE: "```: É um cabeçalho escrito somente no componente de mensagem e enviado junto do nome do arquivo mais sua extensão. Ele serve para indicar ao destinatário o recebimento de um novo arquivo.

- Componente EOF: É um pacote extra que indica o envio final de um arquivo.

- Flags Ready e Valid: A flag Ready é um dos retornos da função ```rdtsend``` que indica para a aplicação quando a função está nos estados WfC0fA ou WfC1fA, ou seja, que está pronta para enviar um novo pacote. A flag Valid é um dos retornos da função ```receive``` que indica quando a função quer retornar algum valor válido, ou seja, message retornado deve somente ser levado em consideração se Valid = True.

### Instruções de execução
1. Entre, no terminal, até a pasta servidor, execute o programa do servidor.py na pasta servidor e aguarde a mensagem de inicialização;
2. Entre, no terminal, até a pasta cliente, abra o código de cliente.py na pasta cliente e especifique o nome e a extensão do arquivo (e.g.: nome = texto.txt) a ser enviado;
3. Execute o programa cliente.py com o programa servidor.py ainda em execução;
4. Cliente irá enviar o nome do arquivo e o arquivo em si em pacotes.
5. A biblioteca random foi utilizada para simular o envio no canal não confiável, no qual um pacote pode ser perdido (na nossa implemetação, simplesmente não é enviado). Há um a probabilidade de 10% de um pacote não ser enviado;
6. Se o arquivo não for enviado, ocorrerá um timeout da espera do ACK por parte do cliente, e ele tentará enviar o arquivo novamente;
7. Quando todo o arquivo for enviado, o cliente sinalizará ao servidor enviando um 'EOF';
8. Cliente irá esperar o retorno do servidor com o novo título do arquivo;
9. Servidor irá receber o nome do arquivo, criar localmente um arquivo com o prefixo "leilao_" e o nome do arquivo recebido;
10. A medida que recebe pacotes o servidor envia ACKs ao cliente confirmando o recebimento de pacotes, e vai escrevendo o conteúdo que receber no arquivo criado;
11. O servidor fará o mesmo processo de enviar para o cliente que o cliente executou anteriormente; 
12. Cliente fará o mesmo processo de recebimento do arquivo que o servidor fez anteriormente.

Pode-se executar o programa através do comando:
```make run```, se a ferramenta make estiver disponível na máquina.

