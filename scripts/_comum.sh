# Variáveis usadas por todos os scripts. Rode com: source scripts/_comum.sh
# O ElasticMQ aceita qualquer credencial, mas a AWS CLI exige que existam.
export AWS_ACCESS_KEY_ID=x AWS_SECRET_ACCESS_KEY=x AWS_DEFAULT_REGION=us-east-1
export ENDPOINT=http://localhost:9324
# No Git Bash do Windows, evita que a CLI converta caminhos e "/" em argumentos.
export MSYS_NO_PATHCONV=1
