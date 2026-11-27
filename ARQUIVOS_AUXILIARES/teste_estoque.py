import requests
import os

TOKEN = os.getenv("DBSOFTWARE_TOKEN")

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json"
}

resposta = requests.get(
    "http://erp.dbsoftware.com.br/api/v1/produtos/2043",
    headers=headers,
    timeout=30
)

print("STATUS:", resposta.status_code)
print()
print(resposta.json())