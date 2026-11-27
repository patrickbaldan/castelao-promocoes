from pathlib import Path

p = Path("app.py")
s = p.read_text(encoding="utf-8")

inicio = s.index("            else:\n\n                pagina = 1", s.index('def inicio():'))
fim = s.index("\n        except Exception as e:", inicio)

novo = '''            else:

                if not hasattr(app, "cache_produtos_pesquisa"):

                    app.cache_produtos_pesquisa = []

                    pagina = 1
                    ultima_pagina = 1

                    while pagina <= ultima_pagina:

                        resposta = requests.get(
                            f"{BASE_API}/produtos",
                            params={
                                "page": pagina,
                                "per_page": 100
                            },
                            headers=db_headers(),
                            timeout=30
                        )

                        resposta.raise_for_status()

                        dados = resposta.json()

                        app.cache_produtos_pesquisa.extend(
                            dados.get("data", [])
                        )

                        ultima_pagina = int(
                            dados.get(
                                "meta",
                                {}
                            ).get(
                                "last_page",
                                1
                            )
                        )

                        pagina += 1

                produtos = [
                    produto
                    for produto in app.cache_produtos_pesquisa
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

print("CORREÇÃO DO CACHE CONCLUÍDA")
