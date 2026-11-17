#!/usr/bin/env bash
# Opcional: mostra o que caiu na DLQ (sem apagar).
set -e
source "$(dirname "$0")/_comum.sh"

URL=$(aws sqs get-queue-url --queue-name guias-dlq --endpoint-url "$ENDPOINT" \
      --query QueueUrl --output text | tr -d "\r")
aws sqs receive-message --queue-url "$URL" --endpoint-url "$ENDPOINT" \
    --max-number-of-messages 10 --visibility-timeout 0 \
    --message-system-attribute-names ApproximateReceiveCount
