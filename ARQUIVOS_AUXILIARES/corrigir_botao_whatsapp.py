p="app.py"
s=open(p,"r",encoding="utf-8").read()

inicio=s.index('        if (\n            navigator.share')
fim=s.index('        }\n    }, "image/png");', inicio)+len('        }\n')

novo='''        const linkImagem = document.createElement("a");
        linkImagem.download = "promocao-castelao.png";
        linkImagem.href = URL.createObjectURL(blob);
        linkImagem.click();

        const urlWhatsApp =
            "https://wa.me/551734623188?text=" +
            encodeURIComponent(texto);

        window.open(urlWhatsApp, "_blank");

        setTimeout(() => {
            URL.revokeObjectURL(linkImagem.href);
        }, 5000);
'''

s=s[:inicio]+novo+s[fim:]

open(p,"w",encoding="utf-8").write(s)
print("ALTERAÇÃO CONCLUÍDA")
