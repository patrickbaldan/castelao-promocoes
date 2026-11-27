from flask import Flask, request, render_template_string, redirect, url_for
import os
from pathlib import Path
import requests
import urllib.parse
import base64
import json
import time
import websocket

app = Flask(__name__)

BASE_API = "http://erp.dbsoftware.com.br/api/v1"
WHATSAPP = "551734623188"

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


def db_headers():
    token = os.environ.get("DBSOFTWARE_TOKEN")

    if not token:
        raise RuntimeError("DBSOFTWARE_TOKEN nÃ£o estÃ¡ configurado.")

    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }


def buscar_produto(produto_id):
    resposta = requests.get(
        f"{BASE_API}/produtos/{produto_id}",
        headers=db_headers(),
        timeout=30
    )

    resposta.raise_for_status()

    dados = resposta.json()

    return dados.get("data", {})


def buscar_foto_produto(produto_id):
    resposta = requests.get(
        f"{BASE_API}/produtos/{produto_id}/fotos",
        headers=db_headers(),
        timeout=30
    )

    resposta.raise_for_status()
    dados = resposta.json()

    conteudo = dados.get("data", {})
    geral = conteudo.get("geral", []) if isinstance(conteudo, dict) else []

    if not geral:
        print(f"Nenhuma foto encontrada para o produto ID {produto_id}")
        print("Resposta da API:", dados)
        return None

    foto_capa = next(
        (foto for foto in geral if foto.get("is_capa") is True),
        geral[0]
    )

    urls = foto_capa.get("urls") or {}

    foto_url = (
        urls.get("medium")
        or urls.get("full")
        or urls.get("thumb")
        or foto_capa.get("url")
    )

    print(f"Produto {produto_id} - URL da foto: {foto_url}")

    return foto_url

        pasta = os.path.join(
            "static",
            "fotos"
        )

        os.makedirs(
            pasta,
            exist_ok=True
        )

        arquivo = os.path.join(
            pasta,
            f"{produto_id}.png"
        )

        if os.path.exists(arquivo):

            print(
                "FOTO JÃ EXISTE:",
                arquivo
            )

            return f"/static/fotos/{produto_id}.png"

        abas = requests.get(
            "http://127.0.0.1:9222/json",
            timeout=10
        ).json()

        aba = next(
            x for x in abas
            if x.get("type") == "page"
            and x.get(
                "url",
                ""
            ).startswith(
                "https://erp.dbsoftware.com.br"
            )
        )

        print(
            "ABA ENCONTRADA PARA FOTO:",
            aba["url"]
        )

        ws = websocket.create_connection(
            aba["webSocketDebuggerUrl"],
            timeout=60,
            origin="http://127.0.0.1:9222"
        )

        contador = 0

        def enviar(method, params=None):

            nonlocal contador

            contador += 1

            ws.send(
                json.dumps({
                    "id": contador,
                    "method": method,
                    "params": params or {}
                })
            )

            return contador

        enviar(
            "Page.enable"
        )

        time.sleep(1)

        enviar(
            "Page.navigate",
            {
                "url": foto_url
            }
        )

        print(
            "NAVEGAÃ‡ÃƒO PARA FOTO ENVIADA"
        )

        time.sleep(5)

        comando = enviar(
            "Page.captureScreenshot",
            {
                "format": "png"
            }
        )

        print(
            "CAPTURANDO FOTO..."
        )

        while True:

            retorno = json.loads(
                ws.recv()
            )

            if retorno.get("id") != comando:
                continue

            if "result" not in retorno:

                print(
                    "ERRO CDP:",
                    retorno
                )

                ws.close()

                return None

            imagem_base64 = retorno[
                "result"
            ]["data"]

            imagem = base64.b64decode(
                imagem_base64
            )

            with open(
                arquivo,
                "wb"
            ) as f:

                f.write(imagem)

            ws.close()

            print(
                "FOTO SALVA:",
                arquivo
            )

            print(
                "BYTES:",
                len(imagem)
            )

            return f"/static/fotos/{produto_id}.png"

    except Exception as e:

        print(
            "ERRO AO BUSCAR FOTO:",
            repr(e)
        )

        return None


