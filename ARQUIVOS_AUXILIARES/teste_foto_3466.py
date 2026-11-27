
import os
import requests
from pathlib import Path
from sincronizar_fotos_completo import obter_foto, baixar_foto

produto_id = 3466
pasta = Path("static") / "fotos"
pasta.mkdir(parents=True, exist_ok=True)

url = obter_foto(produto_id)

if not url:
    raise RuntimeError("O ERP não retornou uma foto para o produto 3466.")

print("URL encontrada:", url)

arquivo = str(pasta / "3466.png")

print("Tentando capturar a imagem usando o Chrome...")
tamanho = baixar_foto(produto_id, url, arquivo)

print("FOTO SALVA:", arquivo)
print("Tamanho:", tamanho, "bytes")
