"""Roda no GitHub Actions: publica os itens da fila que ja chegaram no horario.

    python postar.py           publica de verdade
    python postar.py --teste   so mostra o que faria (nao chama API nenhuma)

Segredos (variaveis de ambiente): IG_TOKEN, YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN.
"""
import datetime as dt
import os
import subprocess
import sys
import tempfile
import time

import requests

from comum import agora, ler_config, ler_fila, quando, salvar_fila, url_video

TESTE = "--teste" in sys.argv


def log(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------- Instagram

def ig_get(cfg, caminho, **params):
    params["access_token"] = os.environ["IG_TOKEN"]
    r = requests.get(f"https://graph.instagram.com/{cfg['instagram_api']}/{caminho}", params=params, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Instagram GET {caminho}: {r.status_code} {r.text[:400]}")
    return r.json()


def ig_post(cfg, caminho, **dados):
    dados["access_token"] = os.environ["IG_TOKEN"]
    r = requests.post(f"https://graph.instagram.com/{cfg['instagram_api']}/{caminho}", data=dados, timeout=120)
    if not r.ok:
        raise RuntimeError(f"Instagram POST {caminho}: {r.status_code} {r.text[:400]}")
    return r.json()


def url_final(url):
    """O link do GitHub redireciona pro servidor de arquivos; devolve o endereco final."""
    r = requests.head(url, allow_redirects=True, timeout=60)
    r.raise_for_status()
    return r.url


def ig_container(cfg, user_id, item, video):
    c = ig_post(cfg, f"{user_id}/media", media_type="REELS", video_url=video,
                caption=item["instagram"]["legenda"], share_to_feed="true")
    cid = c["id"]
    for _ in range(40):  # ate ~10 min
        time.sleep(15)
        st = ig_get(cfg, cid, fields="status_code,status")
        codigo = st.get("status_code")
        log(f"    instagram: processando ({codigo})")
        if codigo == "FINISHED":
            return cid
        if codigo in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram recusou o video: {st.get('status')}")
    raise RuntimeError("Instagram demorou mais de 10 min processando o video")


def postar_instagram(cfg, item, _arquivo_local):
    user_id = ig_get(cfg, "me", fields="user_id,username")["user_id"]
    link = url_video(cfg, item)
    try:
        cid = ig_container(cfg, user_id, item, link)
    except RuntimeError as e:
        log(f"    instagram: falhou com o link do GitHub ({e}); tentando o link direto")
        cid = ig_container(cfg, user_id, item, url_final(link))
    pub = ig_post(cfg, f"{user_id}/media_publish", creation_id=cid)
    mid = pub["id"]
    try:
        permalink = ig_get(cfg, mid, fields="permalink").get("permalink", "")
    except RuntimeError:
        permalink = ""
    return {"id": mid, "url": permalink}


# ---------------------------------------------------------------- YouTube

def postar_youtube(cfg, item, arquivo_local):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    cred = Credentials(
        None,
        refresh_token=os.environ["YT_REFRESH_TOKEN"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["YT_CLIENT_ID"],
        client_secret=os.environ["YT_CLIENT_SECRET"],
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    yt = build("youtube", "v3", credentials=cred, cache_discovery=False)
    y = item["youtube"]
    corpo = {
        "snippet": {
            "title": y["titulo"][:100].replace("<", "").replace(">", ""),
            "description": y["descricao"][:5000],
            "tags": y.get("tags", [])[:30],
            "categoryId": cfg.get("youtube_categoria", "20"),
            "defaultLanguage": "pt-BR",
            "defaultAudioLanguage": "pt-BR",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": bool(item.get("ia")),
        },
    }
    media = MediaFileUpload(arquivo_local, mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=corpo, media_body=media)
    resp = None
    while resp is None:
        progresso, resp = req.next_chunk()
        if progresso:
            log(f"    youtube: enviando {int(progresso.progress() * 100)}%")
    vid = resp["id"]
    privacidade = resp.get("status", {}).get("privacyStatus")
    return {"id": vid, "url": f"https://youtube.com/shorts/{vid}", "privacidade": privacidade}


POSTADORES = {"instagram": postar_instagram, "youtube": postar_youtube}
PRECISA_ARQUIVO = {"youtube"}


# ---------------------------------------------------------------- fila

def pendentes(cfg, item):
    ativas = [p for p, on in cfg["plataformas"].items() if on]
    saida = []
    for p in ativas:
        st = item.setdefault("status", {}).get(p, {})
        if st.get("ok") or st.get("pulado"):
            continue
        if st.get("tentativas", 0) >= cfg.get("max_tentativas", 3):
            continue
        saida.append(p)
    return saida


def baixar(cfg, item):
    destino = os.path.join(tempfile.gettempdir(), item["arquivo"])
    with requests.get(url_video(cfg, item), stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(destino, "wb") as f:
            for bloco in r.iter_content(1024 * 1024):
                f.write(bloco)
    return destino


def apagar_video(cfg, item):
    if TESTE or not cfg.get("apagar_video_depois"):
        return
    subprocess.run(["gh", "release", "delete-asset", cfg["release_fila"], item["arquivo"], "-y",
                    "--repo", cfg["repo"]], check=False)


def main():
    cfg = ler_config()
    fila = ler_fila()
    hoje = agora(cfg)
    tolerancia = dt.timedelta(minutes=10)
    atraso_max = dt.timedelta(hours=cfg.get("atraso_maximo_horas", 24))

    na_hora = [i for i in fila if quando(i) <= hoje + tolerancia and pendentes(cfg, i)]
    log(f"Agora: {hoje:%d/%m %H:%M}. Na fila: {len(fila)}. Prontos pra postar: {len(na_hora)}.")

    feitos = 0
    mudou = False
    houve_erro = False
    for item in sorted(na_hora, key=quando):
        if feitos >= cfg.get("max_por_execucao", 1):
            log("Limite por execucao atingido; o resto vai na proxima.")
            break
        if hoje - quando(item) > atraso_max:
            log(f"- {item['id']}: atrasado demais, pulando (mude o 'quando' na fila.json pra reagendar)")
            for p in pendentes(cfg, item):
                item["status"][p] = {"pulado": "atrasado"}
            mudou = True
            continue

        plats = pendentes(cfg, item)
        log(f"- {item['id']} ({item['titulo']}) -> {', '.join(plats)}")
        if TESTE:
            for p in plats:
                log(f"    [teste] postaria no {p}")
            feitos += 1
            continue

        local = baixar(cfg, item) if PRECISA_ARQUIVO & set(plats) else None
        for p in plats:
            st = item["status"].get(p, {})
            try:
                res = POSTADORES[p](cfg, item, local)
                item["status"][p] = {"ok": True, "em": agora(cfg).isoformat(timespec="minutes"), **res}
                log(f"    {p}: POSTADO {res.get('url', '')}")
            except Exception as e:  # noqa: BLE001 - qualquer erro vira tentativa registrada
                item["status"][p] = {"tentativas": st.get("tentativas", 0) + 1, "erro": str(e)[:500]}
                log(f"    {p}: ERRO {e}")
                houve_erro = True
            mudou = True
        if not pendentes(cfg, item) and all(item["status"].get(p, {}).get("ok")
                                             for p, on in cfg["plataformas"].items() if on):
            apagar_video(cfg, item)
        feitos += 1

    if mudou and not TESTE:
        salvar_fila(fila)
    erros = [i["id"] for i in fila for p, s in i.get("status", {}).items()
             if s.get("erro") and s.get("tentativas", 0) >= cfg.get("max_tentativas", 3)]
    if erros:
        log(f"ATENCAO: desistiu depois de {cfg.get('max_tentativas', 3)} tentativas em: {', '.join(erros)}")
    if houve_erro:
        sys.exit(1)  # deixa a execucao vermelha no GitHub (e o GitHub manda e-mail avisando)


if __name__ == "__main__":
    main()
