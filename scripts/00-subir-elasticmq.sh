#!/usr/bin/env bash
# Passo 2a: sobe o ElasticMQ. Deixe este terminal aberto.
# 9324 = API compatível com SQS · 9325 = painel web (http://localhost:9325), bom para o vídeo.
docker run --rm -p 9324:9324 -p 9325:9325 softwaremill/elasticmq-native
