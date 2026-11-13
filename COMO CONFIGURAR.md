# Robô de postagem — vicenix

Ele lê `G:\Meu Drive\GTA6\PRONTOS PARA POSTAR` (pasta por dia, `12h - Video NN - x.mp4` + `- LEGENDA.txt`),
sobe os vídeos pro GitHub e um robô no GitHub posta **sozinho no horário**, com o PC desligado. É grátis.

| Rede | Situação |
|---|---|
| Instagram (Reels) | **Automático** assim que você fizer os passos 1, 2 e 4. |
| YouTube Shorts | Código pronto, **desligado**. O Google trava como privado todo vídeo enviado por app novo até aprovar uma auditoria (grátis, leva semanas). Faça o passo 3 e peça a auditoria. |
| TikTok / Kwai | Manual por enquanto. No TikTok dá pra agendar até 10 dias antes pelo site (TikTok Studio). |

Faça uma vez só, na ordem. Leva uns 20 minutos.

---

## 1. GitHub (5 min)

1. Dê dois cliques em **`1 - CONFIGURAR.bat`**.
2. Ele instala o GitHub CLI e abre o navegador: entre na sua conta do GitHub e autorize.
   (Se ele disser que acabou de instalar o `gh` e não achou, feche e abra o `.bat` de novo.)
3. Ele pergunta o nome do repositório: só aperte Enter (`vicenix-autopost`).

> O repositório é **público**: o Instagram só aceita o vídeo num link aberto (e o robô é ilimitado em repo público).
> As senhas/tokens ficam nos **Segredos** do GitHub, criptografados, e nunca aparecem no código.
> Quem abrir o repo vê os vídeos da fila e o seu nome de usuário do GitHub. Se o canal é pra ser anônimo,
> use um usuário do GitHub que não tenha seu nome.

## 2. Instagram (10 min)

A conta `@vicenix45` já é Profissional, então não precisa de Página do Facebook.

1. Entre em **developers.facebook.com** → **Meus apps** → **Criar app**.
   (Se pedir, cadastre-se como desenvolvedor com seu Facebook. O app não aparece no seu perfil.)
2. Nome do app: `vicenix autopost`. Caso de uso: **"Gerenciar mensagens e conteúdo no Instagram"**. Conclua.
3. No app: **Casos de uso** → **Personalizar** (no caso do Instagram) → **Configuração da API com login do Instagram**.
   Confira se as permissões `instagram_business_basic` e `instagram_business_content_publish` estão adicionadas.
4. Em **"Gerar tokens de acesso"** → **Adicionar conta** → entre com a `@vicenix45` e permita.
   - Se pedir pra aceitar convite de testador: no app do Instagram, **Configurações → Apps e sites → Convites de testador → Aceitar**, e volte aqui.
5. Clique em **Gerar token** ao lado da conta e **copie** o token.
6. Crie o token do GitHub que deixa o robô renovar o do Instagram sozinho (ele vence em 60 dias):
   **github.com/settings/personal-access-tokens/new** →
   nome `renovar-instagram`, validade **1 ano**, *Repository access*: **Only select repositories** → `vicenix-autopost`,
   *Permissions* → **Secrets: Read and write** → **Generate token** → copie.
7. Dê dois cliques em **`2 - CONECTAR INSTAGRAM.bat`** e cole o token do Instagram (não aparece na tela, é normal).
   Depois ele pede o token do GitHub (item 6): cole também.

> O app fica em "modo de desenvolvimento" pra sempre, e tudo bem: nesse modo ele posta na sua própria conta sem precisar de revisão da Meta.

## 3. YouTube (10 min, pode deixar pra depois)

1. **console.cloud.google.com** → seletor de projeto → **Novo projeto** → nome `vicenix` → Criar.
2. **APIs e serviços → Biblioteca** → procure **YouTube Data API v3** → **Ativar**.
3. **Google Auth Platform** (ou "Tela de permissão OAuth") → **Começar**: nome `vicenix autopost`, seu e-mail,
   público **Externo**, aceite e crie.
4. **Público** → **Publicar app** → confirmar (fica "Em produção").
   **Não pule isso**: em "Teste" a autorização vence a cada 7 dias.
5. **Clientes** → **Criar cliente** → tipo **App para computador** → Criar → **Baixar JSON**.
   Salve nesta pasta `AUTOPOST` com o nome **`client_secret.json`** (ele nunca sobe pro GitHub).
6. Dê dois cliques em **`3 - CONECTAR YOUTUBE.bat`** → entre na conta Google do canal → escolha o canal.
   Aviso "O Google não verificou este app" → **Avançado → Acessar** (é o seu próprio app).
7. Peça a auditoria: **support.google.com/youtube/contact/yt_api_form**. Uso: "ferramenta interna pra publicar
   os vídeos do meu próprio canal, sem outros usuários". Quando aprovarem, em `config.json` troque
   `"youtube": false` por `true` e rode o `1 - CONFIGURAR.bat` de novo pra subir a mudança.

## 4. Mandar os vídeos pra fila (todo lote novo)

Dê dois cliques em **`4 - ENVIAR VIDEOS PRA FILA.bat`**. Ele pega todo vídeo novo de `PRONTOS PARA POSTAR`
com horário que ainda não passou, sobe e agenda. Pode rodar quantas vezes quiser: o que já está na fila é ignorado.

**`VER FILA.bat`** mostra o que já foi postado e o que está esperando.

---

## Como funciona

- O robô roda **a cada 30 min, das 9h às 23h30**. O GitHub às vezes atrasa uns minutos, então um vídeo das 12h sai entre 12h e 12h40.
- Ele posta **1 vídeo por rodada**. Se der erro, tenta de novo nas próximas rodadas (até 3 vezes).
  Se falhar, a rodada fica vermelha e o GitHub te avisa por e-mail.
- Vídeo com **mais de 24h de atraso** não é postado (pra não despejar vários de uma vez). Pra reagendar, mude o
  `"quando"` dele na `fila.json` e suba de novo.
- Depois de postado, o vídeo é apagado da fila do GitHub (o original continua no seu Drive).
- Vídeos com narração de IA (os que têm `_sistema\narracoes\vNN.txt`) sobem no YouTube com o aviso de "conteúdo alterado/sintético", como o YouTube exige.
- Pra postar agora sem esperar: github.com → seu repo → **Actions → Postar videos → Run workflow**.
- Pra parar tudo: **Actions → Postar videos → ⋯ → Disable workflow**.
