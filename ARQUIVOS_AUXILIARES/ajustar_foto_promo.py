from pathlib import Path

p = Path("app.py")
s = p.read_text(encoding="utf-8")

antigo = """const areaX = 100;
const areaY = 270;
const areaLargura = 880;
const areaAltura = 500;

const proporcao = Math.min(
    areaLargura / imagemProduto.naturalWidth,
    areaAltura / imagemProduto.naturalHeight
);

const largura = imagemProduto.naturalWidth * proporcao;
const altura = imagemProduto.naturalHeight * proporcao;

ctx.fillStyle = "#ffffff";
ctx.fillRect(areaX, areaY, areaLargura, areaAltura);

ctx.drawImage(
    imagemProduto,
    areaX + (areaLargura - largura) / 2,
    areaY + (areaAltura - altura) / 2,
    largura,
    altura
);"""

novo = """const areaX = 100;
const areaY = 270;
const areaLargura = 880;
const areaAltura = 500;

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
);"""

if antigo not in s:
    print("NAO ALTERADO: trecho original nao encontrado. Preserve o arquivo.")
else:
    p.write_text(s.replace(antigo, novo, 1), encoding="utf-8")
    print("ALTERACAO FEITA: area da foto ajustada.")
