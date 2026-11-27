from pathlib import Path

p = Path("app.py")
s = p.read_text(encoding="utf-8")

alvo = "import urllib.parse"
novas = """import urllib.parse
import base64
import json
import time
import websocket"""

if "import base64" not in s:
    s = s.replace(alvo, novas, 1)

p.write_text(s, encoding="utf-8")
print("IMPORTS ADICIONADOS")
