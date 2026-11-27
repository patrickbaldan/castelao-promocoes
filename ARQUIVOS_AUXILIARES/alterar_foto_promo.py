p = "app.py"

with open(p, "r", encoding="utf-8") as f:
    s = f.read()

alvo = '''        <h2>{{ produto.get("nome", "") }}</h2>

        <div class="linha">
'''

novo = '''        <h2>{{ produto.get("nome", "") }}</h2>

        {% if foto_url %}
        <div style="text-align:center; margin:20px 0;">
            <img src="{{ foto_url }}" alt="produto" style="max-width:100%; max-height:300px; object-fit:contain; border-radius:10px;">
        </div>
        {% endif %}

        <div class="linha">
'''

if alvo not in s:
    print("TRECHO NÃO ENCONTRADO")
else:
    s = s.replace(alvo, novo, 1)
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)
    print("ALTERAÇÃO CONCLUÍDA")
