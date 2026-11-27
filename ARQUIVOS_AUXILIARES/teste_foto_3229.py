import requests
import json
import time
import base64
import websocket
import os

URL_FOTO = "https://erp.dbsoftware.com.br/produto-foto/emp08078723000115/3229/46cb0b41daf91f49/full"
ARQUIVO = r"static\fotos\teste_3229.png"

abas = requests.get("http://127.0.0.1:9222/json", timeout=10).json()

aba = next(
    x for x in abas
    if x.get("type") == "page"
    and x.get("url", "").startswith("https://erp.dbsoftware.com.br")
)

print("ABA ENCONTRADA")
print("URL:", aba["url"])

ws = websocket.create_connection(
    aba["webSocketDebuggerUrl"],
    timeout=60,
    origin="http://127.0.0.1:9222"
)

ws.send(json.dumps({
    "id": 1,
    "method": "Page.enable",
    "params": {}
}))

time.sleep(1)

ws.send(json.dumps({
    "id": 2,
    "method": "Page.navigate",
    "params": {
        "url": URL_FOTO
    }
}))

print("ABRINDO FOTO...")
time.sleep(5)

ws.send(json.dumps({
    "id": 3,
    "method": "Page.captureScreenshot",
    "params": {
        "format": "png"
    }
}))

print("CAPTURANDO...")

while True:
    retorno = json.loads(ws.recv())
    if retorno.get("id") == 3:
        break

if "result" not in retorno:
    print("ERRO:")
    print(retorno)
    ws.close()
    raise SystemExit

imagem = base64.b64decode(retorno["result"]["data"])

os.makedirs(os.path.dirname(ARQUIVO), exist_ok=True)

with open(ARQUIVO, "wb") as f:
    f.write(imagem)

ws.close()

print("================================")
print("FOTO SALVA COM SUCESSO")
print("ARQUIVO:", ARQUIVO)
print("BYTES:", len(imagem))
print("================================")
