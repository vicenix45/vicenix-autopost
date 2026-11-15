"""Diagnostico do Instagram: testa varias chamadas de leitura (nao publica nada) e mostra qual falha."""
import os

import requests

from comum import ler_config

cfg = ler_config()
base = f"https://{cfg['instagram_host']}/{cfg['instagram_api']}"
tok = os.environ["IG_TOKEN"]
ig = cfg["instagram_user_id"]

testes = [
    ("quem e o token (me)", "me", {"fields": "id,name"}),
    ("permissoes do token", "me/permissions", {}),
    ("perfil do Instagram", ig, {"fields": "username,followers_count,media_count"}),
    ("ultimos posts", f"{ig}/media", {"fields": "id,timestamp,permalink", "limit": 3}),
    ("limite de publicacao", f"{ig}/content_publishing_limit", {"fields": "quota_usage,config"}),
]
for nome, caminho, params in testes:
    r = requests.get(f"{base}/{caminho}", params={**params, "access_token": tok}, timeout=30)
    print(f"[{'OK ' if r.ok else 'ERRO'}] {nome}: {r.text[:400]}")
