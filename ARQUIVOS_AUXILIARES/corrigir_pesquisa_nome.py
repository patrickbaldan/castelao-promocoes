from pathlib import Path

p = Path("app.py")
linhas = p.read_text(encoding="utf-8").splitlines()

novo = '''            else:

                pagina = 1
                ultima_pagina = 1

                while pagina <= ultima_pagina:

                    resposta = requests.get(
                        f"{BASE_API}/produtos",
                        params={
                            "page": pagina,
                            "per_page": 100,
                            "busca": busca
                        },
                        headers=db_headers(),
                        timeout=30
                    )

                    resposta.raise_for_status()

                    dados = resposta.json()

                    pagina_produtos = dados.get(
                        "data",
                        []
                    )

                    meta = dados.get(
                        "meta",
                        {}
                    )

                    ultima_pagina = int(
                        meta.get(
                            "last_page",
                            1
                        )
                    )

                    for produto in pagina_produtos:

                        nome = unicodedata.normalize(
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

                        if termo in nome:

                            produtos.append(
                                produto
                            )

                    pagina += 1'''.splitlines()

linhas[1077:1115] = novo

p.write_text("\n".join(linhas) + "\n", encoding="utf-8")

print("ALTERAÇÃO CONCLUÍDA")
