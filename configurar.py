"""Passo 1: entra no GitHub, cria o repositorio e a 'fila' de videos. Pode rodar de novo sem problema."""
import json
import subprocess
import sys

from comum import RAIZ, ler_config, salvar_config
from local import gh, gh_exe, git

NOME_PADRAO = "vicenix-autopost"


def main():
    gh_exe()
    if subprocess.run([gh_exe(), "auth", "status"], capture_output=True).returncode != 0:
        print("\nVai abrir o navegador pra voce entrar na sua conta do GitHub.")
        print("Escolha: GitHub.com -> HTTPS -> Yes -> Login with a web browser.\n")
        subprocess.run([gh_exe(), "auth", "login", "--web", "--git-protocol", "https",
                        "--scopes", "repo,workflow"], check=True)
    gh("auth", "setup-git")

    eu = json.loads(gh("api", "user"))
    login = eu["login"]
    print(f"Conectado no GitHub como: {login}")

    cfg = ler_config()
    if not (RAIZ / ".git").exists():
        git("init", "-b", "main")
    # commits saem com e-mail anonimo do GitHub, nao o seu e-mail pessoal
    git("config", "user.name", login)
    git("config", "user.email", f"{eu['id']}+{login}@users.noreply.github.com")

    if not cfg.get("repo"):
        nome = input(f"Nome do repositorio [{NOME_PADRAO}]: ").strip() or NOME_PADRAO
        cfg["repo"] = f"{login}/{nome}"
        salvar_config(cfg)
        if not (RAIZ / "fila.json").exists():
            (RAIZ / "fila.json").write_text("[]\n", encoding="utf-8")
        git("add", "-A")
        git("commit", "-m", "robo de postagem")
        # publico: o Instagram so aceita o video num link aberto, e Actions e ilimitado em repo publico
        gh("repo", "create", nome, "--public", "--source", ".", "--remote", "origin", "--push",
           "--description", "Postagem automatica")
        print(f"Repositorio criado: https://github.com/{cfg['repo']}")
    else:
        git("add", "-A")
        if git("status", "--porcelain"):
            git("commit", "-m", "atualiza robo")
        git("push", "-u", "origin", "main")
        print(f"Repositorio ja existia: https://github.com/{cfg['repo']}")

    lista = gh("release", "list", "--repo", cfg["repo"], "--json", "tagName")
    if cfg["release_fila"] not in lista:
        gh("release", "create", cfg["release_fila"], "--repo", cfg["repo"], "--title", "Fila de videos",
           "--notes", "Videos esperando a hora de postar. O robo apaga cada um depois de postado.")
        print("Fila de videos criada.")

    print("\nPronto. Proximo passo: '2 - CONECTAR INSTAGRAM.bat' (veja COMO CONFIGURAR.md).")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        sys.exit(f"Falhou: {e}")
