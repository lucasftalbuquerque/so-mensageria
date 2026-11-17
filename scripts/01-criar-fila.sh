#!/usr/bin/env bash
# Passo 2b: cria a fila "guias" com visibility timeout de 15 s e mostra os atributos.
set -e
source "$(dirname "$0")/_comum.sh"

aws sqs create-queue --queue-name guias --attributes VisibilityTimeout=15 \
    --endpoint-url "$ENDPOINT"

URL=$(aws sqs get-queue-url --queue-name guias --endpoint-url "$ENDPOINT" \
      --query QueueUrl --output text | tr -d "\r")
aws sqs get-queue-attributes --queue-url "$URL" --attribute-names All \
    --endpoint-url "$ENDPOINT"
