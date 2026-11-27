import requests
import websocket
import json
import time
import base64

abas = requests.get(
    "http://127.0.0.1:9222/json",
    timeout=10
).json()

aba = next(
    x for x in abas
    if x.get("type") == "page"
    and x.get("url", "").startswith(
        "https://erp.dbsoftware.com.br"
    )
)

print("ABA ENCONTRADA")
print("URL:", aba["url"])

ws = websocket.create_connection(
    aba["webSocketDebuggerUrl"],
    timeout=60,
    origin="http://127.0.0.1:9222"
)

contador = 0


def enviar(method, params=None):

    global contador

    contador += 1

    ws.send(
        json.dumps({
            "id": contador,
            "method": method,
            "params": params or {}
        })
    )

    return contador


enviar("Page.enable")

time.sleep(1)

url = (
    "https://erp.dbsoftware.com.br/"
    "produto-foto/emp08078723000115/"
    "2043/ec5d185794e742b0/"
    "full"
)

enviar(
    "Page.navigate",
    {
        "url": url
    }
)

print("NAVEGAÇÃO ENVIADA")

time.sleep(5)

comando = enviar(
    "Page.captureScreenshot",
    {
        "format": "png"
    }
)

print("CAPTURANDO IMAGEM...")

while True:

    retorno = json.loads(
        ws.recv()
    )

    if retorno.get("id") != comando:
        continue

    if "result" not in retorno:
        print("ERRO:", retorno)
        break

    imagem_base64 = retorno["result"]["data"]

    imagem = base64.b64decode(
        imagem_base64
    )

    with open(
        "static/fotos/2043.png",
        "wb"
    ) as arquivo:

        arquivo.write(imagem)

    print()
    print("FOTO SALVA:")
    print("static/fotos/2043.png")
    print("BYTES:", len(imagem))

    break

ws.close()

print()
print("TESTE FINALIZADO")