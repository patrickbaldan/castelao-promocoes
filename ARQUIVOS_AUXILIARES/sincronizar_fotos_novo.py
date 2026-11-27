import os
import json
import time
import base64
import requests
import websocket

BASE_API = "http://erp.dbsoftware.com.br/api/v1"
PASTA_FOTOS = os.path.join("static", "fotos")

PER_PAGE = 100
LIMITE_PRODUTOS = 60000

os.makedirs(PASTA_FOTOS, exist_ok=True)

TOKEN = os.getenv("DBSOFTWARE_TOKEN")

if not TOKEN:
    print("ERRO: DBSOFTWARE_TOKEN não configurado.")
    raise SystemExit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json",
}


def buscar_aba_chrome():
    abas = requests.get(
        "http://127.0.0.1:9222/json",
        timeout=10
    ).json()

    for aba in abas:
        if (
            aba.get("type") == "page"
            and aba.get("url", "").rstrip("/")
            == "https://erp.dbsoftware.com.br/dashboard"
            and aba.get("webSocketDebuggerUrl")
        ):
            return aba

    for aba in abas:
        if (
            aba.get("type") == "page"
            and aba.get("url", "").startswith(
                "https://erp.dbsoftware.com.br"
            )
            and aba.get("webSocketDebuggerUrl")
        ):
            return aba

    raise RuntimeError(
        "Nenhuma aba adequada do DBSoftware encontrada no Chrome."
    )

def conectar_chrome():
    aba = buscar_aba_chrome()

    ws = websocket.create_connection(
        aba["webSocketDebuggerUrl"],
        timeout=10,
        origin="http://127.0.0.1:9222"
    )

    ws.settimeout(2)

    return ws



def navegar_capturar(ws, foto_url):
    proximo_id = 10
    def enviar(metodo, parametros=None, limite=30):
        nonlocal proximo_id
        proximo_id += 1
        comando_id = proximo_id

        ws.send(json.dumps({
            "id": comando_id,
            "method": metodo,
            "params": parametros or {}
        }))

        inicio = time.time()
        while time.time() - inicio < limite:
            try:
                retorno = json.loads(ws.recv())
            except websocket.WebSocketTimeoutException:
                continue

            if retorno.get("id") != comando_id:
                continue

            if "error" in retorno:
                raise RuntimeError(
                    f"Erro CDP em {metodo}: {retorno['error']}"
                )

            return retorno

        raise RuntimeError(
            f"Tempo limite aguardando {metodo}."
        )

    ws.settimeout(2)

    
   
    print("Abrindo foto no Chrome...", flush=True)

    ws.send(json.dumps({
        "id": 1,
        "method": "Page.navigate",
        "params": {"url": foto_url}
    }))

    time.sleep(3)


    dimensoes = None

    for tentativa in range(20):
        retorno = enviar(
            "Runtime.evaluate",
            {
                "expression": (
                    "(()=>{const i=document.querySelector('img');"
                    "return i&&i.complete&&i.naturalWidth>0?"
                    "{w:i.naturalWidth,h:i.naturalHeight}:null})()"
                ),
                "returnByValue": True
            }
        )

        resultado = retorno.get("result", {}).get("result", {})
        dimensoes = resultado.get("value")

        if dimensoes:
            break

        time.sleep(1)

    if not dimensoes:
        raise RuntimeError(
            "A foto nÃ£o carregou no Chrome apÃ³s 20 tentativas."
        )

    print(
        f"Foto carregada: {dimensoes['w']}x{dimensoes['h']}",
        flush=True
    )

    enviar(
        "Emulation.setDeviceMetricsOverride",
        {
            "width": dimensoes["w"],
            "height": dimensoes["h"],
            "deviceScaleFactor": 1,
            "mobile": False
        }
    )

    retorno = enviar(
        "Page.captureScreenshot",
        {
            "format": "png",
            "fromSurface": True,
            "captureBeyondViewport": True
        },
        limite=60
    )

    dados = retorno.get("result", {}).get("data")

    if not dados:
        raise RuntimeError("Chrome nÃ£o retornou a imagem.")

    imagem = base64.b64decode(dados)

    if not imagem.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("A captura retornada nÃ£o Ã© PNG vÃ¡lido.")

    if len(imagem) < 1000:
        raise RuntimeError(
            f"Imagem capturada muito pequena: {len(imagem)} bytes."
        )

    enviar("Emulation.clearDeviceMetricsOverride")

    print(f"Captura concluÃ­da: {len(imagem)} bytes", flush=True)

    return imagem


