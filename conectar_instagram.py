"""Passo 2: cola o token do Instagram (gerado no painel da Meta) e grava no GitHub."""
import getpass
import sys

import requests

from local import gh, gravar_segredo, repo_ou_sair


def main():
    cfg = repo_ou_sair()
    print("Cole o token do Instagram e aperte Enter (ele NAO aparece na tela enquanto cola):")
    token = getpass.getpass("> ").strip()
    if not token:
        sys.exit("Nenhum token colado.")

    r = requests.get(f"https://graph.instagram.com/{cfg['instagram_api']}/me",
                     params={"fields": "user_id,username,account_type", "access_token": token}, timeout=30)
    if not r.ok:
        sys.exit(f"O Instagram nao aceitou esse token: {r.text[:300]}")
    conta = r.json()
    print(f"Token valido. Conta: @{conta.get('username')} ({conta.get('account_type', '?')})")
    esperado = cfg.get("instagram_conta")
    if esperado and conta.get("username", "").lower() != esperado.lower():
        if input(f"Atencao: esperava @{esperado}. Usar mesmo assim? (s/n) ").strip().lower() != "s":
            sys.exit("Cancelado.")

    # troca por token de 60 dias se for um token curto (se ja for longo, o Instagram so devolve erro e seguimos)
    r = requests.get("https://graph.instagram.com/refresh_access_token",
                     params={"grant_type": "ig_refresh_token", "access_token": token}, timeout=30)
    if r.ok:
        token = r.json()["access_token"]

    gravar_segredo("IG_TOKEN", token)

    if "GH_PAT" not in gh("secret", "list", "--repo", cfg["repo"]):
        print("\nAgora o token do GitHub que deixa o robo renovar o do Instagram sozinho (passo 2.6 do guia).")
        print("Cole e aperte Enter (ou so Enter pra fazer depois):")
        pat = getpass.getpass("> ").strip()
        if pat:
            gravar_segredo("GH_PAT", pat)
        else:
            print("  pulado: sem ele, o token do Instagram vence em 60 dias.")
    print("\nInstagram conectado. Proximo: '4 - ENVIAR VIDEOS PRA FILA.bat'.")


if __name__ == "__main__":
    main()
