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



@app.route("/atualizar-fotos", methods=["POST"])
def atualizar_fotos():
    import subprocess
    import sys

    try:
        pasta = Path(__file__).resolve().parent
        script = pasta / "sincronizar_fotos_completo.py"
        log = pasta / "resultado_atualizacao_fotos.txt"

        with open(log, "w", encoding="utf-8") as arquivo:
            arquivo.write("Iniciando atualização de fotos...\n")

        with open(log, "a", encoding="utf-8") as arquivo:
            subprocess.Popen(
                [sys.executable, "-u", str(script)],
                cwd=str(pasta),
                stdout=arquivo,
                stderr=subprocess.STDOUT
            )

        return "Atualização iniciada. Resultado será salvo em resultado_atualizacao_fotos.txt.", 200

    except Exception as e:
        return f"Erro ao iniciar atualização: {e}", 500


@app.route("/atualizar-catalogo", methods=["POST"])

@app.route("/atualizar-catalogo", methods=["POST"])
def atualizar_catalogo():
    import subprocess
    import sys

    pasta = Path(__file__).resolve().parent
    script = pasta / "sincronizar_catalogo_completo.py"

    try:
        resultado = subprocess.run(
            [sys.executable, "-u", str(script)],
            cwd=str(pasta),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=1800
        )

        saida = (resultado.stdout or "").strip()
        erros = (resultado.stderr or "").strip()

        if resultado.returncode == 0:
            titulo = "Atualização do catálogo finalizada."
            status = 200
        else:
            titulo = "Erro na atualização do catálogo."
            status = 500

        detalhes = saida or erros or "O script terminou sem apresentar detalhes."

        return (
            f"<h2>{titulo}</h2>"
            f"<pre style='white-space:pre-wrap;overflow-wrap:anywhere'>{detalhes}</pre>"
            "<p><a href='/'>Voltar ao catálogo</a></p>",
            status
        )

    except subprocess.TimeoutExpired:
        return (
            "A atualização ultrapassou 30 minutos e foi interrompida. "
            "<a href='/'>Voltar ao catálogo</a>",
            500
        )
    except Exception as e:
        return (
            f"Não foi possível iniciar a atualização: {e}"
            "<p><a href='/'>Voltar ao catálogo</a></p>",
            500
        )
BASE_API = "http://erp.dbsoftware.com.br/api/v1"
WHATSAPP = "551734623188"

ARQUIVO_CACHE_PRODUTOS = "produtos_cache.json"


