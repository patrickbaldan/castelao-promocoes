from pathlib import Path

p = Path("app.py")
s = p.read_text(encoding="utf-8")

inicio = s.index("            else:\n\n                pagina = 1", s.index('def inicio():'))
fim = s.index("\n        except Exception as e:", inicio)

novo = '''            else:

                produtos_cache = carregar_produtos_cache()

                produtos = [
                    produto
                    for produto in produtos_cache
                    if termo in unicodedata.normalize(
                        "NFKD",
                        str(
                            produto.get(
                                "nome",
                                ""
                            )
                        )
                    ).encode(
                        "ascii",
                        "ignore"
                    ).decode().lower()
                ]'''

s = s[:inicio] + novo + s[fim:]

p.write_text(s, encoding="utf-8")

print("PESQUISA POR NOME ALTERADA PARA CACHE")
