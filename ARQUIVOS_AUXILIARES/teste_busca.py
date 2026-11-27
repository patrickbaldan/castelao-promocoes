import requests
import os

TOKEN = os.getenv("DBSOFTWARE_TOKEN")

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json"
}

resposta = requests.get(
    "http://erp.dbsoftware.com.br/api/v1/produtos",
    params={
        "busca": "porca",
        "page": 1,
        "per_page": 20
    },
    headers=headers,
    timeout=30
)

print("STATUS:", resposta.status_code)

dados = resposta.json()

print("RESULTADOS:")

for produto in dados.get("data", []):
    print(
        produto.get("id"),
        "|",
        produto.get("nome")
    )