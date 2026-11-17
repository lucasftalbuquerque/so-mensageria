#!/usr/bin/env bash
# Apaga todas as mensagens da fila (útil entre o teste com 1 e com 2 consumidores,
# para a mensagem inválida da rodada anterior não se misturar).
# Uso: scripts/03-limpar-fila.sh [nome-da-fila]
set -e
source "$(dirname "$0")/_comum.sh"
FILA=${1:-guias}

URL=$(aws sqs get-queue-url --queue-name "$FILA" --endpoint-url "$ENDPOINT" \
      --query QueueUrl --output text | tr -d "\r")
aws sqs purge-queue --queue-url "$URL" --endpoint-url "$ENDPOINT"
echo "fila $FILA limpa"
