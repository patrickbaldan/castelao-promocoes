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
    timeout=120,
    origin="http://127.0.0.1:9222"
)

contador = 0


def enviar(method, params=None):

    global contador

    contador += 1

    mensagem = {
        "id": contador,
        "method": method
    }

    if params:
        mensagem["params"] = params

    ws.send(
        json.dumps(mensagem)
    )


enviar("Network.enable")

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

inicio = time.time()

while time.time() - inicio < 30:

    mensagem = json.loads(
        ws.recv()
    )

    if mensagem.get("method") != "Network.responseReceived":
        continue

    params = mensagem.get(
        "params",
        {}
    )

    resposta = params.get(
        "response",
        {}
    )

    url_resposta = resposta.get(
        "url",
        ""
    )

    if "produto-foto" not in url_resposta:
        continue

    print()
    print("RESPOSTA ENCONTRADA")
    print(
        "STATUS:",
        resposta.get("status")
    )
    print(
        "TIPO:",
        resposta.get("mimeType")
    )
    print(
        "URL:",
        url_resposta
    )

    request_id = params.get(
        "requestId"
    )

    contador += 1

    comando_body = contador

    ws.send(
        json.dumps({
            "id": comando_body,
            "method": "Network.getResponseBody",
            "params": {
                "requestId": request_id
            }
        })
    )

    inicio_body = time.time()

    while time.time() - inicio_body < 30:

        retorno = json.loads(
            ws.recv()
        )

        if retorno.get("id") != comando_body:
            continue

        if "result" not in retorno:
            continue

        if "body" not in retorno["result"]:
            continue

        body = retorno["result"]["body"]

        imagem = base64.b64decode(
            body
        )

        with open(
            "static/fotos/2043.webp",
            "wb"
        ) as arquivo:

            arquivo.write(imagem)

        print()
        print(
            "FOTO SALVA: static/fotos/2043.webp"
        )

        print(
            "BYTES:",
            len(imagem)
        )

        break

    break


ws.close()

print()
print("TESTE FINALIZADO")