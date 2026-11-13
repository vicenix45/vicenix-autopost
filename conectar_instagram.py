"""Passo 2: cola o token do Instagram e grava no GitHub.

Aceita os dois tipos:
  IGAA...  token do "login do Instagram" (vence em 60 dias, o robo renova)
  EAA...   token de usuario do sistema do portfolio empresarial / login unificado (nao vence)
"""
import getpass
import sys

import requests

from comum import ler_config, salvar_config
from local import gh, git, gravar_segredo, repo_ou_sair


def get(host, versao, caminho, token, **params):
    params["access_token"] = token
    r = requests.get(f"https://{host}/{versao}/{caminho}", params=params, timeout=30)
    return r.json() if r.ok else None


def conta_instagram_login(cfg, token):
    conta = get("graph.instagram.com", cfg["instagram_api"], "me", token, fields="user_id,username,account_type")
    if not conta:
        return None
    r = requests.get("https://graph.instagram.com/refresh_access_token",
                     params={"grant_type": "ig_refresh_token", "access_token": token}, timeout=30)
    if r.ok:  # troca token curto por um de 60 dias
        token = r.json()["access_token"]
    return {"host": "graph.instagram.com", "user_id": "", "username": conta.get("username", ""), "token": token}


def conta_facebook_login(cfg, token):
    v = cfg["instagram_api"]
    if not get("graph.facebook.com", v, "me", token, fields="id"):
        return None
    achados = {}
    for biz in (get("graph.facebook.com", v, "me/businesses", token, fields="id,name") or {}).get("data", []):
        for aresta in ("owned_instagram_accounts", "instagram_accounts"):
            for c in (get("graph.facebook.com", v, f"{biz['id']}/{aresta}", token, fields="id,username") or {}).get("data", []):
                achados[c["id"]] = c.get("username", "")
    for pg in (get("graph.facebook.com", v, "me/accounts", token,
                   fields="instagram_business_account{id,username}") or {}).get("data", []):
        c = pg.get("instagram_business_account")
        if c:
            achados[c["id"]] = c.get("username", "")

    esperado = (cfg.get("instagram_conta") or "").lower()
    user_id = next((i for i, u in achados.items() if u.lower() == esperado), None)
    if not user_id and len(achados) == 1:
        user_id = next(iter(achados))
    if not user_id:
        if achados:
            print("Contas encontradas: " + ", ".join(f"@{u} ({i})" for i, u in achados.items()))
        print("Nao achei sozinho o numero da conta do Instagram.")
        print("Pegue em business.facebook.com/settings -> Contas -> Contas do Instagram -> vicenix45 (campo 'Identificacao').")
        user_id = input("Numero da conta do Instagram: ").strip()
    conta = get("graph.facebook.com", v, user_id, token, fields="id,username")
    if not conta:
        sys.exit("Esse token nao tem acesso a essa conta do Instagram. Confira as permissoes do usuario do sistema.")
    return {"host": "graph.facebook.com", "user_id": conta["id"], "username": conta.get("username", ""), "token": token}


def main():
    cfg = repo_ou_sair()
    print("Cole o token do Instagram e aperte Enter (ele NAO aparece na tela enquanto cola):")
    token = getpass.getpass("> ").strip()
    if not token:
        sys.exit("Nenhum token colado.")

    conta = conta_instagram_login(cfg, token) or conta_facebook_login(cfg, token)
    if not conta:
        sys.exit("Nem o Instagram nem o Facebook aceitaram esse token. Gere de novo e confira se copiou inteiro.")
    print(f"Token valido. Conta: @{conta['username']}")
    esperado = cfg.get("instagram_conta")
    if esperado and conta["username"].lower() != esperado.lower():
        if input(f"Atencao: esperava @{esperado}. Usar mesmo assim? (s/n) ").strip().lower() != "s":
            sys.exit("Cancelado.")

    gravar_segredo("IG_TOKEN", conta["token"])

    cfg = ler_config()
    if cfg.get("instagram_host") != conta["host"] or cfg.get("instagram_user_id", "") != conta["user_id"]:
        cfg["instagram_host"], cfg["instagram_user_id"] = conta["host"], conta["user_id"]
        salvar_config(cfg)
        git("pull", "--rebase", "--autostash", checar=False)
        git("add", "config.json")
        git("commit", "-m", "instagram conectado")
        git("push")
        print("  configuracao enviada pro GitHub.")

    if conta["host"] == "graph.instagram.com" and "GH_PAT" not in gh("secret", "list", "--repo", cfg["repo"]):
        print("\nAgora o token do GitHub que deixa o robo renovar o do Instagram sozinho (veja o guia).")
        print("Cole e aperte Enter (ou so Enter pra fazer depois):")
        pat = getpass.getpass("> ").strip()
        if pat:
            gravar_segredo("GH_PAT", pat)
        else:
            print("  pulado: sem ele, o token do Instagram vence em 60 dias.")
    print("\nInstagram conectado. Proximo: '4 - ENVIAR VIDEOS PRA FILA.bat'.")


if __name__ == "__main__":
    main()