HTML_BUSCA = """
<!DOCTYPE html>
<html lang="pt-BR">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Castelão Promoções</title>

    <style>

        * {
            box-sizing: border-box;
        }

        body {
            font-family: Arial, sans-serif;
            background: #f3f3f3;
            margin: 0;
        }

        header {
            background: #ff6a00;
            color: white;
            padding: 22px;
            text-align: center;
        }

        header h1 {
            margin: 0;
        }

        .container {
            max-width: 1200px;
            margin: 25px auto;
            padding: 20px;
        }

        .busca {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }

        input[type="text"] {
            width: 70%;
            padding: 13px;
            border: 1px solid #ccc;
            border-radius: 6px;
            font-size: 16px;
        }

        button,
        .botao {
            background: #ff6a00;
            color: white;
            border: none;
            padding: 13px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            text-decoration: none;
            display: inline-block;
        }

        button:hover,
        .botao:hover {
            background: #e65f00;
        }

        .produto {
            background: white;
            padding: 20px;
            margin-bottom: 12px;
            border-radius: 10px;
            border-left: 5px solid #ff6a00;
        }

        .produto h3 {
            margin-top: 0;
            margin-bottom: 12px;
        }

        .info {
            color: #555;
            margin: 5px 0;
        }

        .preco {
            font-size: 21px;
            font-weight: bold;
            color: #ff6a00;
            margin: 12px 0;
        }

        .erro {
            background: #ffe0e0;
            color: #a00000;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }

        @media (max-width: 700px) {

            input[type="text"] {
                width: 100%;
                margin-bottom: 10px;
            }

            .botao {
                width: 100%;
                text-align: center;
            }

        }

    </style>

</head>

<body>

<header>

    <h1>CASTELÃO PARAFUSOS</h1>

    <p>Central de Promoções</p>

</header>

<div class="container">

    <div class="busca">

        <form method="GET">

            <input
                type="text"
                name="busca"
                value="{{ busca }}"
                placeholder="Digite o nome ou cÃ³digo do produto..."
                autofocus
            >

            <button type="submit">
                ðŸ”Ž Buscar produto
            </button>

        </form>

    </div>

    {% if erro %}

        <div class="erro">
            {{ erro }}
        </div>

    {% endif %}

    {% if busca and produtos %}

        <h2>Produtos encontrados</h2>

        {% for produto in produtos %}

            <div class="produto">

                <div style="text-align:center; margin-bottom:12px;">
                    <img
                        src="{{ url_for("static", filename="fotos/" ~ produto.get("id") ~ ".png") }}"
                        alt="produto"
                        onerror="this.style.display='none';"
                        style="max-width:100%; max-height:180px; object-fit:contain; border-radius:8px;"
                    >
                </div>

                <h3>
                    {{ produto.get("nome", "") }}
                </h3>

                <div class="info">
                    <strong>ID:</strong>
                    {{ produto.get("id", "") }}
                </div>

                <div class="info">
                    <strong>CÃ³digo:</strong>
                    {{ produto.get("codigo_externo", "") }}
                </div>

                <div class="info">
                    <strong>Categoria:</strong>
                    {{ produto.get("categoria", "") }}
                </div>

                <div class="info">
                    <strong>Marca:</strong>
                    {{ produto.get("marca", "") }}
                </div>

                <div class="preco">
                    R$ {{ "%.2f"|format(produto.get("preco_venda", 0)|float) }}
                </div>

                <a
                    class="botao"
                    href="{{ url_for('criar_promocao', produto_id=produto.get('id')) }}"
                >
                    ðŸ”¥ Criar promoção
                </a>

            </div>

        {% endfor %}

    {% elif busca %}

        <p>Nenhum produto encontrado.</p>

    {% endif %}

</div>

</body>

</html>
"""


