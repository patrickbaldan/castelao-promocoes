import sqlite3
import requests
import os
import json
import time
import base64
import websocket
from pathlib import Path

BASE_API = "http://erp.dbsoftware.com.br/api/v1"
TOKEN = os.getenv("DBSOFTWARE_TOKEN")
BANCO = "promocoes.db"

PASTA_FOTOS = Path("static/fotos")
PASTA_FOTOS.mkdir(parents=True, exist_ok=True)

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json"
}


def baixar_foto(produto_id):

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
        raise Exception(
            "Chrome com depuração não encontrado."
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
        headers=headers,
        timeout=30
    )

    resposta.raise_for_status()

    dados = resposta.json()

    geral = dados.get("data", {}).get("geral", [])

    if not geral:

        ws.close()

        return None

    capa = next(
        (
            foto for foto in geral
            if foto.get("is_capa")
        ),
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

for(let i = 0; i < bytes.length; i += 8192){

    binary += String.fromCharCode(
        ...bytes.subarray(i, i + 8192)
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

    valor = (
        resultado
        ["result"]
        ["result"]
        ["value"]
    )

    imagem = base64.b64decode(
        valor["base64"]
    )

    ws.close()

    return imagem


conn = sqlite3.connect(BANCO)

cursor = conn.cursor()

cursor.execute("""
SELECT id, nome
FROM produtos
WHERE foto_local IS NULL
ORDER BY id
LIMIT 10
""")

produtos = cursor.fetchall()

print()
print("========================================")
print("TESTE DE SINCRONISMO DE FOTOS")
print("PRODUTOS:", len(produtos))
print("========================================")

baixadas = 0
sem_foto = 0
erros = 0

for numero, (produto_id, nome) in enumerate(
    produtos,
    start=1
):

    print()
    print(
        f"[{numero}/{len(produtos)}] "
        f"{produto_id} | {nome}"
    )

    try:

        imagem = baixar_foto(produto_id)

        if not imagem:

            print("SEM FOTO")
            sem_foto += 1
            continue

        arquivo = (
            PASTA_FOTOS
            / f"{produto_id}.webp"
        )

        arquivo.write_bytes(imagem)

        caminho = (
            f"/static/fotos/{produto_id}.webp"
        )

        cursor.execute(
            """
            UPDATE produtos
            SET foto_local = ?
            WHERE id = ?
            """,
            (caminho, produto_id)
        )

        conn.commit()

        print(
            "FOTO SALVA:",
            arquivo
        )

        baixadas += 1

    except Exception as e:

        print(
            "ERRO:",
            e
        )

        erros += 1

conn.commit()
conn.close()

print()
print("========================================")
print("TESTE FINALIZADO")
print("FOTOS BAIXADAS:", baixadas)
print("SEM FOTO:", sem_foto)
print("ERROS:", erros)
print("========================================")