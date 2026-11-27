from pathlib import Path

p = Path("app.py")
s = p.read_text(encoding="utf-8")

alvo = '''WHATSAPP = "551734623188"


def db_headers():'''

novo = '''WHATSAPP = "551734623188"

ARQUIVO_CACHE_PRODUTOS = "produtos_cache.json"


def carregar_produtos_cache():

    caminho = Path(ARQUIVO_CACHE_PRODUTOS)

    if caminho.exists():

        try:

            return json.loads(
                caminho.read_text(
                    encoding="utf-8"
                )
            )

        except Exception:

            pass

    produtos = []

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

        produtos.extend(
            dados.get(
                "data",
                []
            )
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

    caminho.write_text(
        json.dumps(
            produtos,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    return produtos


def db_headers():'''

if alvo not in s:
    raise SystemExit("TRECHO NAO ENCONTRADO")

s = s.replace(
    alvo,
    novo,
    1
)

p.write_text(
    s,
    encoding="utf-8"
)

print("CACHE DE PRODUTOS CRIADO")
