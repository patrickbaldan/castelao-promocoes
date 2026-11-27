from pathlib import Path
import shutil
from datetime import datetime

p = Path("app.py")
s = p.read_text(encoding="utf-8-sig")
inicio = s.index("def buscar_foto_produto(produto_id):")
fim = s.index('HTML_BUSCA = """', inicio)

backup = Path(f"app_backup_fotos_{datetime.now():%Y%m%d_%H%M%S}.py")
shutil.copy2(p, backup)

funcao = r'''def buscar_foto_produto(produto_id):
    resposta = requests.get(
        f"{BASE_API}/produtos/{produto_id}/fotos",
        headers=db_headers(),
        timeout=30
    )
    resposta.raise_for_status()
    dados = resposta.json()

    conteudo = dados.get("data", {})
    geral = conteudo.get("geral", []) if isinstance(conteudo, dict) else []
    if not geral:
        print(f"Nenhuma foto encontrada para o produto ID {produto_id}")
        return None

    capa = next(
        (foto for foto in geral if foto.get("is_capa") is True),
        geral[0]
    )
    urls = capa.get("urls") or {}
    foto_original = (
        urls.get("medium") or urls.get("full")
        or urls.get("thumb") or capa.get("url")
    )
    if not foto_original:
        return None

    pasta = Path("static") / "fotos"
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = pasta / f"dbsoftware_{produto_id}.png"

    if arquivo.exists() and arquivo.stat().st_size > 1000:
        return f"/static/fotos/{arquivo.name}"

    alvo_id = None
    try:
        base = "http://127.0.0.1:9222"
        url_nova = base + "/json/new?" + urllib.parse.quote(
            foto_original, safe=":/?=&"
        )
        r = requests.put(url_nova, timeout=10)
        r.raise_for_status()
        aba = r.json()
        alvo_id = aba.get("id")

        ws = websocket.create_connection(
            aba["webSocketDebuggerUrl"],
            timeout=15,
            suppress_origin=True
        )
        try:
            time.sleep(2)
            ws.send(json.dumps({
                "id": 1,
                "method": "Page.captureScreenshot",
                "params": {"format": "png", "captureBeyondViewport": True}
            }))
            while True:
                msg = json.loads(ws.recv())
                if msg.get("id") == 1:
                    if "error" in msg:
                        raise RuntimeError(str(msg["error"]))
                    imagem = base64.b64decode(msg["result"]["data"])
                    break
            if len(imagem) < 1000:
                raise RuntimeError("Imagem capturada vazia.")
            arquivo.write_bytes(imagem)
        finally:
            ws.close()

        print(f"Foto salva: {arquivo}")
        return f"/static/fotos/{arquivo.name}"

    except Exception as e:
        print(f"Falha ao salvar foto local do produto {produto_id}: {e}")
        return foto_original
    finally:
        if alvo_id:
            try:
                requests.get(f"http://127.0.0.1:9222/json/close/{alvo_id}", timeout=3)
            except Exception:
                pass


'''

p.write_text(s[:inicio] + funcao + s[fim:], encoding="utf-8")
print("Backup criado:", backup)
print("Função de fotos atualizada.")
