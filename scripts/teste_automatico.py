"""Roda os três cenários da atividade de ponta a ponta e salva as saídas em
evidencias/teste-automatico/. Uso: python scripts/teste_automatico.py
(ou duplo clique em scripts/testar-tudo.bat no Windows).

1. sobe o ElasticMQ no Docker (container "so-elasticmq", fica rodando no final);
2. cria a fila "guias" com VisibilityTimeout=15 pela AWS CLI;
3. um consumidor + produtor (50 s);
4. dois consumidores + produtor (35 s);
5. opcional: fila com DLQ, maxReceiveCount=3 (55 s).
"""
import json, os, shutil, subprocess, sys, time, urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "evidencias" / "teste-automatico"
SAIDA.mkdir(parents=True, exist_ok=True)
ENDPOINT = "http://localhost:9324"
ENV = dict(os.environ, AWS_ACCESS_KEY_ID="x", AWS_SECRET_ACCESS_KEY="x",
           AWS_DEFAULT_REGION="us-east-1", PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
resumo = open(SAIDA / "00-resumo.txt", "w", encoding="utf-8")


def log(*a):
    linha = time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a)
    print(linha, flush=True)
    resumo.write(linha + "\n"); resumo.flush()


def rodar(cmd, arquivo=None, checar=True):
    log("$", " ".join(cmd))
    r = subprocess.run(cmd, cwd=RAIZ, env=ENV, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    texto = (r.stdout or "") + (r.stderr or "")
    log(texto.strip())
    if arquivo:
        (SAIDA / arquivo).write_text("$ " + " ".join(cmd) + "\n" + texto, encoding="utf-8")
    if checar and r.returncode != 0:
        raise SystemExit(f"falhou (código {r.returncode}): {' '.join(cmd)}")
    return texto.strip()


def aws(*args, arquivo=None):
    return rodar(["aws", "sqs", *args, "--endpoint-url", ENDPOINT], arquivo)


def consumidor(nome, fila="guias"):
    f = open(SAIDA / nome, "w", encoding="utf-8")
    p = subprocess.Popen([sys.executable, "consumidor.py"], cwd=RAIZ,
                         env=dict(ENV, FILA=fila), stdout=f, stderr=subprocess.STDOUT)
    return p, f


def produtor(fila="guias"):
    r = subprocess.run([sys.executable, "produtor.py"], cwd=RAIZ, env=dict(ENV, FILA=fila),
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    log("produtor:", (r.stdout + r.stderr).strip())


def parar(*procs):
    for p, f in procs:
        p.terminate(); p.wait(); f.close()


def url(fila):
    return aws("get-queue-url", "--queue-name", fila, "--query", "QueueUrl",
               "--output", "text").strip()


# 0. ferramentas
for f in ("docker", "aws"):
    if not shutil.which(f):
        log(f"ERRO: '{f}' não encontrado no PATH. Instale e abra um terminal novo.")
        raise SystemExit(1)
try:
    import boto3  # noqa: F401
except ImportError:
    rodar([sys.executable, "-m", "pip", "install", "boto3"])
rodar(["docker", "version", "--format", "Docker {{.Server.Version}}"])
rodar(["aws", "--version"])
log("Python", sys.version.split()[0])

# 1. ElasticMQ
rodar(["docker", "rm", "-f", "so-elasticmq"], checar=False)
rodar(["docker", "run", "-d", "--rm", "--name", "so-elasticmq", "-p", "9324:9324",
       "-p", "9325:9325", "softwaremill/elasticmq-native"])
for _ in range(60):
    try:
        urllib.request.urlopen(ENDPOINT, timeout=1)
        break
    except urllib.error.HTTPError:
        break  # respondeu (mesmo com erro HTTP): está no ar
    except Exception:
        time.sleep(1)
log("ElasticMQ no ar")

# 2. fila
aws("create-queue", "--queue-name", "guias", "--attributes", "VisibilityTimeout=15",
    arquivo="01-criar-fila.txt")
aws("get-queue-attributes", "--queue-url", url("guias"), "--attribute-names", "All",
    arquivo="01-atributos-fila.txt")

# 3. um consumidor
log("== um consumidor (50 s)")
c = consumidor("02-um-consumidor.txt")
time.sleep(3); produtor(); time.sleep(50); parar(c)
log((SAIDA / "02-um-consumidor.txt").read_text(encoding="utf-8"))

# 4. dois consumidores
aws("purge-queue", "--queue-url", url("guias"))
time.sleep(2)
log("== dois consumidores (35 s)")
a = consumidor("03-consumidor-A.txt"); b = consumidor("03-consumidor-B.txt")
time.sleep(3); produtor(); time.sleep(35); parar(a, b)
for n in ("03-consumidor-A.txt", "03-consumidor-B.txt"):
    log(n, "\n" + (SAIDA / n).read_text(encoding="utf-8"))

# 5. DLQ
log("== DLQ (55 s)")
aws("create-queue", "--queue-name", "guias-dlq")
arn = aws("get-queue-attributes", "--queue-url", url("guias-dlq"), "--attribute-names",
          "QueueArn", "--query", "Attributes.QueueArn", "--output", "text").strip()
redrive = json.dumps({"deadLetterTargetArn": arn, "maxReceiveCount": "3"})
aws("create-queue", "--queue-name", "guias-com-dlq", "--attributes",
    json.dumps({"VisibilityTimeout": "15", "RedrivePolicy": redrive}),
    arquivo="04-criar-fila-dlq.txt")
d = consumidor("04-consumidor-dlq.txt", "guias-com-dlq")
time.sleep(3); produtor("guias-com-dlq"); time.sleep(55); parar(d)
log((SAIDA / "04-consumidor-dlq.txt").read_text(encoding="utf-8"))
aws("get-queue-attributes", "--queue-url", url("guias-com-dlq"), "--attribute-names",
    "ApproximateNumberOfMessages", "ApproximateNumberOfMessagesNotVisible",
    arquivo="04-estado-fila-principal.txt")
aws("receive-message", "--queue-url", url("guias-dlq"), "--max-number-of-messages", "10",
    "--visibility-timeout", "0", "--message-system-attribute-names", "ApproximateReceiveCount",
    arquivo="04-mensagem-na-dlq.txt")

log("FIM. ElasticMQ continua rodando (painel em http://localhost:9325).",
    "Para parar: docker stop so-elasticmq")
