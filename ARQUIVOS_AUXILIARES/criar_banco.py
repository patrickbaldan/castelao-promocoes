import sqlite3

BANCO = "promocoes.db"

conn = sqlite3.connect(BANCO)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY,
    codigo_externo TEXT,
    nome TEXT,
    marca TEXT,
    preco_custo REAL,
    preco_venda REAL,
    estoque REAL,
    foto_url TEXT,
    foto_local TEXT,
    atualizado_em TEXT
)
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_produtos_nome
ON produtos(nome)
""")

conn.commit()
conn.close()

print("BANCO CRIADO COM SUCESSO")
print("Arquivo:", BANCO)