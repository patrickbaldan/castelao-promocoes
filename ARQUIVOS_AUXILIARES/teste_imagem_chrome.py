
import base64
import json
import requests
import websocket

abas = requests.get(
    "http://127.0.0.1:9222/json",
    timeout=10
).json()

aba = next(
    x for x in abas
    if x.get("type") == "page"
    and "/produto-foto/" in x.get("url", "")
)

ws = websocket.create_connection(
    aba["webSocketDebuggerUrl"],
    timeout=30,
    origin="http://127.0.0.1:9222"
)

try:
    ws.send(json.dumps({
        "id": 1,
        "method": "Page.captureScreenshot",
        "params": {"format": "png"}
    }))

    while True:
        resposta = json.loads(ws.recv())

        if resposta.get("id") != 1:
            continue

        if "result" not in resposta:
            raise RuntimeError(resposta)

        imagem = base64.b64decode(
            resposta["result"]["data"]
        )

        with open("teste_foto_2043.png", "wb") as arquivo:
            arquivo.write(imagem)

        print("Arquivo de teste salvo.")
        print("Tamanho:", len(imagem), "bytes")
        break

finally:
    ws.close()
