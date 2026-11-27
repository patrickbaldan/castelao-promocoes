import requests
import json
import time
import base64
import websocket
from pathlib import Path

produto_id = 2043

abas = requests.get(
    "http://127.0.0.1:9222/json",
    timeout=10
).json()

aba = next(
    (
        x for x in abas
        if x.get("type") == "page"
        and x.get("webSocketDebuggerUrl")
    ),
    None
)

if not aba:
    raise Exception("Chrome com depuração não encontrado.")

print("ABA ENCONTRADA")
print("URL ATUAL:", aba.get("url"))

ws = websocket.create_connection(
    aba["webSocketDebuggerUrl"],
    timeout=30,
    origin="http://127.0.0.1:9222"
)

contador = 0

def comando(method, params=None):

    global contador

    contador += 1

    mensagem = {
        "id": contador,
        "method": method
    }

    if params:
        mensagem["params"] = params

    ws.send(json.dumps(mensagem))

    while True:

        resposta = json.loads(ws.recv())

        if resposta.get("id") == contador:
            return resposta


resposta = comando(
    "Page.navigate",
    {
        "url": "https://erp.dbsoftware.com.br/produto-foto/emp08078723000115/2043/ec5d185794e742b0/full"
    }
)

print("NAVEGAÇÃO ENVIADA")

time.sleep(3)

resultado = comando(
    "Runtime.evaluate",
    {
        "expression": """
(async () => {

const r = await fetch(location.href);

const blob = await r.blob();

const buffer = await blob.arrayBuffer();

const bytes = new Uint8Array(buffer);

let binary = '';

for(let i = 0; i < bytes.length; i += 8192){

    binary += String.fromCharCode(
        ...bytes.subarray(i, i + 8192)
    );

}

return {
    tipo: blob.type,
    tamanho: bytes.length,
    base64: btoa(binary)
};

})()
""",
        "awaitPromise": True,
        "returnByValue": True
    }
)

print("RESULTADO CDP COMPLETO:")
print(resultado)

valor = (
    resultado
    ["result"]
    ["result"]
    .get("value", {})
)

print("VALOR:")
print(valor)

ws.close()