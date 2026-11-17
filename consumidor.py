"""Consumidor da fila de guias (Atividade individual 2 · Mensageria).

Retira até 10 mensagens por vez, gera a guia e só então apaga a mensagem.
Se o processamento falhar, a mensagem NÃO é apagada: ela fica invisível até o
visibility timeout (15 s) acabar e volta para a fila.

Variáveis de ambiente (opcionais):
  FILA          nome da fila (padrão: guias)
  SQS_ENDPOINT  endereço da fila (padrão: http://localhost:9324, o ElasticMQ).
                Deixe vazio (SQS_ENDPOINT=) para usar o Amazon SQS de verdade.
"""
import json, os, time, boto3

FILA = os.environ.get("FILA", "guias")
ENDPOINT = os.environ.get("SQS_ENDPOINT", "http://localhost:9324")

if ENDPOINT:  # Caminho A: ElasticMQ local, aceita credenciais falsas
    sqs = boto3.client(
        "sqs", endpoint_url=ENDPOINT, region_name="us-east-1",
        aws_access_key_id="x", aws_secret_access_key="x")
else:         # Caminho B: Amazon SQS, credenciais do `aws configure`
    sqs = boto3.client("sqs")
url = sqs.get_queue_url(QueueName=FILA)["QueueUrl"]


def agora():
    return time.strftime("%H:%M:%S")


def processar(pedido):
    if "requisicaoId" not in pedido:
        raise ValueError("mensagem sem requisicaoId")
    print(agora(), os.getpid(), "guia G-" + pedido["requisicaoId"], pedido.get("hospital"),
          flush=True)


print(agora(), os.getpid(), "consumidor ouvindo", url, flush=True)
while True:
    resp = sqs.receive_message(
        QueueUrl=url, MaxNumberOfMessages=10, WaitTimeSeconds=10,
        MessageSystemAttributeNames=["ApproximateReceiveCount"])
    for m in resp.get("Messages", []):
        try:
            processar(json.loads(m["Body"]))
            # só confirma (apaga) depois que a guia foi gerada
            sqs.delete_message(QueueUrl=url, ReceiptHandle=m["ReceiptHandle"])
        except Exception as e:
            print(agora(), os.getpid(), "falhou; volta para a fila:", e, m.get("Attributes"),
                  flush=True)
