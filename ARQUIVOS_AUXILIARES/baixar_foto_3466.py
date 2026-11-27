import json
import base64
import time
import requests
import websocket
from pathlib import Path

produto_id = 3466
api = "http://erp.dbsoftware.com.br/api/v1/produtos/3466/fotos"
headers = {
    "Authorization": "Bearer " + __import__("os").environ["DBSOFTWARE_TOKEN"],
    "Accept": "application/json"
}

r = requests.get(api, headers=headers, timeout=20)
r.raise_for_status()
fotos = r.json()["data"]["geral"]
capa = next((f for f in fotos if f.get("is_capa")), fotos[0])
url = capa["urls"]["medium"]

aba = requests.put(
    "http://127.0.0.1:9222/json/new?" + __import__("urllib.parse").parse.quote(url, safe=":/?=&"),
    timeout=10
)
aba.raise_for_status()
alvo = aba.json()
ws = None

try:
    ws = websocket.create_connection(
        alvo["webSocketDebuggerUrl"],
        timeout=20,
        suppress_origin=True
    )
    contador = 0

    def comando(metodo, parametros=None):
        global contador
        contador += 1
        n = contador
        ws.send(json.dumps({
            "id": n,
            "method": metodo,
            "params": parametros or {}
        }))
        while True:
            msg = json.loads(ws.recv())
            if msg.get("id") == n:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})

    time.sleep(3)
    js = """
    fetch(location.href, {cache:'no-store'})
      .then(r => { if (!r.ok) throw Error('HTTP ' + r.status); return r.blob(); })
      .then(b => new Promise((resolve, reject) => {
        const f = new FileReader();
        f.onloadend = () => resolve(f.result.split(',')[1]);
        f.onerror = reject;
        f.readAsDataURL(b);
      }))
    """
    resultado = comando("Runtime.evaluate", {
        "expression": js,
        "awaitPromise": True,
        "returnByValue": True
    })
    dados = resultado.get("result", {}).get("value")
    if not dados:
        raise RuntimeError(str(resultado.get("exceptionDetails", resultado)))

    imagem = base64.b64decode(dados)
    if len(imagem) < 1000:
        raise RuntimeError("Imagem recebida muito pequena.")

    pasta = Path("static") / "fotos"
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / "3466.png"
    destino.write_bytes(imagem)
    print(f"FOTO SALVA: {destino.resolve()}")
    print(f"Tamanho: {len(imagem)} bytes")

finally:
    if ws:
        ws.close()
    try:
        requests.get(
            "http://127.0.0.1:9222/json/close/" + alvo["id"],
            timeout=3
        )
    except Exception:
        pass
