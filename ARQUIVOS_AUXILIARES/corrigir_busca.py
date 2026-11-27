from pathlib import Path

p = Path("app.py")
s = p.read_text(encoding="utf-8")

antigo = '''            produtos = dados.get("data", [])'''

novo = '''            produtos = dados.get("data", [])

            import unicodedata

            termo = unicodedata.normalize(
                "NFKD",
                busca
            ).encode(
                "ascii",
                "ignore"
            ).decode().lower()

            produtos = [
                produto
                for produto in produtos
                if termo in unicodedata.normalize(
                    "NFKD",
                    str(produto.get("nome", ""))
                ).encode(
                    "ascii",
                    "ignore"
                ).decode().lower()
            ]'''

print("ENCONTROU:", antigo in s)

if antigo not in s:
    print("TRECHO NÃO ENCONTRADO")
else:
    s = s.replace(antigo, novo, 1)
    p.write_text(s, encoding="utf-8")
    print("FILTRO DE BUSCA CORRIGIDO")