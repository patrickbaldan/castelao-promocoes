p="app.py"
s=open(p,"r",encoding="utf-8").read()
ant='''    const precoPromocional = document.querySelector(
        "input[name='preco_promocional']"
    ).value;'''
novo='''    const textoPromocao = document.querySelector(
        "#previewPromocao div[style*='white-space']"
    ).innerText;

    const linhaPreco = textoPromocao
        .split("\\n")
        .find(linha => linha.trim().startsWith("POR R$"));

    const precoPromocional = linhaPreco
        ? linhaPreco.replace("POR R$", "").trim()
        : "";'''
if ant not in s:
    raise SystemExit("BLOCO NÃO ENCONTRADO")
s=s.replace(ant,novo,1)
open(p,"w",encoding="utf-8").write(s)
print("ALTERAÇÃO CONCLUÍDA")
