from pathlib import Path
from datetime import datetime
import py_compile
import shutil
import sys

arquivo = Path("app.py")
codigo = arquivo.read_text(encoding="utf-8")

inicio = "def buscar_foto_produto(produto_id):\n"
alvo = inicio + "    resposta = requests.get("

bloco_novo = inicio + '''    # Prioriza fotos que ja foram sincronizadas para o computador.
    pasta_local = Path("static") / "fotos"
    for extensao in (".webp", ".png", ".jpg", ".jpeg"):
        for nome in (
            f"dbsoftware_{produto_id}{extensao}",
            f"{produto_id}{extensao}",
        ):
            local = pasta_local / nome
            if local.is_file() and local.stat().st_size > 1000:
                return f"/static/fotos/{nome}"

    resposta = requests.get('''

if "Prioriza fotos que ja foram sincronizadas" in codigo:
    print("A correção das fotos locais já está aplicada.")
else:
    if codigo.count(alvo) != 1:
        print("Não alterei o arquivo: o trecho esperado não foi encontrado exatamente uma vez.")
        sys.exit(1)

    backup = Path(
        "app_backup_foto_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".py"
    )
    shutil.copy2(arquivo, backup)

    codigo = codigo.replace(alvo, bloco_novo, 1)
    arquivo.write_text(codigo, encoding="utf-8")

    try:
        py_compile.compile(str(arquivo), doraise=True)
    except Exception as erro:
        print("A verificação falhou:", erro)
        print("Restaurando o backup...")
        shutil.copy2(backup, arquivo)
        sys.exit(1)

    print("Correção aplicada e sintaxe verificada.")
    print("Backup:", backup)

