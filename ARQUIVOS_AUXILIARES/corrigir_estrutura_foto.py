from pathlib import Path

p = Path("app.py")
s = p.read_text(encoding="utf-8")

s = s.replace(
    '        fotos = dados.get("data", [])\n\n        if not fotos:\n            print("PRODUTO SEM FOTO:", produto_id)\n            return None\n\n        foto_url = fotos[0].get("url")',
    '''        fotos = dados.get("data", {}).get("geral", [])

        if not fotos:
            print("PRODUTO SEM FOTO:", produto_id)
            return None

        foto_url = fotos[0].get("urls", {}).get("full")'''
)

p.write_text(s, encoding="utf-8")

print("ESTRUTURA DA FOTO CORRIGIDA")