from pathlib import Path

p = Path("app.py")
s = p.read_text(encoding="utf-8")

alvo = '''        <br><br>

        <a
            class="botao"
            href="{{ whatsapp_url }}"
            target="_blank"
        >
            Abrir WhatsApp somente com texto
        </a>'''

if alvo not in s:
    raise SystemExit("BOTÃO DE TEXTO NÃO ENCONTRADO")

s = s.replace(alvo, "", 1)

p.write_text(s, encoding="utf-8")

print("BOTÃO EXTRA REMOVIDO")