HTML_PROMOCAO = """
<!DOCTYPE html>
<html lang="pt-BR">

<head>

    <meta charset="UTF-8">

    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <title>Criar Promoção</title>

    <style>

        * {
            box-sizing: border-box;
        }

        body {
            font-family: Arial, sans-serif;
            background: #f3f3f3;
            margin: 0;
        }

        header {
            background: #ff6a00;
            color: white;
            padding: 22px;
            text-align: center;
        }

        .container {
            max-width: 800px;
            margin: 25px auto;
            padding: 20px;
        }

        .card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        h2 {
            margin-top: 0;
        }

        .linha {
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }

        .label {
            color: #666;
            font-size: 14px;
        }

        .valor {
            font-size: 18px;
            font-weight: bold;
        }

        .preco-normal {
            font-size: 22px;
            color: #555;
        }

        .estoque {
            color: #008000;
            font-weight: bold;
        }

        .campo {
            margin-top: 25px;
        }

        .campo label {
            display: block;
            font-weight: bold;
            margin-bottom: 8px;
        }

        .campo input {
            width: 100%;
            padding: 14px;
            border: 2px solid #ff6a00;
            border-radius: 7px;
            font-size: 20px;
        }

        .check {
            margin-top: 18px;
            font-size: 16px;
        }

        .acoes {
            margin-top: 25px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        button,
        .botao {
            background: #ff6a00;
            color: white;
            border: none;
            padding: 14px 20px;
            border-radius: 7px;
            cursor: pointer;
            font-weight: bold;
            text-decoration: none;
        }

        .voltar {
            background: #555;
        }

        .resultado {
            margin-top: 25px;
            background: #fff7f0;
            border: 2px solid #ff6a00;
            border-radius: 10px;
            padding: 20px;
        }

        .resultado textarea {
            width: 100%;
            min-height: 220px;
            padding: 12px;
            font-size: 16px;
            border-radius: 6px;
            border: 1px solid #ccc;
        }

        .whatsapp {
            background: #25D366;
        }

        .whatsapp:hover {
            background: #1ebe5d;
        }

        .erro {
            background: #ffe0e0;
            color: #a00000;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }

    </style>

</head>

<body>

<header>

    <h1>CASTELÃO PARAFUSOS</h1>

    <p>Criar Promoção</p>

</header>

<div class="container">

    <div class="card">

        <h2>{{ produto.get("nome", "") }}</h2>

        {% if foto_url %}
        <div style="text-align:center; margin:20px 0;">
            <img src="{{ foto_url }}" alt="produto" style="max-width:100%; max-height:300px; object-fit:contain; border-radius:10px;">
        </div>
        {% endif %}

        <div class="linha">

            <div class="label">CÃ³digo</div>

            <div class="valor">
                {{ produto.get("codigo_externo", "") }}
            </div>

        </div>

        <div class="linha">

            <div class="label">Marca</div>

            <div class="valor">
                {{ produto.get("marca", "") }}
            </div>

        </div>

        <div class="linha">

            <div class="label">Categoria</div>

            <div class="valor">
                {{ produto.get("categoria", "") }}
            </div>

        </div>

        <div class="linha">

            <div class="label">Preço atual</div>

            <div class="preco-normal">
                R$ {{ "%.2f"|format(produto.get("preco_venda", 0)|float) }}
            </div>

        </div>

        <div class="linha">

            <div class="label">Estoque atual</div>

            <div class="estoque">
                {{ produto.get("estoque_atual", 0) }} unidades
            </div>

        </div>

        <form method="POST">

            <div class="campo">

                <label>
                    Preço promocional
                </label>

                <input
                    type="text"
                    name="preco_promocional"
                    placeholder="Ex.: 6,99"
                    required
                >

            </div>

            <div class="check">

                <label>

                    <input
                        type="checkbox"
                        name="avista"
                        checked
                    >

                    Pagamento Ã  vista

                </label>

            </div>

            <div class="acoes">

                <button type="submit">
                    ðŸ”¥ Gerar promoÃ§Ã£o
                </button>

                <a
                    class="botao voltar"
                    href="{{ url_for('inicio') }}"
                >
                    â† Voltar
                </a>

            </div>

        </form>

        {% if texto %}

    <div class="resultado">

        <h3>Texto da promoÃ§Ã£o</h3>

        <div
            id="previewPromocao"
            style="
                background:white;
                border:1px solid #ddd;
                border-radius:10px;
                padding:15px;
                text-align:center;
            "
        >

            {% if foto_url %}

            <img
                src="{{ foto_url }}"
                alt="produto"
                style="
                    max-width:100%;
                    max-height:300px;
                    object-fit:contain;
                    border-radius:10px;
                    margin-bottom:15px;
                "
            >

            {% endif %}

            <div
                style="
                    white-space:pre-line;
                    text-align:left;
                    font-size:16px;
                    line-height:1.5;
                "
            >
                {{ texto }}
            </div>

        </div>

        <br>

      <button
    type="button"
    class="botao whatsapp"
    onclick="compartilharPromocao()"
>
    ðŸ“² Compartilhar promoÃ§Ã£o no WhatsApp
</button>


        <canvas
            id="canvasPromocao"
            style="display:none;"
        ></canvas>

    </div>

{% endif %}

    </div>

</div>

<script>

async function compartilharPromocao() {

    const imagemProduto = document.querySelector("img[alt='produto']");

    if (!imagemProduto) {
        alert("Foto do produto nÃ£o encontrada.");
        return;
    }

    const canvas = document.getElementById("canvasPromocao");
    const ctx = canvas.getContext("2d");

    canvas.width = 1080;
    canvas.height = 1350;

    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = "#ff6a00";
    ctx.fillRect(0, 0, canvas.width, 180);

    ctx.fillStyle = "#ffffff";
    ctx.textAlign = "center";

    ctx.font = "bold 52px Arial";
    ctx.fillText("CASTELÃO PARAFUSOS", 540, 75);

    ctx.font = "bold 34px Arial";
    ctx.fillText("OFERTA ESPECIAL", 540, 135);

    const nome = document.querySelector("h2").innerText;

    ctx.fillStyle = "#222222";
    ctx.font = "bold 38px Arial";

    let nomeTexto = nome;

    if (nomeTexto.length > 42) {
        nomeTexto = nomeTexto.substring(0, 42) + "...";
    }

    ctx.fillText(nomeTexto, 540, 240);

    const proporcao = Math.min(
        800 / imagemProduto.naturalWidth,
        500 / imagemProduto.naturalHeight
    );

    const largura = imagemProduto.naturalWidth * proporcao;
    const altura = imagemProduto.naturalHeight * proporcao;

    ctx.drawImage(
        imagemProduto,
        (1080 - largura) / 2,
        280,
        largura,
        altura
    );

    const precoNormal = document.querySelector(
        ".preco-normal"
    ).innerText;

    const textoPromocao = document.querySelector(
        "#previewPromocao div[style*='white-space']"
    ).innerText;

    const linhaPreco = textoPromocao
        .split("\\n")
        .find(linha => linha.trim().startsWith("POR R$"));

    const precoPromocional = linhaPreco
        ? linhaPreco.replace("POR R$", "").trim()
        : "";

    ctx.fillStyle = "#777777";
    ctx.font = "32px Arial";

    ctx.fillText(
        "De " + precoNormal,
        540,
        850
    );

    ctx.fillStyle = "#ff6a00";
    ctx.font = "bold 58px Arial";

    ctx.fillText(
        "POR R$ " + precoPromocional.replace(".", ","),
        540,
        930
    );

    ctx.fillStyle = "#222222";
    ctx.font = "bold 32px Arial";

   ctx.fillText(
    "PAGAMENTO À VISTA",
    540,
    1000
);

    ctx.fillStyle = "#25D366";
    ctx.fillRect(
        190,
        1070,
        700,
        100
    );

    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 34px Arial";

    ctx.fillText(
        "17 3462-3188",
        540,
        1135
    );

    ctx.fillStyle = "#222222";
    ctx.font = "28px Arial";

    ctx.fillText(
        "Peca ja pelo WhatsApp!",
        540,
        1240
    );

    canvas.toBlob(function(blob) {

        if (!blob) {
            alert("Nao foi possivel gerar a imagem.");
            return;
        }

        const texto = document.querySelector(
            ".resultado div[style*='white-space']"
        ).innerText;

        const mensagem = encodeURIComponent(texto);

        window.open(
            "https://web.whatsapp.com/send?phone=551734623188&text=" + mensagem,
            "_blank"
        );

        const linkDownload = document.createElement("a");

        linkDownload.download = "promocao-castelao.png";

        linkDownload.href = URL.createObjectURL(blob);

        linkDownload.click();

        setTimeout(function() {
            URL.revokeObjectURL(linkDownload.href);
        }, 1000);

    }, "image/png");
}
</script>
</body>

</html>
"""

