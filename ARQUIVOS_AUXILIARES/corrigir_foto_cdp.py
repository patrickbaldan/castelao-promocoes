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
            print("PRODUTO SEM FOTO:", produto_id)
            return None

        foto_url = fotos[0].get("url")

        if not foto_url:
            print("URL DA FOTO NÃO ENCONTRADA:", produto_id)
            return None

        pasta = os.path.join(
            "static",
            "fotos"
        )

        os.makedirs(
            pasta,
            exist_ok=True
        )

        arquivo = os.path.join(
            pasta,
            f"{produto_id}.png"
        )

        if os.path.exists(arquivo):

            print(
                "FOTO JÁ EXISTE:",
                arquivo
            )

            return f"/static/fotos/{produto_id}.png"

        abas = requests.get(
            "http://127.0.0.1:9222/json",
            timeout=10
        ).json()

        aba = next(
            x for x in abas
            if x.get("type") == "page"
            and x.get(
                "url",
                ""
            ).startswith(
                "https://erp.dbsoftware.com.br"
            )
        )

        print(
            "ABA ENCONTRADA PARA FOTO:",
            aba["url"]
        )

        ws = websocket.create_connection(
            aba["webSocketDebuggerUrl"],
            timeout=60,
            origin="http://127.0.0.1:9222"
        )

        contador = 0

        def enviar(method, params=None):

            nonlocal contador

            contador += 1

            ws.send(
                json.dumps({
                    "id": contador,
                    "method": method,
                    "params": params or {}
                })
            )

            return contador

        enviar(
            "Page.enable"
        )

        time.sleep(1)

        enviar(
            "Page.navigate",
            {
                "url": foto_url
            }
        )

        print(
            "NAVEGAÇÃO PARA FOTO ENVIADA"
        )

        time.sleep(5)

        comando = enviar(
            "Page.captureScreenshot",
            {
                "format": "png"
            }
        )

        print(
            "CAPTURANDO FOTO..."
        )

        while True:

            retorno = json.loads(
                ws.recv()
            )

            if retorno.get("id") != comando:
                continue

            if "result" not in retorno:

                print(
                    "ERRO CDP:",
                    retorno
                )

                ws.close()

                return None

            imagem_base64 = retorno[
                "result"
            ]["data"]

            imagem = base64.b64decode(
                imagem_base64
            )

            with open(
                arquivo,
                "wb"
            ) as f:

                f.write(imagem)

            ws.close()

            print(
                "FOTO SALVA:",
                arquivo
            )

            print(
                "BYTES:",
                len(imagem)
            )

            return f"/static/fotos/{produto_id}.png"

    except Exception as e:

        print(
            "ERRO AO BUSCAR FOTO:",
            repr(e)
        )

        return None


'''

s = s[:inicio] + nova_funcao + s[fim:]

p.write_text(
    s,
    encoding="utf-8"
)

print(
    "CORREÇÃO CDP DA FOTO CONCLUÍDA"
)
