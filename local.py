"""Ajudantes dos scripts que rodam no PC (Windows): achar o gh, rodar comandos, gravar segredos."""
import os
import shutil
import subprocess
import sys

from comum import RAIZ, ler_config

CAMINHOS_GH = [
    r"C:\Program Files\GitHub CLI\gh.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\GitHub CLI\gh.exe"),
]


def gh_exe():
    achado = shutil.which("gh")
    if achado:
        return achado
    for c in CAMINHOS_GH:
        if os.path.exists(c):
            return c
    sys.exit("O GitHub CLI (gh) nao esta instalado. Rode primeiro '1 - CONFIGURAR.bat'.")


def gh(*args, entrada=None, capturar=True, checar=True):
    r = subprocess.run([gh_exe(), *args], input=entrada, text=True, cwd=RAIZ,
                       capture_output=capturar, encoding="utf-8")
    if checar and r.returncode != 0:
        sys.exit(f"Erro no gh {' '.join(args[:3])}: {(r.stderr or r.stdout or '').strip()}")
    return (r.stdout or "").strip()


def git(*args, checar=True):
    r = subprocess.run(["git", *args], text=True, cwd=RAIZ, capture_output=True, encoding="utf-8")
    if checar and r.returncode != 0:
        sys.exit(f"Erro no git {' '.join(args[:2])}: {(r.stderr or r.stdout).strip()}")
    return r.stdout.strip()


def gravar_segredo(nome, valor):
    """Grava o segredo direto no GitHub (criptografado). O valor nunca aparece na tela."""
    cfg = ler_config()
    gh("secret", "set", nome, "--repo", cfg["repo"], entrada=valor)
    print(f"  segredo {nome} gravado no GitHub.")


def repo_ou_sair():
    cfg = ler_config()
    if not cfg.get("repo"):
        sys.exit("Repositorio ainda nao criado. Rode primeiro '1 - CONFIGURAR.bat'.")
    return cfg
