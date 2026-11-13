"""Teste real do envio pro YouTube (usado no video da auditoria do Google).

Pega o proximo video da fila e envia pro canal como PRIVADO, com "[teste]" no titulo.
Nao mexe na fila: o item continua esperando o horario normal.
Roda no GitHub Actions pelo workflow "Testar YouTube" (botao Run workflow).
"""
import copy

from comum import agora, ler_config, ler_fila, quando
from postar import baixar, log, postar_youtube


def main():
    cfg = ler_config()
    fila = ler_fila()
    if not fila:
        raise SystemExit("Fila vazia: rode o '4 - ENVIAR VIDEOS PRA FILA.bat' antes.")
    hoje = agora(cfg)
    item = next((i for i in sorted(fila, key=quando) if quando(i) >= hoje), fila[0])
    teste = copy.deepcopy(item)
    teste["youtube"]["titulo"] = "[teste] " + item["youtube"]["titulo"]
    log(f"Enviando como PRIVADO: {teste['youtube']['titulo']}")
    local = baixar(cfg, item)
    res = postar_youtube(cfg, teste, local, privacidade="private")
    log(f"ENVIADO. Privacidade: {res['privacidade']}")
    log(f"Link: https://studio.youtube.com/video/{res['id']}/edit")


if __name__ == "__main__":
    main()
