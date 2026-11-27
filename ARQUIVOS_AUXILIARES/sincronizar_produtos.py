import sqlite3
import requests
import os
from datetime import datetime

BASE_API = "http://erp.dbsoftware.com.br/api/v1"
TOKEN = os.getenv("DBSOFTWARE_TOKEN")
BANCO = "promocoes.db"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json"
}

conn = sqlite3.connect(BANCO)
cursor = conn.cursor()

pagina = 1
total = 0
erros = 0

while True:

    print(f"\nBuscando página {pagina}...")

    resposta = requests.get(
        f"{BASE_API}/produtos",
        params={
            "page": pagina,
            "per_page": 100
        },
        headers=headers,
        timeout=60
    )

    resposta.raise_for_status()

    dados = resposta.json()
    produtos = dados.get("data", [])

    if not produtos:
        break

    for produto in produtos:

        produto_id = produto.get("id")

        try:
            detalhe = requests.get(
                f"{BASE_API}/produtos/{produto_id}",
                headers=headers,
                timeout=30
            )

            detalhe.raise_for_status()

            produto_completo = detalhe.json().get("data", {})

            cursor.execute("""
            INSERT OR REPLACE INTO produtos (
                id,
                codigo_externo,
                nome,
                marca,
                preco_custo,
                preco_venda,
                estoque,
                atualizado_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                produto_completo.get("id"),
                produto_completo.get("codigo_externo"),
                produto_completo.get("nome"),
                produto_completo.get("marca"),
                produto_completo.get("preco_custo"),
                produto_completo.get("preco_venda"),
                produto_completo.get("estoque_atual"),
                datetime.now().isoformat()
            ))

            total += 1

        except Exception as e:

            erros += 1

            print(
                f"ERRO produto {produto_id}: {e}"
            )

    conn.commit()

    print(
        f"Página {pagina}: "
        f"{len(produtos)} produtos | "
        f"Total: {total} | "
        f"Erros: {erros}"
    )

    pagina += 1

conn.commit()
conn.close()

print()
print("========================================")
print("SINCRONISMO COMPLETO")
print("PRODUTOS:", total)
print("ERROS:", erros)
print("========================================")