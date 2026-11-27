from pathlib import Path

p = Path("app.py")
s = p.read_text(encoding="utf-8")

inicio = s.index("def buscar_foto_produto(produto_id):")
fim = s.index("\n\nHTML_BUSCA", inicio)

nova_funcao = '''def buscar_foto_produto(produto_id):

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

    ws = websocket.create_connection(
        aba["webSocketDebuggerUrl"],
        timeout=30,
        origin="http://127.0.0.1:9222"
    )

    contador = 0

    def comando(method, params=None):
        nonlocal contador

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

    resposta = requests.get(
        f"{BASE_API}/produtos/{produto_id}/fotos",
        headers=db_headers(),
        timeout=30
    )

    resposta.raise_for_status()

    dados = resposta.json()

    geral = dados.get("data", {}).get("geral", [])

    if not geral:
        ws.close()
        return None

    capa = next(
        (foto for foto in geral if foto.get("is_capa")),
        geral[0]
    )

    url = capa["urls"]["full"]

    comando(
        "Page.navigate",
        {"url": url}
    )

    time.sleep(2)

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

for(let i=0;i<bytes.length;i+=8192){
    binary += String.fromCharCode(
        ...bytes.subarray(i,i+8192)
    );
}

return {
    tipo: blob.type,
    base64: btoa(binary)
};

})()
""",
            "awaitPromise": True,
            "returnByValue": True
        }
    )

    valor = resultado["result"]["result"]["value"]

    imagem = base64.b64decode(
        valor["base64"]
    )

    ws.close()

    return imagem
'''

s = s[:inicio] + nova_funcao + s[fim:]

p.write_text(s, encoding="utf-8")

print("FUNÇÃO DE FOTO SUBSTITUÍDA COM SUCESSO")