import app
import requests

codigos = [1110, 5464, 2582]

for codigo in codigos:
    rotas = [
        f"/produtos/{codigo}/fotos",
        f"/produtos/{codigo}/imagens",
    ]

    for rota in rotas:
        try:
            resposta = requests.get(
                app.BASE_API + rota,
                headers=app.db_headers(),
                timeout=15,
            )
            print(f"\nProduto: {codigo} | Rota: {rota}")
            print(f"HTTP: {resposta.status_code}")
            print(resposta.text[:500])
        except Exception as erro:
            print(f"Erro: {erro}")