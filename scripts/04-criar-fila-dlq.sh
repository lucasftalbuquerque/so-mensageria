#!/usr/bin/env bash
# Opcional: cria a DLQ "guias-dlq" e a fila "guias-com-dlq", que manda para a DLQ
# toda mensagem recebida 3 vezes sem ser apagada (maxReceiveCount = 3).
# Depois rode o consumidor e o produtor com FILA=guias-com-dlq.
set -e
source "$(dirname "$0")/_comum.sh"

aws sqs create-queue --queue-name guias-dlq --endpoint-url "$ENDPOINT" > /dev/null
DLQ_URL=$(aws sqs get-queue-url --queue-name guias-dlq --endpoint-url "$ENDPOINT" \
          --query QueueUrl --output text | tr -d "\r")
DLQ_ARN=$(aws sqs get-queue-attributes --queue-url "$DLQ_URL" --attribute-names QueueArn \
          --endpoint-url "$ENDPOINT" --query Attributes.QueueArn --output text | tr -d "\r")
echo "DLQ: $DLQ_ARN"

aws sqs create-queue --queue-name guias-com-dlq --endpoint-url "$ENDPOINT" --attributes \
  "{\"VisibilityTimeout\":\"15\",\"RedrivePolicy\":\"{\\\"deadLetterTargetArn\\\":\\\"$DLQ_ARN\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"}"

URL=$(aws sqs get-queue-url --queue-name guias-com-dlq --endpoint-url "$ENDPOINT" \
      --query QueueUrl --output text | tr -d "\r")
aws sqs get-queue-attributes --queue-url "$URL" --endpoint-url "$ENDPOINT" \
    --attribute-names VisibilityTimeout RedrivePolicy
