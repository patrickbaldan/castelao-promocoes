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
        "page": 1,
        "per_page": 100
    },
    headers=headers,
    timeout=30
)

print("STATUS:", resposta.status_code)

dados = resposta.json()

print("TOTAL:", dados.get("meta", {}).get("total"))
print("ÚLTIMA PÁGINA:", dados.get("meta", {}).get("last_page"))