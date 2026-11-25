# so-mensageria · Fila de guias do Rota Vital

Atividade individual 2 (Mensageria) · Infraestrutura de Software · ADS · CESAR School · 2026.2

Comunicação assíncrona com fila: um **produtor** publica 21 pedidos de guia de transporte
(20 válidos e 1 sem `requisicaoId`) e um ou mais **consumidores** retiram, geram a guia e
só então confirmam (apagam) a mensagem. Com isso observei:

- a mensagem só sai da fila quando o consumidor confirma;
- dois consumidores dividem o trabalho;
- a fila padrão entrega **pelo menos uma vez** e não garante ordem;
- uma falha faz a mensagem voltar depois do **visibility timeout** (15 s);
- (opcional) depois de 3 tentativas a mensagem inválida vai para uma **DLQ**.

## Caminho escolhido

**Caminho A: ElasticMQ local** em Docker, que implementa a mesma API do Amazon SQS.
Tudo roda no computador, sem conta na AWS. O mesmo código funciona no Amazon SQS
trocando só o endereço (ver [Caminho B](#caminho-b-amazon-sqs)).

## Estrutura

```
.
├── produtor.py            # Publica R-001..R-020 + 1 mensagem inválida
├── consumidor.py          # receive → processa → delete (só se deu certo)
├── requirements.txt       # boto3
├── scripts/
│   ├── _comum.sh              # Credenciais falsas, endpoint e ajuste do Git Bash
│   ├── 00-subir-elasticmq.sh  # docker run do ElasticMQ (API 9324, painel 9325)
│   ├── 01-criar-fila.sh       # Fila "guias" com VisibilityTimeout=15
│   ├── 02-estado-fila.sh      # Mensagens visíveis e em voo
│   ├── 03-limpar-fila.sh      # purge-queue entre um teste e outro
│   ├── 04-criar-fila-dlq.sh   # (opcional) "guias-com-dlq" → "guias-dlq", maxReceiveCount=3
│   ├── 05-ler-dlq.sh          # (opcional) mostra o que caiu na DLQ
│   ├── teste_automatico.py    # Roda os 3 cenários de ponta a ponta e salva as saídas
│   └── testar-tudo.bat        # Atalho do teste automático no Windows (duplo clique)
└── evidencias/            # Prints e saídas (teste-automatico/ = logs em texto)
```

## Mudanças em relação ao enunciado

O código do produtor e do consumidor é o do enunciado, com três acréscimos pequenos:

1. **Fila e endpoint por variável de ambiente.** `FILA` (padrão `guias`) e `SQS_ENDPOINT`
   (padrão `http://localhost:9324`). Assim o mesmo código serve para a fila com DLQ
   (`FILA=guias-com-dlq`) e para o Amazon SQS (`SQS_ENDPOINT=` vazio).
2. **Hora e PID em todas as linhas do consumidor**, para mostrar nos prints e no vídeo
   que a mensagem inválida volta a cada 15 s e qual consumidor pegou cada mensagem.
3. **`flush=True` nos `print`**, para a saída aparecer na hora no terminal do Git Bash.

## Como rodar (Caminho A)

### Pré-requisitos

- Docker Desktop
- AWS CLI v2
- Python 3.12 e boto3: `pip install -r requirements.txt`
- No Windows, usar o **Git Bash** (ou WSL) para os scripts.

### Passo 2. Subir a fila

Terminal 1 (deixar aberto):

```bash
bash scripts/00-subir-elasticmq.sh
```

Terminal 2:

```bash
bash scripts/01-criar-fila.sh      # cria "guias" e mostra VisibilityTimeout = 15
```

O painel do ElasticMQ fica em <http://localhost:9325> e mostra as filas e a contagem de
mensagens.

### Passo 5.1. Um consumidor

```bash
python consumidor.py               # terminal 2
python produtor.py                 # terminal 3
```

Esperado: as 20 guias `G-R-001` a `G-R-020` aparecem, e a mensagem inválida reaparece a
cada ~15 s com `ApproximateReceiveCount` subindo (1, 2, 3…). Parar com `Ctrl+C`.

### Passo 5.2. Dois consumidores

```bash
bash scripts/03-limpar-fila.sh     # tira a inválida da rodada anterior
python consumidor.py               # terminal 2 (PID A)
python consumidor.py               # terminal 3 (PID B)
python produtor.py                 # terminal 4
```

Anotar quais `R-xxx` cada PID processou e se a ordem foi mantida.

### Opcional: DLQ

```bash
bash scripts/04-criar-fila-dlq.sh
FILA=guias-com-dlq python consumidor.py
FILA=guias-com-dlq python produtor.py
# depois de 3 falhas (~30 s) a inválida some da fila principal:
bash scripts/02-estado-fila.sh guias-com-dlq
bash scripts/05-ler-dlq.sh         # ela está na guias-dlq
```

### Teste automático (conferência rápida)

Com o Docker aberto e a AWS CLI instalada, `python scripts/teste_automatico.py` (ou duplo
clique em `scripts\testar-tudo.bat`) sobe o ElasticMQ, cria a fila pela AWS CLI e roda os
três cenários (um consumidor, dois consumidores, DLQ) em ~2,5 min. As saídas ficam em
`evidencias/teste-automatico/`. Ele não substitui os prints e o vídeo: serve para conferir
que tudo funciona antes de gravar.

## Resultados

⟨Preencher com a sua execução e apontar os prints de `evidencias/`.⟩

| Teste | O que observei | Evidência |
|---|---|---|
| Fila criada | `VisibilityTimeout = 15` | `evidencias/01-fila.png` |
| 1 consumidor | 20 guias geradas; inválida voltou às ⟨hh:mm:ss⟩, ⟨+15 s⟩, ⟨+30 s⟩ com contador 1, 2, 3 | `evidencias/02-um-consumidor.png` |
| 2 consumidores | PID ⟨A⟩ processou ⟨n⟩ mensagens, PID ⟨B⟩ processou ⟨m⟩ | `evidencias/03-dois-consumidores.png` |
| DLQ (opcional) | inválida saiu da fila principal após 3 recebimentos e apareceu na `guias-dlq` | `evidencias/04-dlq.png` |

## Respostas

**1. Por que o consumidor só apaga a mensagem depois de processar? O que aconteceria se
apagasse antes?**

Apagar é a confirmação de que o trabalho foi feito. Enquanto não apago, a mensagem só
fica invisível; se o consumidor cair ou der erro no meio, ela volta para a fila depois do
visibility timeout e outro consumidor tenta de novo. Se eu apagasse antes de processar e o
processamento falhasse (exceção, queda do processo, falta de energia), a mensagem já teria
sumido da fila e a guia nunca seria gerada: o pedido se perderia sem ninguém saber. Foi o
que vi com a mensagem inválida: como ela nunca foi apagada, continuou voltando.

**2. Com dois consumidores, como as mensagens se dividiram? A ordem foi mantida? O que a
documentação do SQS diz sobre ordem nas filas padrão?**

⟨Descrever a sua divisão: quantas e quais mensagens cada PID pegou.⟩ Cada `receive_message`
pega até 10 mensagens, então a divisão não é alternada uma a uma: cada consumidor pega um
lote, e quem estiver livre pega o próximo. A ordem global não foi mantida (cada consumidor
imprimiu uma sequência com "buracos", e os dois rodaram ao mesmo tempo). A documentação diz
que a fila padrão faz *best-effort ordering*: tenta preservar a ordem de envio, mas pode
entregar fora de ordem. Quem precisa de ordem estrita usa fila FIFO.

**3. A fila padrão garante entrega pelo menos uma vez, e a mesma mensagem pode chegar duas
vezes. O que isso exige do consumidor? Como vocês o tornariam idempotente?**

O consumidor tem de ser **idempotente**: processar a mesma mensagem duas vezes tem de dar
o mesmo resultado que processar uma vez (não pode gerar duas guias para a mesma
requisição). Eu usaria o `requisicaoId` como chave: antes de gerar a guia, verificar numa
tabela (ou cache) se `G-<requisicaoId>` já existe; se existir, só apago a mensagem e sigo.
O registro e a verificação deveriam ser atômicos, por exemplo um `INSERT` com chave única
no banco, ou uma escrita condicional (`attribute_not_exists`) no DynamoDB. Assim, se a
mensagem chegar de novo porque o `delete` falhou ou o timeout venceu no meio, a segunda
tentativa não duplica nada.

**4. Expliquem o visibility timeout com o que viram na mensagem inválida. Para que serve uma
DLQ?**

Quando um consumidor recebe a mensagem, ela não sai da fila: fica invisível para os outros
pelo visibility timeout (15 s na nossa fila). Se ele apaga dentro desse tempo, acabou; se
não apaga, ela volta a ficar visível. A inválida sempre dá `ValueError`, nunca é apagada, e
por isso reapareceu a cada ~15 s com `ApproximateReceiveCount` 1, 2, 3, 4…, às vezes em
outro consumidor. Sem limite, ela ficaria nesse ciclo para sempre, gastando processamento
(uma *poison message*). A **DLQ** é a fila para onde vão as mensagens que falharam
`maxReceiveCount` vezes: tira a mensagem problemática do fluxo principal e guarda para
alguém investigar, corrigir e, se for o caso, reenviar. No teste opcional, com
`maxReceiveCount = 3`, a inválida saiu da `guias-com-dlq` e foi parar na `guias-dlq`.

**5. No Rota Vital, qual a diferença entre o hospital chamar a emissão de guia diretamente
(síncrono) e passar por uma fila (assíncrono)? O que se ganha e o que se perde?**

No síncrono, o hospital chama o serviço de guias e espera a resposta: se o serviço estiver
lento ou fora do ar, o hospital trava ou recebe erro e tem de tentar de novo. Com a fila, o
hospital só publica o pedido e segue; o serviço de guias processa no seu ritmo.

- **Ganha-se:** desacoplamento (o hospital não depende do serviço estar no ar naquele
  instante), absorção de picos (a fila acumula e os consumidores esvaziam aos poucos),
  escala horizontal (é só subir mais consumidores, como fizemos com dois) e reentrega
  automática em caso de falha.
- **Perde-se:** a resposta imediata (o hospital não recebe a guia na hora; precisa de outro
  canal para saber o resultado, como um evento de "guia emitida" ou uma consulta), mais
  complexidade (fila, DLQ, monitoramento) e garantias mais fracas: possível duplicidade e
  falta de ordem, que obrigam o consumidor a ser idempotente. Também fica mais difícil
  rastrear um pedido de ponta a ponta.

## Vídeo (até 3 min)

⟨Link do vídeo.⟩

Roteiro sugerido:

1. (0:00) Terminal com o ElasticMQ rodando e `01-criar-fila.sh` mostrando `VisibilityTimeout = 15`.
2. (0:30) Um consumidor + produtor: 20 guias e a inválida voltando a cada 15 s.
3. (1:30) Dois consumidores lado a lado + produtor: PIDs diferentes dividindo as mensagens.
4. (2:30) (opcional) DLQ: `02-estado-fila.sh` e `05-ler-dlq.sh`.

## Uso de IA

Declaração conforme a PO-CESAR-021.

- **Ferramenta:** Claude (Anthropic).
- **Finalidade:** montar a estrutura do repositório, adaptar o produtor e o consumidor do
  enunciado (variáveis de ambiente, hora e PID na saída), escrever os scripts da fila e da
  DLQ, testar o fluxo contra um emulador da API do SQS e escrever o rascunho do README e das
  respostas.
- **Como validei:** ⟨descrever: subi o ElasticMQ na minha máquina, rodei os scripts, um e
  dois consumidores e a DLQ; conferi nos prints de `evidencias/` o intervalo de 15 s e o
  `ApproximateReceiveCount`; li a documentação de visibility timeout, filas padrão e DLQ do
  SQS; reescrevi as respostas com as minhas palavras⟩.

## Referências

- ElasticMQ: <https://github.com/softwaremill/elasticmq>
- Visibility timeout: <https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html>
- Filas padrão: <https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html>
- Filas de mensagens mortas: <https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html>
- Lambda com SQS: <https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html>
