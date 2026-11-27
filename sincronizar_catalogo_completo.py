import json
import os
import sqlite3
import time
import requests
from datetime import datetime
from pathlib import Path

BASE_API = "http://erp.dbsoftware.com.br/api/v1"
BANCO = "promocoes.db"
CACHE = Path("produtos_cache.json")
TOKEN = os.getenv("DBSOFTWARE_TOKEN")

if not TOKEN:
    raise SystemExit("ERRO: DBSOFTWARE_TOKEN não está configurado.")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json"
}

sessao = requests.Session()
sessao.headers.update(HEADERS)

conn = sqlite3.connect(BANCO)
cursor = conn.cursor()

catalogo = []
total = 0
erros = []
pagina = 1

try:
    while True:
        resposta = sessao.get(
            f"{BASE_API}/produtos",
            params={"page": pagina, "per_page": 100},
            timeout=60
        )
        resposta.raise_for_status()
        dados = resposta.json()
        lista = dados.get("data", [])

        if not lista:
            break

        ultima_pagina = int(
            dados.get("meta", {}).get("last_page", pagina)
        )

        print(
            f"\nPágina {pagina}/{ultima_pagina} "
            f"- {len(lista)} produtos"
        )

        for item in lista:
            produto_id = item.get("id")

            if not produto_id:
                continue

            try:
                detalhe = sessao.get(
                    f"{BASE_API}/produtos/{produto_id}",
                    timeout=45
                )
                detalhe.raise_for_status()
                produto = detalhe.json().get("data", {})

                if not produto or not produto.get("id"):
                    raise ValueError("Detalhe do produto vazio.")

                catalogo.append(produto)

                cursor.execute("""
                    INSERT OR REPLACE INTO produtos (
                        id, codigo_externo, nome, marca,
                        preco_custo, preco_venda, estoque, atualizado_em
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    produto.get("id"),
                    produto.get("codigo_externo"),
                    produto.get("nome"),
                    produto.get("marca"),
                    produto.get("preco_custo"),
                    produto.get("preco_venda"),
                    produto.get("estoque_atual"),
                    datetime.now().isoformat()
                ))

                total += 1

            except Exception as e:
                erros.append({
                    "id": produto_id,
                    "erro": str(e)
                })
                print(f"  ERRO no produto {produto_id}: {e}")

        conn.commit()
        print(f"Atualizados: {total} | Erros: {len(erros)}")
        pagina += 1

    # Só substitui o cache se todos os produtos da lista
    # tiverem sido obtidos com sucesso.
    total_api = int(
        dados.get("meta", {}).get("total", total)
    )

    if erros or len(catalogo) != total_api:
        relatorio = Path("erros_sincronizacao.json")
        relatorio.write_text(
            json.dumps(erros, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print("\nATENÇÃO: houve falhas.")
        print("O cache antigo foi preservado.")
        print(f"Relatório: {relatorio}")
        print(f"Produtos detalhados: {len(catalogo)} de {total_api}")
    else:
        temporario = CACHE.with_suffix(".tmp")
        temporario.write_text(
            json.dumps(catalogo, ensure_ascii=False),
            encoding="utf-8"
        )
        temporario.replace(CACHE)
        print("\nCache atualizado com sucesso.")

finally:
    conn.close()

print("\n========== RESULTADO ==========")
print("Produtos atualizados:", total)
print("Erros:", len(erros))
print("Fim:", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
