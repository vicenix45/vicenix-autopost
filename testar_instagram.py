"""Teste SEGURO do Instagram: cria o container do proximo Reels da fila e espera a Meta processar,
mas NAO publica. Prova que o token, a conta e o link do video funcionam.
Roda no GitHub Actions pelo workflow "Testar Instagram".
"""
from comum import agora, ler_config, ler_fila, quando, url_video
from postar import ig_container, ig_get, log, url_final


def main():
    cfg = ler_config()
    user_id = cfg.get("instagram_user_id") or ig_get(cfg, "me", fields="user_id")["user_id"]
    conta = ig_get(cfg, user_id, fields="username")
    log(f"Conta: @{conta.get('username')} ({user_id})")
    fila = ler_fila()
    hoje = agora(cfg)
    item = next((i for i in sorted(fila, key=quando) if quando(i) >= hoje), None) or fila[-1]
    log(f"Video de teste: {item['titulo']}")
    link = url_video(cfg, item)
    try:
        cid = ig_container(cfg, user_id, item, link)
    except RuntimeError as e:
        log(f"Link do GitHub falhou ({e}); tentando o link direto")
        cid = ig_container(cfg, user_id, item, url_final(link))
    log(f"OK: a Meta baixou e processou o video (container {cid}). NADA foi publicado.")


if __name__ == "__main__":
    main()
