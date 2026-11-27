
from pathlib import Path
from PIL import Image
import shutil

pasta = Path("static/fotos")
backup = Path("static/fotos_backup_vertical")
backup.mkdir(parents=True, exist_ok=True)

extensoes = {".png", ".jpg", ".jpeg", ".webp"}
corrigidas = 0
mantidas = 0
erros = 0

for arquivo in sorted(pasta.iterdir()):
    if not arquivo.is_file() or arquivo.suffix.lower() not in extensoes:
        continue

    nome = arquivo.stem.lower()
    if any(p in nome for p in ("backup", "teste", "temporario", "_novo")):
        continue

    try:
        with Image.open(arquivo) as original:
            formato = original.format
            rgb = original.convert("RGB")

        w, h = rgb.size
        if w < 100 or h < 100:
            mantidas += 1
            continue

        passo = max(1, w // 100)

        def linha_escura(y):
            valores = [
                max(rgb.getpixel((x, y)))
                for x in range(0, w, passo)
            ]
            return sum(v < 45 for v in valores) / len(valores) > 0.90

        topo = 0
        while topo < h // 3 and linha_escura(topo):
            topo += 1

        baixo = h - 1
        while baixo > 2 * h // 3 and linha_escura(baixo):
            baixo -= 1

        cortar_cima = topo
        cortar_baixo = h - 1 - baixo

        if cortar_cima < 20 or cortar_baixo < 20 or baixo <= topo:
            mantidas += 1
            continue

        copia = backup / arquivo.name
        if not copia.exists():
            shutil.copy2(arquivo, copia)

        recorte = rgb.crop((0, topo, w, baixo + 1))
        temporario = arquivo.with_name(arquivo.stem + "_temporario" + arquivo.suffix)

        opcoes = {"quality": 95} if formato == "JPEG" else {}
        recorte.save(temporario, format=formato, **opcoes)
        temporario.replace(arquivo)

        print(f"CORRIGIDA: {arquivo.name} | cima: {cortar_cima}px | baixo: {cortar_baixo}px")
        corrigidas += 1

    except Exception as erro:
        print(f"ERRO: {arquivo.name}: {erro}")
        erros += 1

print("\n===== RESUMO =====")
print("Fotos corrigidas:", corrigidas)
print("Fotos mantidas:", mantidas)
print("Erros:", erros)
print("Backups:", backup.resolve())
