# [CIN0018] Fundamentos de Redes de Computadores - Grupo 1
## Equipe
- André Lima Jordão {alj}
- Ludmila Cabral Lopes Magnani {lclm}
- Marina Rodas Sales {mrs5}
- Fernando Luis Campelo dos Anjos {flca}

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
12. Cliente fará o mesmo processo de recebimento do arquivo que o servidor fez anteriormente.

Pode-se executar o programa através do comando:
```make run```, se a ferramenta make estiver disponível na máquina.
