"""Le a pasta PRONTOS PARA POSTAR (uma pasta por dia, "12h - Video NN - x.mp4" + " - LEGENDA.txt"),
sobe os videos novos pra fila do GitHub e agenda cada um.

    python enfileirar.py            envia os videos novos (so os de horarios que ainda nao passaram)
    python enfileirar.py --teste    so mostra o que leu, nao envia nada
    python enfileirar.py --ver      mostra a fila e o que ja foi postado
    python enfileirar.py --incluir-passados   envia tambem horarios que ja passaram (posta na hora)
"""
import datetime as dt
import pathlib
import re
import shutil
import sys
import unicodedata

from comum import RAIZ, agora, fuso, ler_config, ler_fila, quando, salvar_fila

RE_DIA = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
RE_VIDEO = re.compile(r"^(\d{1,2})h(\d{2})?\s*-\s*(.+)\.mp4$", re.I)
RE_NUM = re.compile(r"video\s*(\d+)", re.I)
REDES = {"youtube shorts": "youtube", "youtube": "youtube", "tiktok": "tiktok",
         "reels": "instagram", "instagram": "instagram", "kwai": "kwai"}


def slug(txt):
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", txt.lower()).strip("-")[:50]


def ler_legenda(arquivo):
    """'Rede: texto' seguido da linha de hashtags -> {rede: (texto, hashtags)}"""
    saida, atual = {}, None
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        m = re.match(r"^([A-Za-z ]+):\s*(.+)$", linha)
        if m and m.group(1).strip().lower() in REDES:
            atual = REDES[m.group(1).strip().lower()]
            saida[atual] = [m.group(2).strip(), ""]
        elif atual and linha.startswith("#"):
            saida[atual][1] = linha
            atual = None
    return saida


def montar_item(cfg, pasta_dia, video):
    d = RE_DIA.match(pasta_dia.name)
    m = RE_VIDEO.match(video.name)
    hora, minuto, titulo = int(m.group(1)), int(m.group(2) or 0), m.group(3).strip()
    data = dt.datetime(int(d.group(1)), int(d.group(2)), int(d.group(3)), hora, minuto, tzinfo=fuso(cfg))

    leg_arq = video.with_name(video.stem + " - LEGENDA.txt")
    if not leg_arq.exists():
        print(f"  ! sem legenda, pulando: {video.name}")
        return None
    leg = ler_legenda(leg_arq)
    if "instagram" not in leg or "youtube" not in leg:
        print(f"  ! legenda sem 'Reels:' ou 'YouTube Shorts:', pulando: {leg_arq.name}")
        return None

    yt_txt, yt_tags = leg["youtube"]
    ig_txt, ig_tags = leg["instagram"]
    num = RE_NUM.search(titulo)
    narrado_ia = bool(num) and (RAIZ / cfg["pasta_narracoes"] / f"v{int(num.group(1)):02d}.txt").exists()

    iid = f"{data:%Y-%m-%d_%Hh%M}"
    item = {
        "id": iid,
        "quando": data.isoformat(timespec="minutes"),
        "titulo": titulo,
        "arquivo": f"{iid}-{slug(titulo)}.mp4",
        "ia": narrado_ia,
        "instagram": {"legenda": f"{ig_txt}\n\n{ig_tags}".strip()},
        "youtube": {
            "titulo": yt_txt,
            "descricao": f"{yt_txt}\n\n{yt_tags}".strip(),
            "tags": [t.lstrip("#") for t in yt_tags.split() if t.startswith("#")],
        },
        "status": {},
    }
    if "tiktok" in leg:
        item["tiktok"] = {"legenda": f"{leg['tiktok'][0]}\n\n{leg['tiktok'][1]}".strip()}
    return item, video


def ler_pasta(cfg):
    base = pathlib.Path(cfg["pasta_postar"])
    if not base.exists():
        sys.exit(f"Pasta nao encontrada: {base}")
    achados = []
    for pasta in sorted(p for p in base.iterdir() if p.is_dir() and RE_DIA.match(p.name)):
        for video in sorted(pasta.glob("*.mp4")):
            if RE_VIDEO.match(video.name):
                r = montar_item(cfg, pasta, video)
                if r:
                    achados.append(r)
    return achados


def ver(cfg):
    fila = ler_fila()
    if not fila:
        print("Fila vazia.")
    for i in fila:
        partes = []
        for p, on in cfg["plataformas"].items():
            if not on:
                continue
            s = i.get("status", {}).get(p, {})
            partes.append(f"{p}: " + ("OK" if s.get("ok") else "pulado" if s.get("pulado")
                                      else f"ERRO x{s['tentativas']}" if s.get("erro") else "esperando"))
        print(f"{quando(i):%d/%m %H:%M}  {i['titulo'][:45]:45}  {' | '.join(partes)}")


def main():
    from local import gh, git, repo_ou_sair

    cfg = ler_config()
    if "--ver" in sys.argv:
        if cfg.get("repo"):
            git("pull", "--rebase", "--autostash", checar=False)
        ver(cfg)
        return
    teste = "--teste" in sys.argv
    passados = "--incluir-passados" in sys.argv

    if not teste:
        cfg = repo_ou_sair()
        git("pull", "--rebase", "--autostash", checar=False)  # pega o status que o robo gravou
    fila = ler_fila()
    ja = {i["id"] for i in fila}
    hoje = agora(cfg)

    novos = []
    for item, video in ler_pasta(cfg):
        if item["id"] in ja:
            continue
        if quando(item) < hoje and not passados:
            print(f"  - {item['id']} ja passou do horario, pulando ({item['titulo']})")
            continue
        novos.append((item, video))

    if not novos:
        print("Nada novo pra enviar.")
        return
    print(f"\n{len(novos)} video(s) novo(s):")
    for item, video in novos:
        ia = "  [voz IA]" if item["ia"] else ""
        print(f"  {quando(item):%d/%m %H:%M}  {item['titulo']}{ia}")
        if teste:
            print(f"      YT: {item['youtube']['titulo']}  |  tags: {len(item['youtube']['tags'])}")
            print(f"      IG: {item['instagram']['legenda'].splitlines()[0]}")
    if teste:
        print("\n(teste: nada foi enviado)")
        return

    envio = RAIZ / ".envio"
    envio.mkdir(exist_ok=True)
    for item, video in novos:
        copia = envio / item["arquivo"]
        shutil.copy2(video, copia)
        print(f"  enviando {item['arquivo']} ...")
        gh("release", "upload", cfg["release_fila"], str(copia), "--clobber", "--repo", cfg["repo"])
        copia.unlink()
        fila.append(item)
        salvar_fila(fila)
    shutil.rmtree(envio, ignore_errors=True)

    git("add", "fila.json")
    git("commit", "-m", f"fila: +{len(novos)} video(s)")
    git("push")
    print(f"\nPronto: {len(novos)} video(s) agendado(s). O robo posta sozinho no horario.")


if __name__ == "__main__":
    main()
