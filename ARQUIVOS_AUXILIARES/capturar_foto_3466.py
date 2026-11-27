import json
import base64
from pathlib import Path
import requests
import websocket

abas = requests.get("http://127.0.0.1:9222/json/list", timeout=10).json()
aba = next(
    (a for a in abas if a.get("type") == "page"
     and "/3466/" in a.get("url", "")
     and a.get("url", "").endswith("/medium")),
    None
)

if not aba:
    raise SystemExit("ERRO: não encontrei a aba da foto do produto 3466.")

ws = websocket.create_connection(
    aba["webSocketDebuggerUrl"], timeout=20, suppress_origin=True
)

try:
    def comando(numero, metodo, parametros=None):
        ws.send(json.dumps({
            "id": numero, "method": metodo, "params": parametros or {}
        }))
        while True:
            resposta = json.loads(ws.recv())
            if resposta.get("id") == numero:
                if "error" in resposta:
                    raise RuntimeError(resposta["error"])
                return resposta.get("result", {})

    comando(1, "Page.enable")
    info = comando(2, "Runtime.evaluate", {
        "expression": "({url:location.href, imagens:[...document.images].map(i=>({w:i.naturalWidth,h:i.naturalHeight}))})",
        "returnByValue": True
    })
    print("Verificação:", info.get("result", {}).get("value"))

    captura = comando(3, "Page.captureScreenshot", {
        "format": "png", "captureBeyondViewport": True
    })
    dados = captura.get("data")
    if not dados:
        raise RuntimeError("O Chrome não retornou a captura.")

    pasta = Path("static") / "fotos"
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = pasta / "dbsoftware_3466.png"
    arquivo.write_bytes(base64.b64decode(dados))

    if arquivo.stat().st_size < 1000:
        arquivo.unlink(missing_ok=True)
        raise RuntimeError("A captura ficou pequena demais; não foi aceita.")

    print(f"ARQUIVO SALVO: {arquivo.resolve()}")
    print(f"TAMANHO: {arquivo.stat().st_size} bytes")
finally:
    ws.close()
