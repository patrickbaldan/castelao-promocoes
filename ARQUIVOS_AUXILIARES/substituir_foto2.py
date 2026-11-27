from pathlib import Path

p = Path("app.py")
s = p.read_text(encoding="utf-8")

inicio = s.index("def buscar_foto_produto(produto_id):")
fim = s.index('HTML_BUSCA = """', inicio)

nova_funcao = '''def buscar_foto_produto(produto_id):
    try:
        resposta = requests.get(
            f"{BASE_API}/produtos/{produto_id}/fotos",
            headers=db_headers(),
            timeout=30
        )
        resposta.raise_for_status()

        dados = resposta.json()
        fotos = dados.get("data", [])

        if not fotos:
            return None

        foto_url = fotos[0].get("url")

        if not foto_url:
            return None

        pasta = os.path.join("static", "fotos")
        os.makedirs(pasta, exist_ok=True)

        arquivo = os.path.join(
            pasta,
            f"{produto_id}.png"
        )

        if os.path.exists(arquivo):
            return f"/static/fotos/{produto_id}.png"

        tabs = requests.get(
            "http://127.0.0.1:9222/json",
            timeout=10
        ).json()

        if not tabs:
            return None

        ws_url = tabs[0].get("webSocketDebuggerUrl")

        if not ws_url:
            return None

        ws = websocket.create_connection(
            ws_url,
            timeout=30
        )

        contador = 1

        ws.send(json.dumps({
            "id": contador,
            "method": "Page.enable"
        }))
        contador += 1

        ws.send(json.dumps({
            "id": contador,
            "method": "Page.navigate",
            "params": {
                "url": foto_url
            }
        }))
        contador += 1

        time.sleep(5)

        ws.send(json.dumps({
            "id": contador,
            "method": "Page.captureScreenshot",
            "params": {
                "format": "png"
            }
        }))

        while True:
            resposta_ws = json.loads(ws.recv())

            if resposta_ws.get("id") == contador:
                imagem = resposta_ws["result"]["data"]
                break

        ws.close()

        with open(arquivo, "wb") as f:
            f.write(base64.b64decode(imagem))

        return f"/static/fotos/{produto_id}.png"

    except Exception as e:
        print("ERRO AO BUSCAR FOTO:", e)
        return None


'''

s = s[:inicio] + nova_funcao + s[fim:]

p.write_text(s, encoding="utf-8")

print("FUNÇÃO DE FOTO SUBSTITUÍDA COM SUCESSO")