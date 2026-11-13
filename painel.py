"""Gera 'PAINEL DE POSTAGEM.html' dentro da pasta PRONTOS PARA POSTAR e abre no navegador.

Um cartao por video (dia/hora), com o video, botoes de copiar o texto de cada rede,
e caixinhas pra marcar o que ja foi agendado/postado (ficam salvas no navegador).
"""
import json
import os
import pathlib
import sys

from comum import agora, ler_config, ler_fila, quando
from enfileirar import RE_DIA, RE_VIDEO, ler_legenda, montar_item

MODELO = r"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Painel de Postagem</title>
<style>
:root{--bg:#0f1115;--card:#181b22;--line:#2a2f3a;--txt:#e8eaf0;--mut:#8b93a5;--yt:#ff3b3b;--tt:#25f4ee;--kw:#ff8a00;--ig:#d62f7f;--ok:#2ecc71}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:15px/1.45 system-ui,Segoe UI,sans-serif}
header{position:sticky;top:0;z-index:5;background:#0f1115ee;backdrop-filter:blur(6px);border-bottom:1px solid var(--line);padding:14px 20px}
h1{margin:0 0 8px;font-size:20px}.links{display:flex;gap:8px;flex-wrap:wrap}
.links a{color:var(--txt);text-decoration:none;border:1px solid var(--line);border-radius:8px;padding:6px 12px;font-size:14px}
.links a:hover{border-color:var(--mut)}
.filtros{margin-top:10px;display:flex;gap:14px;flex-wrap:wrap;color:var(--mut);font-size:14px}
main{max-width:1100px;margin:0 auto;padding:20px}
details.ajuda{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin-bottom:18px}
details.ajuda summary{cursor:pointer;font-weight:600}details.ajuda li{margin:4px 0}
.dia{margin:26px 0 10px;font-size:17px;font-weight:700;color:var(--mut)}
.card{display:grid;grid-template-columns:150px 1fr;gap:16px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;margin-bottom:12px}
.card.passado{opacity:.55}.card.feito{border-color:#2ecc7155}
video{width:150px;aspect-ratio:9/16;border-radius:10px;background:#000;object-fit:cover}
.topo{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:8px}
.hora{font-size:20px;font-weight:800}.tit{font-weight:600}
.tag{font-size:12px;border-radius:999px;padding:2px 8px;border:1px solid var(--line);color:var(--mut)}
.tag.ia{color:#ffd166;border-color:#ffd16666}
.redes{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}
.rede{border:1px solid var(--line);border-left:4px solid var(--c);border-radius:10px;padding:10px}
.rede h3{margin:0 0 6px;font-size:14px;display:flex;justify-content:space-between;align-items:center}
.rede p{margin:0 0 8px;color:var(--mut);font-size:13px;white-space:pre-wrap;max-height:4.5em;overflow:hidden}
button{background:#232836;color:var(--txt);border:1px solid var(--line);border-radius:8px;padding:6px 10px;cursor:pointer;font-size:13px;margin:0 6px 6px 0}
button:hover{border-color:var(--c,var(--mut))}button.copiado{background:var(--ok);color:#000;border-color:var(--ok)}
label.chk{font-size:12px;color:var(--mut);display:flex;gap:5px;align-items:center;cursor:pointer;font-weight:400}
.auto{font-size:12px;color:var(--ig)}
@media (max-width:640px){.card{grid-template-columns:1fr}video{width:100%;max-width:220px}}
</style></head><body>
<header>
  <h1>Painel de Postagem · vicenix</h1>
  <div class="links">
    <a href="https://studio.youtube.com" target="_blank">YouTube Studio ↗</a>
    <a href="https://www.tiktok.com/tiktokstudio/upload" target="_blank">TikTok Studio ↗</a>
    <a href="https://www.kwai.com" target="_blank">Kwai ↗</a>
    <a href="https://github.com/__REPO__/actions" target="_blank">Robô do Instagram ↗</a>
  </div>
  <div class="filtros">
    <label class="chk"><input type="checkbox" id="esconderPassados" checked> esconder horários que já passaram</label>
    <label class="chk"><input type="checkbox" id="esconderFeitos"> esconder vídeos já agendados em todas as redes</label>
  </div>
</header>
<main>
<details class="ajuda"><summary>Como agendar a semana inteira (uns 20 min por rede)</summary>
<p><b>YouTube Shorts</b> (studio.youtube.com → Criar → Enviar vídeos; dá pra selecionar até 15 de uma vez):</p>
<ol><li>Arraste os vídeos da pasta do dia. Em cada um: <b>Copiar título</b> → cola no título, <b>Copiar descrição</b> → cola na descrição.</li>
<li>“É conteúdo para crianças?” → <b>Não</b>. Em <b>Conteúdo alterado</b>: <b>Sim</b> nos vídeos com a etiqueta <span class="tag ia">voz IA</span>, <b>Não</b> nos outros.</li>
<li>Visibilidade → <b>Programar</b> → coloque a data e a hora do cartão → Programar.</li></ol>
<p><b>TikTok</b> (pelo computador, TikTok Studio → Enviar; agenda com até 10 dias de antecedência):</p>
<ol><li>Envie o vídeo → <b>Copiar legenda</b> → cola na descrição.</li>
<li>Ative <b>Programar</b> → data e hora do cartão → Programar.</li></ol>
<p><b>Kwai</b>: não tem agendamento. No horário, pelo celular: abra o vídeo no app do Google Drive (pasta GTA6/PRONTOS PARA POSTAR) → baixar → postar no Kwai com a legenda do arquivo <i>LEGENDA.txt</i> (ou copie daqui e mande pro celular).</p>
<p><b>Instagram</b>: automático pelo robô. Se precisar postar na mão, a legenda está no cartão.</p>
<p>Marque as caixinhas conforme for agendando. Elas ficam salvas neste computador.</p>
</details>
<div id="lista"></div>
</main>
<script>
const DADOS = __DADOS__;
const REDES = [
  {k:"youtube", nome:"YouTube Shorts", c:"var(--yt)", botoes:[["Copiar título","titulo"],["Copiar descrição","descricao"]]},
  {k:"tiktok", nome:"TikTok", c:"var(--tt)", botoes:[["Copiar legenda","legenda"]]},
  {k:"kwai", nome:"Kwai", c:"var(--kw)", botoes:[["Copiar legenda","legenda"]]},
  {k:"instagram", nome:"Reels", c:"var(--ig)", botoes:[["Copiar legenda","legenda"]], auto:true},
];
const mem = {get(k){try{return localStorage.getItem(k)}catch(e){return null}}, set(k,v){try{localStorage.setItem(k,v)}catch(e){}}};
function copiar(txt, btn){
  const ok=()=>{btn.classList.add("copiado");const t=btn.textContent;btn.textContent="Copiado!";setTimeout(()=>{btn.classList.remove("copiado");btn.textContent=t},1200)};
  if(navigator.clipboard){navigator.clipboard.writeText(txt).then(ok,()=>velho(txt)&&ok())}else if(velho(txt))ok();
}
function velho(txt){const t=document.createElement("textarea");t.value=txt;document.body.appendChild(t);t.select();let r=false;try{r=document.execCommand("copy")}catch(e){}t.remove();return r}
function feitoTudo(v){return REDES.filter(r=>!r.auto&&v[r.k]).every(r=>mem.get(v.id+":"+r.k)==="1")}
function render(){
  const escP=document.getElementById("esconderPassados").checked, escF=document.getElementById("esconderFeitos").checked;
  const L=document.getElementById("lista"); L.innerHTML=""; let dia="";
  const agora=Date.now();
  for(const v of DADOS){
    const passado = new Date(v.quando).getTime() < agora - 30*60*1000;
    if(escP&&passado) continue;
    if(escF&&feitoTudo(v)) continue;
    if(v.dia!==dia){dia=v.dia;const h=document.createElement("div");h.className="dia";h.textContent=dia;L.appendChild(h)}
    const c=document.createElement("div"); c.className="card"+(passado?" passado":"")+(feitoTudo(v)?" feito":"");
    c.innerHTML=`<video src="${encodeURI(v.video)}" controls preload="metadata"></video><div>
      <div class="topo"><span class="hora">${v.hora}</span><span class="tit"></span>${v.ia?'<span class="tag ia">voz IA</span>':''}</div>
      <div class="redes"></div></div>`;
    c.querySelector(".tit").textContent=v.titulo;
    const R=c.querySelector(".redes");
    for(const r of REDES){
      if(!v[r.k]) continue;
      const d=document.createElement("div"); d.className="rede"; d.style.setProperty("--c",r.c);
      const chave=v.id+":"+r.k;
      d.innerHTML=`<h3><span>${r.nome}</span>${r.auto?`<span class="auto">${v.igStatus}</span>`:`<label class="chk"><input type="checkbox"> agendado</label>`}</h3><p></p>`;
      d.querySelector("p").textContent = r.k==="youtube" ? v.youtube.titulo : v[r.k].legenda;
      for(const [rot,campo] of r.botoes){const b=document.createElement("button");b.textContent=rot;b.onclick=()=>copiar(v[r.k][campo],b);d.appendChild(b)}
      const cb=d.querySelector("input");
      if(cb){cb.checked=mem.get(chave)==="1";cb.onchange=()=>{mem.set(chave,cb.checked?"1":"0");c.classList.toggle("feito",feitoTudo(v))}}
      R.appendChild(d);
    }
    L.appendChild(c);
  }
  if(!L.children.length) L.innerHTML='<p style="color:var(--mut)">Nada pendente. Gere mais vídeos e rode o painel de novo.</p>';
}
for(const id of ["esconderPassados","esconderFeitos"]){const e=document.getElementById(id);const s=mem.get("f:"+id);if(s!==null)e.checked=s==="1";e.onchange=()=>{mem.set("f:"+id,e.checked?"1":"0");render()}}
render();
</script></body></html>
"""

DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


def main():
    cfg = ler_config()
    base = pathlib.Path(cfg["pasta_postar"])
    fila = {i["id"]: i for i in ler_fila()}
    dados = []
    for pasta in sorted(p for p in base.iterdir() if p.is_dir() and RE_DIA.match(p.name)):
        for video in sorted(pasta.glob("*.mp4")):
            if not RE_VIDEO.match(video.name):
                continue
            r = montar_item(cfg, pasta, video)
            if not r:
                continue
            item = r[0]
            leg = ler_legenda(video.with_name(video.stem + " - LEGENDA.txt"))
            q = quando(item)
            st = fila.get(item["id"], {}).get("status", {}).get("instagram", {})
            ig = ("postado ✓" if st.get("ok") else "erro ✗" if st.get("erro") else
                  "automático" if item["id"] in fila else "fora da fila")
            dados.append({
                "id": item["id"], "quando": item["quando"], "titulo": item["titulo"], "ia": item["ia"],
                "dia": f"{q:%d/%m} ({DIAS[q.weekday()]})", "hora": f"{q:%H:%M}",
                "video": f"{pasta.name}/{video.name}",
                "youtube": item["youtube"], "instagram": item["instagram"], "igStatus": ig,
                "tiktok": item.get("tiktok"),
                "kwai": {"legenda": f"{leg['kwai'][0]}\n\n{leg['kwai'][1]}".strip()} if "kwai" in leg else None,
            })
    html = MODELO.replace("__DADOS__", json.dumps(dados, ensure_ascii=False)).replace("__REPO__", cfg.get("repo", ""))
    saida = base / "PAINEL DE POSTAGEM.html"
    saida.write_text(html, encoding="utf-8")
    print(f"Painel gerado com {len(dados)} video(s): {saida}  (agora: {agora(cfg):%d/%m %H:%M})")
    if "--nao-abrir" not in sys.argv:
        os.startfile(saida)


if __name__ == "__main__":
    main()
