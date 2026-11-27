from pathlib import Path

p = Path("app.py")
s = p.read_text(encoding="utf-8")

antigo = """const areaLargura = 880;
const areaAltura = 500;"""

novo = """const areaLargura = 880;
const areaAltura = 500;"""

if antigo not in s:
    print("NAO ALTERADO: nao encontrei o trecho exato.")
else:
    print("O trecho foi localizado. Nenhuma alteracao feita ainda.")