def buscar_fotos(produto_id):
    resposta = requests.get(
        f"{BASE_API}/produtos/{produto_id}/fotos",
        headers=HEADERS,
        timeout=30
    )

    resposta.raise_for_status()

    dados = resposta.json()

    return dados.get("data", {}).get("geral", [])


def buscar_produtos(pagina):
    resposta = requests.get(
        f"{BASE_API}/produtos",
        headers=HEADERS,
        params={
            "page": pagina,
            "per_page": PER_PAGE
        },
        timeout=30
    )

    resposta.raise_for_status()

    return resposta.json()


print("========================================")
print("SINCRONIZADOR NOVO DE FOTOS")
print("========================================")
print("Limite de teste:", LIMITE_PRODUTOS)
print()

ws = None

try:
    ws = conectar_chrome()

    print("CHROME CDP: CONECTADO")
    print()

    processados = 0
    baixadas = 0
    existentes = 0
    sem_foto = 0
    erros = 0

    pagina = 1

    while processados < LIMITE_PRODUTOS:

        dados = buscar_produtos(pagina)

        produtos = dados.get("data", [])

        if not produtos:
            print("FIM DOS PRODUTOS.")
            break

        print(
            f"--- PÃƒÆ’Ã‚ÂGINA {pagina} | "
            f"{len(produtos)} produtos ---"
        )

        for produto in produtos:

            if processados >= LIMITE_PRODUTOS:
                break

            produto_id = produto.get("id")

            if not produto_id:
                continue

            processados += 1

            arquivo = os.path.join(
                PASTA_FOTOS,
                f"{produto_id}.png"
            )

            print(
                f"[{processados}/{LIMITE_PRODUTOS}] "
                f"ID {produto_id}",
                end=" "
            )

            try:

                if os.path.exists(arquivo):
                    existentes += 1
                    print("ATUALIZANDO FOTO EXISTENTE")

                
                print("Consultando fotos no DBSoftware...", flush=True)
                fotos = buscar_fotos(produto_id)
                print("Consulta concluÃ­da. Quantidade:", len(fotos), flush=True)




                if not fotos:
                    sem_foto += 1
                    print("SEM FOTO")
                    continue

                foto = next(
                    (
                        f for f in fotos
                        if f.get("is_capa")
                    ),
                    fotos[0]
                )

                foto_url = (
                    foto.get("urls", {})
                    .get("full")
                )

                if not foto_url:
                    sem_foto += 1
                    print("SEM URL")
                    continue

              
                    
                print("URL da foto:", foto_url, flush=True)
                print("Abrindo foto no Chrome...", flush=True)

                imagem = navegar_capturar(
                    ws,
                    foto_url
                )

                print("Captura concluÃ­da:", len(imagem), "bytes", flush=True)



                if not imagem:
                    raise RuntimeError(
                        "Imagem vazia."
                    )

                
                arquivo_temporario = arquivo + ".tmp"

                try:
                    with open(arquivo_temporario, "wb") as f:
                        f.write(imagem)
                        f.flush()
                        os.fsync(f.fileno())

                    with open(arquivo_temporario, "rb") as f:
                        cabecalho = f.read(8)

                    if cabecalho != b"\x89PNG\r\n\x1a\n":
                        raise RuntimeError(
                            "Arquivo temporÃ¡rio nÃ£o Ã© um PNG vÃ¡lido."
                        )

                    if os.path.getsize(arquivo_temporario) < 1000:
                        raise RuntimeError(
                            "Arquivo temporÃ¡rio muito pequeno."
                        )

                    os.replace(arquivo_temporario, arquivo)

                finally:
                    if os.path.exists(arquivo_temporario):
                        os.remove(arquivo_temporario)

                baixadas += 1

                print(
                    f"BAIXADA ({len(imagem)} bytes)"
                )

            
            except Exception as e:
                erros += 1
                print("ERRO:", repr(e), flush=True)
                import traceback
                traceback.print_exc()

        pagina += 1

finally:

    if ws:
        ws.close()


print()
print("========================================")
print("RESULTADO DO TESTE")
print("========================================")
print("PROCESSADOS :", processados)
print("BAIXADAS    :", baixadas)
print("JÃƒÆ’Ã‚Â EXISTIAM :", existentes)
print("SEM FOTO    :", sem_foto)
print("ERROS       :", erros)
print("========================================")







