"""Passo 3: autoriza o robo a subir videos no seu canal do YouTube (uma vez so)."""
import json
import sys

from comum import RAIZ
from local import gravar_segredo, repo_ou_sair

ESCOPOS = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    repo_ou_sair()
    segredo = RAIZ / "client_secret.json"
    if not segredo.exists():
        candidatos = sorted(RAIZ.glob("client_secret*.json"))
        if not candidatos:
            sys.exit("Nao achei o client_secret.json nesta pasta. Veja o passo 3 do COMO CONFIGURAR.md.")
        segredo = candidatos[0]

    from google_auth_oauthlib.flow import InstalledAppFlow

    print("Vai abrir o navegador. Entre na conta Google DONA do canal e escolha o canal vicenix.")
    print("Se aparecer 'O Google nao verificou este app': Avancado -> Acessar (e seu proprio app).\n")
    flow = InstalledAppFlow.from_client_secrets_file(str(segredo), ESCOPOS)
    cred = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    if not cred.refresh_token:
        sys.exit("O Google nao devolveu o refresh token. Rode de novo.")

    info = json.loads(segredo.read_text(encoding="utf-8"))
    info = info.get("installed") or info.get("web")
    gravar_segredo("YT_CLIENT_ID", info["client_id"])
    gravar_segredo("YT_CLIENT_SECRET", info["client_secret"])
    gravar_segredo("YT_REFRESH_TOKEN", cred.refresh_token)
    print("\nYouTube conectado.")
    print("Pra ligar: em config.json troque \"youtube\": false por true e rode '1 - CONFIGURAR.bat' pra subir.")
    print("Enquanto a auditoria do Google nao for aprovada, os videos sobem TRAVADOS como privados.")


if __name__ == "__main__":
    main()
