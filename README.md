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

## Entrega 3

### Explicação

A pasta "entrega-3" corresponde à terceira entrega do projeto da disciplina de Fundamentos de Redes de Computadores. Nesta etapa, foi implementado o sistema **AuctionCin**, um sistema de leilão online multiusuário, executado em linha de comando, utilizando o paradigma cliente-servidor.

Nesta entrega, o foco deixa de ser a transmissão simples de arquivos das etapas anteriores e passa a ser a aplicação final de leilão. Ainda assim, foi mantido o uso de comunicação UDP com transmissão confiável em camada de aplicação, baseada no protocolo RDT 3.0.

O sistema é composto por dois programas principais:

* `servidor.py`: responsável por manter o estado global do sistema, controlar os usuários conectados, cadastrar os itens do leilão, receber comandos dos clientes, validar lances, controlar o tempo de cada item e enviar alertas aos usuários conectados.
* `cliente.py`: responsável por permitir que o usuário interaja com o sistema por linha de comando, enviando comandos ao servidor e recebendo respostas, alertas de novos lances, mensagens de encerramento e o item arrematado, quando for o vencedor.

A aplicação foi implementada utilizando sockets UDP da biblioteca `socket` do Python. Como o UDP não garante entrega confiável, foi mantida uma camada de confiabilidade implementada na aplicação por meio das funções `rdtsend` e `receive`, que simulam o comportamento do RDT 3.0.


### Funcionamento geral do AuctionCin

O sistema permite que múltiplos clientes participem simultaneamente de leilões em tempo real. Para isso, o servidor mantém uma lista de usuários conectados e associa cada usuário a suas informações de endereço, porta e estado de transmissão.

No servidor, os itens do leilão são representados pela classe `Item`, que armazena as seguintes informações:

* `name`: nome do item;
* `id`: identificador numérico do item;
* `price`: preço atual do item;
* `bidder_username`: nome do usuário que possui o maior lance atual;
* `content`: conteúdo do arquivo correspondente ao item;
* `count`: quantidade restante de lances até o encerramento automático;
* `time`: tempo disponível do item no leilão;
* `filepath`: caminho local do arquivo associado ao item.

Os itens são gerados a partir de arquivos `.txt` presentes na pasta do servidor. A função `generateItems` verifica periodicamente a existência desses arquivos e cadastra cada um como um item disponível para leilão. Cada item recebe um identificador numérico, um preço inicial e tempo de disponibilidade de 60 segundos.

Cada item fica disponível até que uma das duas condições ocorra:

1. O tempo de 60 segundos se encerre; ou
2. O item receba 5 lances válidos.

Ao final do leilão, se nenhum usuário tiver dado lance, o servidor envia uma mensagem informando que o leilão foi encerrado sem lances. Se houver vencedor, o servidor informa todos os usuários conectados sobre o resultado e envia o conteúdo do item ao usuário com o maior lance.

### Estruturas principais do servidor

O servidor utiliza algumas estruturas globais para manter o estado da aplicação:

* `userList`: armazena os usuários conectados e suas informações de endereço, porta de alerta e estados de sequência;
* `itemsList`: armazena os itens disponíveis no leilão;
* `itemsTimeList`: armazena o tempo restante de cada item;
* `userListState`: armazena o estado RDT de recepção associado a cada cliente;
* `bidBuffer`: armazena os lances válidos que precisam gerar alerta para todos os usuários conectados.

Além do loop principal, o servidor executa threads auxiliares:

* Uma thread para gerar itens automaticamente a partir de arquivos `.txt`;
* Uma thread para controlar o tempo dos itens, processar novos lances e enviar alertas aos clientes.

### Estruturas principais do cliente

O cliente cria dois sockets UDP:

* `clientSocket`: utilizado para enviar comandos ao servidor e receber respostas diretas;
* `alertSocket`: utilizado para receber alertas enviados pelo servidor, como novos lances, encerramento de leilões e recebimento de itens.

Cada cliente é considerado um processo independente e, ao ser executado, recebe portas próprias. Assim, é possível abrir dois ou mais clientes simultaneamente em terminais diferentes.

O cliente também utiliza buffers e locks para lidar com concorrência entre as threads:

* `commandBuffer`: armazena comandos digitados pelo usuário;
* `alertBuffer`: armazena alertas recebidos do servidor;
* `itemBuffer`: armazena itens recebidos pelo usuário vencedor;
* `commandLock`, `alertLock` e `itemLock`: controlam o acesso concorrente aos respectivos buffers.

O cliente possui uma thread para capturar comandos digitados pelo usuário e outra thread para escutar alertas vindos do servidor.

### Protocolo da aplicação

