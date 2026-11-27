import os
import json
import time
import base64
import sqlite3
import requests
import websocket

BASE_API = "http://erp.dbsoftware.com.br/api/v1"
PASTA_FOTOS = os.path.join("static", "fotos")
PER_PAGE = 10

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
            and aba.get("url", "").startswith(
                "https://erp.dbsoftware.com.br"
            )
        ):
            return aba

    raise RuntimeError(
        "Nenhuma aba do DBSoftware encontrada no Chrome."
    )


def abrir_ws():
    aba = buscar_aba_chrome()

    return websocket.create_connection(
        aba["webSocketDebuggerUrl"],
        timeout=60,
        origin="http://127.0.0.1:9222"
    )


def baixar_foto(produto_id, foto_url, arquivo):
    ws = abrir_ws()

    contador = 0

    def enviar(method, params=None):
        nonlocal contador
        contador += 1

        ws.send(json.dumps({
            "id": contador,
            "method": method,
            "params": params or {}
        }))

        return contador

    try:
        enviar("Page.enable")
        time.sleep(0.5)

        enviar(
            "Page.navigate",
            {"url": foto_url}
        )

        time.sleep(3)

        comando = enviar(
            "Page.captureScreenshot",
            {"format": "png"}
        )

        while True:
            retorno = json.loads(ws.recv())

            if retorno.get("id") != comando:
                continue

            if "result" not in retorno:
                raise RuntimeError(
                    f"Erro CDP: {retorno}"
                )

            imagem_base64 = retorno["result"]["data"]

            imagem = base64.b64decode(
                imagem_base64
            )

            with open(arquivo, "wb") as f:
                f.write(imagem)

            return len(imagem)

    finally:
        ws.close()


def obter_produtos(pagina):
    resposta = requests.get(
        f"{BASE_API}/produtos",
        headers=HEADERS,
        params={
            "page": pagina,
            "per_page": PER_PAGE
        },
        timeout=60
    )

    resposta.raise_for_status()

    dados = resposta.json()

    return dados.get("data", []), dados.get("meta", {})


def obter_foto(produto_id):
    resposta = requests.get(
        f"{BASE_API}/produtos/{produto_id}/fotos",
        headers=HEADERS,
        timeout=30
    )

    resposta.raise_for_status()

    dados = resposta.json()

    fotos = dados.get(
        "data", {}
    ).get(
        "geral", []
    )

    if not fotos:
        return None

    capas = [
        f for f in fotos
        if f.get("is_capa") is True
    ]

    foto = capas[0] if capas else fotos[0]

    return foto.get(
        "urls", {}
    ).get("full")


def main():

    print("=" * 60)
    print("SINCRONIZAÇÃO DE FOTOS - DBSoftware")
    print("=" * 60)

    primeira, meta = obter_produtos(1)

    total = int(meta.get("total", 0))
    ultima_pagina = int(
        meta.get("last_page", 1)
    )

    print(f"TOTAL DE PRODUTOS: {total}")
    print(f"TOTAL DE PÁGINAS: {ultima_pagina}")
    print()

    processados = 0
    baixadas = 0
    existentes = 0
    sem_foto = 0
    erros = 0

    for pagina in range(1, ultima_pagina + 1):

        print(
            f"--- PÁGINA {pagina}/{ultima_pagina} ---"
        )

        if pagina == 1:
            produtos = primeira
        else:
            produtos, _ = obter_produtos(pagina)

        for produto in produtos:

            processados += 1

            produto_id = produto.get("id")
            nome = produto.get("nome", "")

            if not produto_id:
                erros += 1
                print(
                    "ERRO: produto sem ID"
                )
                continue

            arquivo = os.path.join(
                PASTA_FOTOS,
                f"{produto_id}.png"
            )

            if os.path.exists(arquivo):
                existentes += 1

                print(
                    f"[{processados}/{total}] "
                    f"JÁ EXISTE {produto_id} - {nome}"
                )

                continue

            try:

                foto_url = obter_foto(
                    produto_id
                )

                if not foto_url:
                    sem_foto += 1

                    print(
                        f"[{processados}/{total}] "
                        f"SEM FOTO {produto_id} - {nome}"
                    )

                    continue

                tamanho = baixar_foto(
                    produto_id,
                    foto_url,
                    arquivo
                )

                baixadas += 1

                print(
                    f"[{processados}/{total}] "
                    f"BAIXADA {produto_id} - "
                    f"{nome} - {tamanho} bytes"
                )

            except Exception as e:

                erros += 1

                print(
                    f"[{processados}/{total}] "
                    f"ERRO {produto_id} - "
                    f"{nome} - {repr(e)}"
                )

    print()
    print("=" * 60)
    print("FINALIZADO")
    print("=" * 60)
    print(f"PROCESSADOS : {processados}")
    print(f"BAIXADAS    : {baixadas}")
    print(f"JÁ EXISTIAM : {existentes}")
    print(f"SEM FOTO    : {sem_foto}")
    print(f"ERROS       : {erros}")
    print("=" * 60)


if __name__ == "__main__":
    main()