def foto_catalogo(produto):
    produto_id = produto.get("id")
    pasta = Path("static") / "fotos"

    if not produto_id:
        return None

    for extensao in (".webp", ".png", ".jpg", ".jpeg"):
        nomes = (
            f"dbsoftware_{produto_id}{extensao}",
            f"{produto_id}{extensao}",
        )

        for nome in nomes:
            arquivo = pasta / nome
            if arquivo.exists() and arquivo.stat().st_size > 1000:
                return f"/static/fotos/{nome}"

    return None



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
    # Prioriza fotos que ja foram sincronizadas para o computador.
    pasta_local = Path("static") / "fotos"
    for extensao in (".webp", ".png", ".jpg", ".jpeg"):
        for nome in (
            f"dbsoftware_{produto_id}{extensao}",
            f"{produto_id}{extensao}",
        ):
            local = pasta_local / nome
            if local.is_file() and local.stat().st_size > 1000:
                return f"/static/fotos/{nome}"

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
        return None

    capa = next(
        (foto for foto in geral if foto.get("is_capa") is True),
        geral[0]
    )
    urls = capa.get("urls") or {}
    foto_original = (
        urls.get("medium") or urls.get("full")
        or urls.get("thumb") or capa.get("url")
    )
    if not foto_original:
        return None

    pasta = Path("static") / "fotos"
    pasta.mkdir(parents=True, exist_ok=True)

    for extensao in (".webp", ".png", ".jpg", ".jpeg"):
        arquivo_existente = pasta / f"dbsoftware_{produto_id}{extensao}"
        if arquivo_existente.exists() and arquivo_existente.stat().st_size > 1000:
            return f"/static/fotos/{arquivo_existente.name}"

    arquivo = pasta / f"dbsoftware_{produto_id}.webp"

    alvo_id = None
    ws = None

    try:
        base = "http://127.0.0.1:9222"
        url_nova = base + "/json/new?" + urllib.parse.quote(
            foto_original, safe=":/?=&"
        )
        r = requests.put(url_nova, timeout=10)
        r.raise_for_status()
        aba = r.json()
        alvo_id = aba.get("id")

        ws = websocket.create_connection(
            aba["webSocketDebuggerUrl"],
            timeout=20,
            suppress_origin=True
        )

        proximo_id = 0

        def comando(metodo, parametros=None):
            nonlocal proximo_id
            proximo_id += 1
            numero = proximo_id
            ws.send(json.dumps({
                "id": numero,
                "method": metodo,
                "params": parametros or {}
            }))
            while True:
                mensagem = json.loads(ws.recv())
                if mensagem.get("id") == numero:
                    if "error" in mensagem:
                        raise RuntimeError(str(mensagem["error"]))
                    return mensagem.get("result", {})

        time.sleep(2)

        javascript = """
        fetch(location.href, {cache: "no-store"})
          .then(r => {
            if (!r.ok) throw new Error("HTTP " + r.status);
            return r.blob();
          })
          .then(blob => new Promise((resolve, reject) => {
            const leitor = new FileReader();
            leitor.onloadend = () => resolve(leitor.result.split(",")[1]);
            leitor.onerror = reject;
            leitor.readAsDataURL(blob);
          }))
        """

        resultado = comando(
            "Runtime.evaluate",
            {
                "expression": javascript,
                "awaitPromise": True,
                "returnByValue": True
            }
        )

        valor = resultado.get("result", {}).get("value")
        if not valor:
            detalhe = resultado.get("exceptionDetails", {})
            raise RuntimeError(
                "N?o foi poss?vel obter os dados da foto: " + str(detalhe)
            )

        imagem = base64.b64decode(valor)
        if len(imagem) < 1000:
            raise RuntimeError("Arquivo da foto muito pequeno.")

        arquivo.write_bytes(imagem)
        print(f"Foto original salva: {arquivo} ({len(imagem)} bytes)")
        return f"/static/fotos/{arquivo.name}"

    except Exception as e:
        print(f"Falha ao salvar foto local do produto {produto_id}: {e}")
        return foto_original

    finally:
        if ws:
            try:
                ws.close()
            except Exception:
                pass
        if alvo_id:
            try:
                requests.get(
                    f"http://127.0.0.1:9222/json/close/{alvo_id}",
                    timeout=3
                )
            except Exception:
                pass

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

        html {
            width: 100%;
            min-height: 100%;
            margin: 0;
            padding: 0;
            background: #f3f3f3;
        }

        body {
            font-family: Arial, sans-serif;
            background: #f3f3f3;
            width: 100%;
            min-height: 100vh;
            margin: 0;
            padding: 0;
            overflow-x: hidden;
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
           width: 100%;
           max-width: 100%;
           margin: 25px 0;
           padding: 20px;
           background: #f3f3f3;
        }

        .busca {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 0px;
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
    padding: 16px;
    margin-bottom: 0;
    border-radius: 10px;
    border: 1px solid #e5e5e5;
    border-left: 5px solid #ff6a00;
    min-width: 0;
    overflow: hidden;
}

.grade-produtos {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 16px;
    width: 100%;
}

.produto img {
    width: 100%;
    height: 180px;
    object-fit: cover;
}

@media (max-width: 1000px) {
    .grade-produtos {
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }
}

@media (max-width: 700px) {
    .grade-produtos {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
    }

    .produto {
        padding: 10px;
    }

    .produto img {
        height: 130px;
    }
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
                placeholder="Digite o nome ou codigo do produto..."
                autofocus
            >

            <button type="submit">
                 Buscar produto
            </button>

            
        </form>

               <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 10px; margin: 10px 0 20px;">

            <form method="POST" action="/atualizar-catalogo" style="margin: 0;">
                <button type="submit" class="botao">
                    🔄 Atualizar catálogo do DBSoftware
                </button>
            </form>

            <form method="POST" action="/atualizar-fotos" style="margin: 0;">
                <button type="submit" class="botao">
                    Atualizar fotos do DBSoftware
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

        <div class="grade-produtos">

        {% for produto in produtos %}

            <div class="produto">

                <div style="text-align:center; margin-bottom:-10px;">
                    <img
                       src="{{ foto_catalogo(produto) or produto.get('foto_url') or '' }}"
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
                    <strong>Codigo:</strong>
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
                    Criar promoção
                </a>

            </div>

        {% endfor %}

    </div>    

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
           
<img
    src="{{ foto_catalogo(produto) or produto.get('foto_url') or '' }}"
    alt="{{ produto.get('nome', 'Produto') }}"
    onerror="if (!this.dataset.tentouFotoAlternativa && this.dataset.fotoAlternativa) { this.dataset.tentouFotoAlternativa = '1'; this.src = this.dataset.fotoAlternativa; } else { this.style.display='none'; }"
    data-foto-alternativa="{{ produto.get('foto_url') or '' }}"
    style="width:100%; height:180px; object-fit:contain; border-radius:8px;">

        </div>
        {% endif %}

        <div class="linha">

            <div class="label">Codigo</div>

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

                    Pagamento á vista

                </label>

            </div>

            <div class="acoes">

                <button type="submit">
                    Gerar promoção
                </button>

                <a
                    class="botao voltar"
                    href="{{ url_for('inicio') }}"
                >
                    Voltar
                </a>

            </div>

        </form>

        {% if texto %}

    <div class="resultado">

        <h3>Texto da promoção</h3>

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
                    max-height:200px;
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
    Compartilhar promoção no WhatsApp
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

    if (!imagemProduto || !imagemProduto.complete || !imagemProduto.naturalWidth) {
        alert("A foto do produto ainda não carregou. Tente novamente.");
        return;
    }

    const canvas = document.getElementById("canvasPromocao");
    const ctx = canvas.getContext("2d");

    canvas.width = 1080;
    canvas.height = 1350;

    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, 1080, 1350);

    ctx.fillStyle = "#ff6a00";
    ctx.fillRect(0, 0, 1080, 150);

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

    
const areaX = 300;
const areaY = 310;
const areaLargura = 500;
const areaAltura = 600;

