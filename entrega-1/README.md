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
2. Entre, no terminal, até a pasta cliete, abra o código de cliente.py na pasta cliente e especifique o nome e a extensão do arquivo (e.g.: nome = textp.txt) a ser enviado;
3. Execute o programa cliente.py com o programa servidor.py ainda em execução;
4. Cliente irá enviar o nome do arquivo e o arquivo em si em pacotes, finalizando a transmissão com um especificador de final de arquivo EOF;
5. Cliente irá esperar o retorno do servidor com o novo título do arquivo;
6. Servidor irá receber o nome do arquivo, criar localmente um arquivo com o prefixo "leilao_" e o nome do arquivo recebido e escrever os dados recebidos em ordem;
7. Servidor, ao detectar EOF, irá fechar o arquivo e reenviar a nova versão com o título alterado na seguinte ordem: irá enviar o nome do arquivo e o arquivo em si em pacotes, finalizando a transmissão com um especificador de final de arquivo EOF;
8. Cliente irá receber o nome do arquivo criar localmente um arquivo com nome do arquivo recebido e escrever os dados recebidos em ordem;
9. Cliente irá fechar o socket, para executar novamente é necessário reiniciar o programa do Cliente.

Pode-se executar o programa através do comando:
```make run```, se a ferramenta make estiver disponível na máquina.
