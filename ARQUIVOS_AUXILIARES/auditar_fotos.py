import json
import csv
from pathlib import Path

base = Path.cwd()
produtos = json.loads((base / "produtos_cache.json").read_text(encoding="utf-8"))
pasta = base / "static" / "fotos"

extensoes = {".png", ".webp", ".jpg", ".jpeg"}
nomes = {
    arquivo.stem.lower()
    for arquivo in pasta.iterdir()
    if arquivo.is_file() and arquivo.suffix.lower() in extensoes
}

sem_foto = []
for produto in produtos:
    identificador = str(produto.get("id", "")).lower()
    if identificador not in nomes and f"dbsoftware_{identificador}" not in nomes:
        sem_foto.append({
            "ID": produto.get("id"),
            "Produto": produto.get("nome"),
            "CodigoExterno": produto.get("codigo_externo")
        })

saida = base / "produtos_sem_foto.csv"
with saida.open("w", newline="", encoding="utf-8-sig") as arquivo:
    escritor = csv.DictWriter(arquivo, fieldnames=["ID", "Produto", "CodigoExterno"])
    escritor.writeheader()
    escritor.writerows(sem_foto)

print("Produtos no catálogo:", len(produtos))
print("Arquivos de imagem encontrados:", len(nomes))
print("Produtos sem foto local correspondente:", len(sem_foto))
print("Relatório:", saida)
print("\nPrimeiros 20 produtos sem foto:")
for produto in sem_foto[:20]:
    print(produto["ID"], "-", produto["Produto"], "| código:", produto["CodigoExterno"])
