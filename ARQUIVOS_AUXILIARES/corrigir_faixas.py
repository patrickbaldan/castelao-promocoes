from pathlib import Path
from PIL import Image
import shutil

pasta = Path("static/fotos")
backup = Path("static/fotos_backup_originais")
backup.mkdir(exist_ok=True)

extensoes = {".png", ".jpg", ".jpeg", ".webp"}
corrigidas = 0
mantidas = 0

for arquivo in pasta.iterdir():
    if not arquivo.is_file() or arquivo.suffix.lower() not in extensoes:
        continue

    if any(p in arquivo.stem.lower() for p in ("backup", "teste", "corrigindo")):
        continue

    try:
        with Image.open(arquivo) as img:
            formato = img.format
            img = img.convert("RGB")

        w, h = img.size
        if w < 100 or h < 100:
            mantidas += 1
            continue

        # Detecta faixas quase pretas em mais de 90% da altura.
        def coluna_escura(x):
            amostras = [
                max(img.getpixel((x, y)))
                for y in range(0, h, max(1, h // 100))
            ]
            return sum(v < 45 for v in amostras) / len(amostras) > 0.90

        esq = 0
        while esq < w // 3 and coluna_escura(esq):
            esq += 1

        dir_ = w - 1
        while dir_ > 2 * w // 3 and coluna_escura(dir_):
            dir_ -= 1

        if esq < 20 or w - 1 - dir_ < 20 or dir_ <= esq:
            mantidas += 1
            continue

        destino = backup / arquivo.name
        if not destino.exists():
            shutil.copy2(arquivo, destino)

        recorte = img.crop((esq, 0, dir_ + 1, h))
        temporario = arquivo.with_name(arquivo.stem + "_novo" + arquivo.suffix)

        if formato == "JPEG":
            recorte.save(temporario, format=formato, quality=95)
        else:
            recorte.save(temporario, format=formato)

        temporario.replace(arquivo)
        print(f"CORRIGIDA: {arquivo.name} ({esq}px / {w - 1 - dir_}px)")
        corrigidas += 1

    except Exception as erro:
        print(f"ERRO: {arquivo.name}: {erro}")

print("\nFINALIZADO")
print("Corrigidas:", corrigidas)
print("Mantidas:", mantidas)
print("Backups em:", backup.resolve())