Os comandos digitados pelo usuário são convertidos em mensagens internas do protocolo da aplicação. A função `commandToCall` realiza essa conversão.

Os principais comandos disponíveis são:

| Funcionalidade         | Comando no cliente        | Mensagem interna |
| ---------------------- | ------------------------- | ---------------- |
| Conectar ao sistema    | `login <nome_do_usuario>` | `T: LGN`         |
| Dar um lance           | `bid <id_item> <valor>`   | `T: BID`         |
| Ver itens e preços     | `list`                    | `T: LST`         |
| Ver quem está ganhando | `status <id_item>`        | `T: STS`         |
| Sair do sistema        | `logout`                  | `T: LGO`         |

A implementação utiliza o comando `status <id_item>` para consultar especificamente quem está vencendo determinado item.

### Funcionalidades implementadas

#### 1. Login de usuários

O usuário acessa o sistema pelo comando:

```bash
login <nome_do_usuario>
```

O servidor verifica se o nome escolhido já está em uso. Se não estiver, o usuário é adicionado à lista de usuários conectados e recebe a confirmação de que está online.

Caso já exista outro usuário com o mesmo nome, o servidor rejeita o login e retorna uma mensagem de erro.

#### 2. Impedimento de nomes duplicados

Dois usuários não podem estar conectados com o mesmo nome. O servidor percorre a lista de usuários conectados e verifica se o nome solicitado já existe. Se existir, retorna:

```text
T: LGN_FAIL; RSN: NAME_TAKEN
```

#### 3. Listagem de itens

O usuário pode listar os itens disponíveis com:

```bash
list
```

O servidor responde com os itens disponíveis, mostrando nome, id, preço atual, quantidade restante de lances e tempo restante.

#### 4. Consulta de status

O usuário pode consultar quem está vencendo determinado item com:

```bash
status <id_item>
```

Se ainda não houver lances, o cliente informa que o item está sem lances e mostra o valor inicial. Se já houver lance, mostra o maior lance e o usuário que está vencendo.

#### 5. Envio de lances

O usuário pode dar um lance com:

```bash
bid <id_item> <valor>
```

O servidor verifica se o item existe e se o valor informado é maior que o preço atual. Se o lance for válido, o servidor atualiza o preço do item, registra o usuário como vencedor parcial e decrementa o contador de lances restantes.

Caso o item não exista, o servidor retorna erro de item não encontrado. Caso o valor seja menor ou igual ao preço atual, o servidor retorna erro de lance muito baixo.

#### 6. Broadcast de novos lances

Quando um usuário dá um lance válido, todos os usuários conectados recebem uma mensagem de alerta informando quem deu o lance, sobre qual item e qual foi o novo valor.

Isso permite que os clientes acompanhem o leilão em tempo real, mesmo sem enviar comandos naquele momento.

#### 7. Encerramento do leilão

Cada item fica disponível por 60 segundos ou até receber 5 lances válidos. Quando uma dessas condições é atingida, o servidor encerra o leilão.

Se não houver vencedor, todos os usuários recebem uma mensagem de encerramento sem lances.

Se houver vencedor, todos os usuários recebem uma mensagem informando o usuário vencedor, o item arrematado e o valor final.

#### 8. Envio do item ao vencedor

Após o encerramento do leilão, o servidor envia o conteúdo do item para o usuário que deu o maior lance.

O cliente vencedor salva o item recebido em uma pasta local com o nome do usuário, no formato:

```text
cliente_<nome_do_usuario>
```

#### 9. Logout

O usuário pode sair do sistema com:

```bash
logout
```

Ao receber esse comando, o servidor remove o cliente da lista de usuários conectados. Após sair, o cliente precisa realizar login novamente para acessar as funcionalidades do sistema.

### Instruções de execução

1. Entre, no terminal, até a pasta da terceira entrega.

2. Entre na pasta do servidor.

3. Adicione à pasta do servidor um ou mais arquivos `.txt` para serem usados como itens do leilão. Por exemplo:

```text
carro.txt
notebook.txt
livro.txt
```

Cada arquivo `.txt` será interpretado como um item leiloável. O nome do arquivo, sem a extensão, será usado como nome do item.

Observação: após o encerramento do leilão, o servidor pode remover o arquivo local correspondente ao item. Portanto, recomenda-se usar arquivos de teste ou cópias dos arquivos originais.

4. Execute o servidor:

```bash
python servidor.py
```

ou, dependendo da instalação local do Python:

```bash
python3 servidor.py
```

5. Em outro terminal, entre na pasta do cliente e execute o primeiro cliente:

```bash
python cliente.py
```

ou:

```bash
python3 cliente.py
```

