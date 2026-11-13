"""Coisas usadas por todos os scripts: config, fila, horario."""
import datetime as dt
import json
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parent
ARQ_CONFIG = RAIZ / "config.json"
ARQ_FILA = RAIZ / "fila.json"


def ler_config():
    return json.loads(ARQ_CONFIG.read_text(encoding="utf-8"))


def salvar_config(cfg):
    ARQ_CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ler_fila():
    if not ARQ_FILA.exists():
        return []
    return json.loads(ARQ_FILA.read_text(encoding="utf-8"))


def salvar_fila(fila):
    fila.sort(key=lambda i: i["quando"])
    ARQ_FILA.write_text(json.dumps(fila, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fuso(cfg):
    return dt.timezone(dt.timedelta(hours=cfg.get("fuso_horas", -3)))


def agora(cfg):
    return dt.datetime.now(fuso(cfg))


def quando(item):
    return dt.datetime.fromisoformat(item["quando"])


def url_video(cfg, item):
    return f"https://github.com/{cfg['repo']}/releases/download/{cfg['release_fila']}/{item['arquivo']}"