@app.route("/")
def inicio():

    busca = request.args.get("busca", "").strip()

    produtos = []

    erro = None

    if busca:

        try:

            import unicodedata

            termo = unicodedata.normalize(
                "NFKD",
                busca
            ).encode(
                "ascii",
                "ignore"
            ).decode().lower()

            # Se for nÃºmero, procura pelo cÃ³digo em todas as pÃ¡ginas.
            if busca.isdigit():

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

                        codigo = str(
                            produto.get(
                                "codigo_externo",
                                ""
                            )
                        ).strip()

                        if codigo == busca:

                            produtos.append(
                                produto
                            )

                    if produtos:
                        break

                    pagina += 1

            else:

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
                ]
        except Exception as e:

            erro = str(e)

    return render_template_string(
        HTML_BUSCA,
        busca=busca,
        produtos=produtos,
        erro=erro
    )

@app.route("/promocao/<int:produto_id>", methods=["GET", "POST"])
def criar_promocao(produto_id):

    erro = None
    texto = None
    whatsapp_url = None

    try:

        produto = buscar_produto(produto_id)

        foto_url = buscar_foto_produto(produto_id)

        if not produto:
            return "Produto nÃ£o encontrado.", 404

        if request.method == "POST":

            valor_digitado = request.form.get(
                "preco_promocional",
                ""
            ).strip()

            valor_digitado = valor_digitado.replace(",", ".")

            preco_promocional = float(valor_digitado)

            preco_atual = float(
                produto.get("preco_venda", 0)
            )

            if preco_promocional <= 0:

                raise ValueError(
                    "O preÃ§o promocional deve ser maior que zero."
                )

            if preco_promocional >= preco_atual:

                raise ValueError(
                    "O preÃ§o promocional deve ser menor que o preÃ§o atual."
                )

            desconto = (
                (preco_atual - preco_promocional)
                / preco_atual
            ) * 100

            nome = produto.get("nome", "")
            codigo = produto.get("codigo_externo", "")
            marca = produto.get("marca", "")

            avista = request.form.get("avista") == "on"

            texto = (
                "ðŸ”¥ OFERTA CASTELÃO PARAFUSOS ðŸ”¥\n\n"
                f"{nome}\n\n"
                f"CÃ³digo: {codigo}\n"
                f"Marca: {marca}\n\n"
                f"De R$ {preco_atual:.2f}".replace(".", ",")
                + "\n"
                + f"POR R$ {preco_promocional:.2f}".replace(".", ",")
                + "\n\n"
                + f"ðŸ’¥ {desconto:.0f}% DE DESCONTO"
                + "\n\n"
            )

            if avista:

                texto += "ðŸ’° PAGAMENTO À VISTA\n\n"

            texto += (
                "ðŸ“² Peça já pelo WhatsApp:\n"
                "17 3462-3188"
            )

            whatsapp_url = (
                "https://wa.me/"
                + WHATSAPP
                + "?text="
                + urllib.parse.quote(texto)
            )

    except Exception as e:

        produto = produto if "produto" in locals() else {}

        erro = str(e)

    return render_template_string(
        HTML_PROMOCAO,
        produto=produto,
        foto_url=foto_url,
        texto=texto,
        whatsapp_url=whatsapp_url,
        erro=erro
    )


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8010,
        debug=True,
        use_reloader=False
    )


