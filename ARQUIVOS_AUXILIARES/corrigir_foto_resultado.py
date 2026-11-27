from pathlib import Path

p = Path("app.py")
s = p.read_text(encoding="utf-8")

s = s.replace(
'''                {% if produto.get("id") and (("static/fotos/" ~ produto.get("id") ~ ".png") | file_exists) %}
                <div style="text-align:center; margin-bottom:12px;">
                    <img
                        src="{{ url_for("static", filename="fotos/" ~ produto.get("id") ~ ".png") }}"
                        alt="produto"
                        style="max-width:100%; max-height:180px; object-fit:contain; border-radius:8px;"
                    >
                </div>
                {% endif %}''',
'''                <div style="text-align:center; margin-bottom:12px;">
                    <img
                        src="{{ url_for("static", filename="fotos/" ~ produto.get("id") ~ ".png") }}"
                        alt="produto"
                        onerror="this.style.display='none';"
                        style="max-width:100%; max-height:180px; object-fit:contain; border-radius:8px;"
                    >
                </div>''',
1
)

p.write_text(s, encoding="utf-8")

print("CORREÇÃO CONCLUÍDA")