6. Em um terceiro terminal, entre novamente na pasta do cliente e execute o segundo cliente:

```bash
python cliente.py
```

ou:

```bash
python3 cliente.py
```

7. Em cada cliente, realize login com nomes diferentes:

Cliente 1:

```bash
login alice
```

Cliente 2:

```bash
login bruno
```

8. Para verificar os itens disponíveis, execute em um dos clientes:

```bash
list
```

9. Para consultar o status de um item, execute:

```bash
status 1
```

10. Para dar um lance, execute:

```bash
bid 1 150
```

11. Para testar a rejeição de lance inválido, tente enviar um lance menor ou igual ao valor atual:

```bash
bid 1 100
```

12. Para testar o broadcast, observe que, quando um cliente dá um lance válido, os demais clientes conectados recebem automaticamente uma mensagem de novo lance.

13. Para encerrar o leilão sem esperar os 60 segundos, envie 5 lances válidos para o mesmo item. Ao atingir o limite de lances, o servidor encerrará o leilão, anunciará o vencedor e enviará o item ao usuário que deu o maior lance.

14. Para sair do sistema, execute:

```bash
logout
```

### Testes recomendados

Para demonstrar o funcionamento da aplicação, recomenda-se realizar os seguintes testes:

#### 1. Teste de múltiplos clientes simultâneos

* Abrir um terminal para o servidor;
* Abrir dois terminais para clientes;
* Realizar login com dois nomes diferentes;
* Verificar que os dois clientes permanecem conectados simultaneamente.

#### 2. Teste de nome duplicado

Fazer login com um usuário, por exemplo:

```bash
login alice
```

Em outro cliente, tentar usar o mesmo nome:

```bash
login alice
```

O sistema deve recusar o segundo login.

#### 3. Teste de listagem

Executar:

```bash
list
```

O sistema deve exibir os itens disponíveis com nome, id, preço atual, lances restantes e tempo restante.

#### 4. Teste de status

Executar:

```bash
status 1
```

O sistema deve informar quem está vencendo o item ou indicar que ainda não houve lances.

#### 5. Teste de lance válido

Executar:

```bash
bid 1 150
```

O sistema deve registrar o lance e atualizar o preço do item.

#### 6. Teste de broadcast

Após um cliente dar um lance válido, verificar se o outro cliente conectado recebe automaticamente a mensagem de novo lance.

#### 7. Teste de lance inválido

Após um lance válido, tentar enviar um lance menor ou igual ao preço atual.

O sistema deve recusar o lance.

#### 8. Teste de encerramento por limite de lances

Enviar 5 lances válidos para o mesmo item.

O sistema deve encerrar o leilão automaticamente.

#### 9. Teste de envio do item ao vencedor

Após o encerramento do leilão, verificar se o cliente vencedor recebeu e salvou o item em sua pasta local.

#### 10. Teste de logout

Executar:

```bash
logout
```

O sistema deve remover o usuário da lista de usuários online.

### Exemplo de execução

Terminal do servidor:

```bash
python servidor.py
```

Cliente 1:

```bash
python cliente.py
login alice
list
bid 1 150
status 1
logout
```

Cliente 2:

```bash
python cliente.py
login bruno
status 1
bid 1 200
logout
```

Durante a execução, quando um cliente envia um lance válido, o outro cliente deve receber uma mensagem semelhante a:

```text
Novo Lance: alice deu R$ 150.00 no item carro
```

Ao final do leilão, os clientes devem receber uma mensagem indicando o vencedor, por exemplo:

```text
Item vendido: bruno arrematou carro por R$ 200.00
```

O cliente vencedor também deve receber e salvar o item localmente.

### Observações

* O servidor deve ser iniciado antes dos clientes.
* Para demonstrar múltiplos usuários, é necessário abrir pelo menos dois processos de cliente em terminais diferentes.
* Cada cliente recebe portas próprias automaticamente.
* O IP local pode ser utilizado como padrão para os testes.
* O sistema utiliza UDP, mas implementa confiabilidade em camada de aplicação por meio do RDT 3.0.
* A perda de pacotes é simulada pela variável `prob`, que pode ser ajustada no código para testar o comportamento da retransmissão.
* A aplicação foi projetada para ser executada em linha de comando.
* Para executar novamente um leilão com os mesmos itens, pode ser necessário recolocar os arquivos `.txt` na pasta do servidor, caso eles tenham sido removidos após o encerramento.

Pode-se executar o programa através do comando:

```bash
make run
```

se a ferramenta `make` estiver disponível na máquina e o Makefile correspondente estiver configurado. Caso contrário, recomenda-se executar manualmente o servidor e os clientes com:

```bash
python servidor.py
python cliente.py
```

