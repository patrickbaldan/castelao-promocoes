import requests
import os

TOKEN = os.getenv("DBSOFTWARE_TOKEN")

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json"
}

produto_id = 2043

resposta = requests.get(
    f"http://erp.dbsoftware.com.br/api/v1/produtos/{produto_id}/fotos",
    headers=headers,
    timeout=30
)

print("STATUS:", resposta.status_code)
print()
print(resposta.json())