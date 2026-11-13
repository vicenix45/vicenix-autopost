"""Roda no GitHub Actions toda semana: renova o token do Instagram e grava no segredo IG_TOKEN."""
import os
import subprocess
import sys

import requests

antigo = os.environ.get("IG_TOKEN", "")
if not antigo:
    sys.exit("Segredo IG_TOKEN vazio. Rode 'CONECTAR INSTAGRAM.bat' no PC.")
if not os.environ.get("GH_TOKEN"):
    sys.exit("Segredo GH_PAT vazio. Veja o passo 4 do COMO CONFIGURAR.md.")

r = requests.get(
    "https://graph.instagram.com/refresh_access_token",
    params={"grant_type": "ig_refresh_token", "access_token": antigo},
    timeout=60,
)
if not r.ok:
    sys.exit(f"Instagram nao renovou o token: {r.status_code} {r.text[:300]}\n"
             "Se ele ja venceu, gere um novo e rode 'CONECTAR INSTAGRAM.bat'.")
novo = r.json()["access_token"]
print(f"::add-mask::{novo}")
subprocess.run(["gh", "secret", "set", "IG_TOKEN", "--repo", os.environ["REPO"]],
               input=novo, text=True, check=True)
dias = int(r.json().get("expires_in", 0)) // 86400
print(f"Token renovado. Vale por mais {dias} dias.")