ctx.fillStyle = "#ffffff";
ctx.fillRect(areaX, areaY, areaLargura, areaAltura);

// Preenche a area da foto, cortando o excesso apenas na imagem gerada.
const proporcao = Math.max(
    areaLargura / imagemProduto.naturalWidth,
    areaAltura / imagemProduto.naturalHeight
);

const corteLargura = areaLargura / proporcao;
const corteAltura = areaAltura / proporcao;
const corteX = (imagemProduto.naturalWidth - corteLargura) / 2;
const corteY = (imagemProduto.naturalHeight - corteAltura) / 2;

ctx.drawImage(
    imagemProduto,
    corteX, corteY, corteLargura, corteAltura,
    areaX, areaY, areaLargura, areaAltura
);


    const precoNormal = document.querySelector(".preco-normal").innerText;
    const texto = document.querySelector(
        ".resultado div[style*='white-space']"
    ).innerText;

    const linhaPreco = texto
        .split("\\n")
        .find(linha => linha.trim().startsWith("POR R$"));

    const precoPromocional = linhaPreco
        ? linhaPreco.replace("POR R$", "").trim()
        : "";

    
    ctx.fillStyle = "#777777";
    ctx.font = "32px Arial";
    ctx.fillText("De " + precoNormal, 540, 965);

    ctx.fillStyle = "#ff6a00";
    ctx.font = "bold 58px Arial";
    ctx.fillText("POR R$ " + precoPromocional, 540, 1040);

    ctx.fillStyle = "#222222";
    ctx.font = "bold 30px Arial";
    ctx.fillText("Pagamento à vista", 540, 1090);

    ctx.fillStyle = "#25D366";
    ctx.fillRect(190, 1110, 700, 85);

    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 34px Arial";
    ctx.fillText("17 3462-3188", 540, 1165);

    ctx.fillStyle = "#222222";
    ctx.font = "26px Arial";
    ctx.fillText("Peça já pelo WhatsApp!", 540, 1260);

    canvas.toBlob(async function(blob) {
        if (!blob) {
            alert("Não foi possível gerar a imagem.");
            return;
        }

        const arquivo = new File(
            [blob],
            "promocao-castelao.png",
            { type: "image/png" }
        );

        if (
            navigator.share &&
            navigator.canShare &&
            navigator.canShare({ files: [arquivo] })
        ) {
            try {
                await navigator.share({
                    title: "Promoção Castelão Parafusos",
                    text: texto,
                    files: [arquivo]
                });
                return;
            } catch (erro) {
                if (erro.name === "AbortError") return;
            }
        }

        const urlImagem = URL.createObjectURL(blob);
        const linkDownload = document.createElement("a");
        linkDownload.download = "promocao-castelao.png";
        linkDownload.href = urlImagem;
        linkDownload.click();

        setTimeout(() => URL.revokeObjectURL(urlImagem), 5000);
        
        alert(
            "A imagem foi baixada. No WhatsApp, anexe o arquivo promocao-castelao.png para enviar a foto."
        );
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

            # Se for numero, procura pelo codigo em todas as paginas.
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
        erro=erro,
        foto_catalogo=foto_catalogo
    )

@app.route("/promocao/<int:produto_id>", methods=["GET", "POST"])
def criar_promocao(produto_id):

    erro = None
    texto = None
    whatsapp_url = None

    try:

        produto = buscar_produto(produto_id)

        if not produto:
            return "Produto não encontrado.", 404

        foto_url = buscar_foto_produto(produto_id)

        produto["foto_url"] = foto_url

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
                    "O preço promocional deve ser maior que zero."
                )

            if preco_promocional >= preco_atual:

                raise ValueError(
                    "O preço promocional deve ser menor que o preço atual."
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
                "OFERTA CASTELÃO PARAFUSOS\n\n"
                f"{nome}\n\n"
                f"Codigo: {codigo}\n"
                f"Marca: {marca}\n\n"
                f"De R$ {preco_atual:.2f}".replace(".", ",")
                + "\n"
                + f"POR R$ {preco_promocional:.2f}".replace(".", ",")
                + "\n\n"
                + f"{desconto:.0f}% DE DESCONTO"
                + "\n\n"
            )

            if avista:

                texto += "PAGAMENTO À VISTA\n\n"

            texto += (
                "Peça já pelo WhatsApp:\n"
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
        foto_catalogo=foto_catalogo,
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


