"""Produtor da fila de guias (Atividade individual 2 · Mensageria).

Publica 20 pedidos válidos (R-001 a R-020) e 1 inválido (sem requisicaoId).
Usa as mesmas variáveis de ambiente do consumidor (FILA e SQS_ENDPOINT).
"""
import json, os, boto3

FILA = os.environ.get("FILA", "guias")
ENDPOINT = os.environ.get("SQS_ENDPOINT", "http://localhost:9324")

if ENDPOINT:
    sqs = boto3.client(
        "sqs", endpoint_url=ENDPOINT, region_name="us-east-1",
        aws_access_key_id="x", aws_secret_access_key="x")
else:
    sqs = boto3.client("sqs")
url = sqs.get_queue_url(QueueName=FILA)["QueueUrl"]

for i in range(1, 21):
    pedido = {"requisicaoId": f"R-{i:03d}", "hospital": "H-Recife"}
    sqs.send_message(QueueUrl=url, MessageBody=json.dumps(pedido))
sqs.send_message(QueueUrl=url, MessageBody=json.dumps({"hospital": "H-Recife"}))
print("21 mensagens enviadas para", url)
