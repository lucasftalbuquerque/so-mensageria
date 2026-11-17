#!/usr/bin/env bash
# Mostra quantas mensagens estão visíveis e quantas estão "em voo" (recebidas e
# ainda não apagadas). Uso: scripts/02-estado-fila.sh [nome-da-fila]
set -e
source "$(dirname "$0")/_comum.sh"
FILA=${1:-guias}

URL=$(aws sqs get-queue-url --queue-name "$FILA" --endpoint-url "$ENDPOINT" \
      --query QueueUrl --output text | tr -d "\r")
aws sqs get-queue-attributes --queue-url "$URL" --endpoint-url "$ENDPOINT" \
    --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible \
    --output table
