# WINDI-HIOS-CONNECTOR — HANDOFF PARA CCODE · 001

```
Estado:       ORDENAÇÃO CANDIDATA · 2026-09-06
De:           Observador cloud (Claude.ai web, sem SSH), a pedido do Human Dragon
Para:         Executor on-origin (CCode/Codex, Strato)
Gate:         Human Dragon (I9) entre TODOS os capítulos
Doc irmão:    WINDI-HIOS-PROTOCOL-001-CANDIDATE.md (contrato de verificação)
Contexto:     llms.txt v2.0 confirmado ao vivo em 2026-09-06 com ambas as linhas canónicas presentes.
              Human Dragon decidiu abrir sessão CCode para trabalhar o connector.
Backlog Vivo: PLAYGROUND-BACKLOG-2026-09-06-d (Drive, pasta "WINDI Playground — Backlog Vivo")
```

> Regra-mãe: um gesto que FECHA ponta-a-ponta vale mais do que oito a 90%.
> Entrega-se UM capítulo por mensagem. O seguinte só sai quando o anterior fecha. O humano é o gate.

---

## 0 · Ler antes de tudo (ordem de carga)

1. `windi-session-continuity` — CLAUDE.md + CLAUDE-HISTORY.md **antes** de propor trabalho.
2. `windi-motor-fremde` — a doutrina do connector. **Tem duas metades com pesos diferentes:** a Lei I–III
   está assente; a Postura de prova (A/B) **NÃO está**. Não tratar a segunda como resolvida por estar escrita.
3. `windi-payment-sovereignty` — o precedente arquitetural ("usar terceiro sem herdar a responsabilidade dele").
4. `windi-metodo-capitulos` — o esqueleto de capítulo usado abaixo.

---

## 1 · Os três papéis (nunca colapsar)

- **Observador (cloud):** símptomas públicos, achados, ordenações, backlog. Sem verdict, sem selo, sem SSH.
- **Executor (CCode):** evidência de fonte, executa capítulos, reporta e **PÁRA**.
- **Humano (I9):** prioridade, Teste do Humano, graduação. Nenhuma IA decide por ele.

---

## 2 · GATES — o que tem de estar verde ANTES de código de connector

A doutrina é explícita: *"se a decisão continuar aberta, não escrever código de connector. Apresentar a
matriz, obter a decisão, registar no HISTORY, e só então propor capítulos."* Estes gates não são burocracia;
são a forma de não construir sobre a postura errada.

### G-A · `[BLOQUEADO até decisão I9]` Postura de prova — Passante (A) vs Testemunha (B)

| | **A · Passante** | **B · Testemunha** |
|---|---|---|
| Fluxo | pedido sai pelo WINDI → motor do fremder → resposta volta pelo WINDI | fremder liga-se direto ao motor dele; WINDI nunca vê tráfego; volta só o artefacto que ele escolhe trazer |
| Prova | a ligação pedido→resposta (input, output, motor, instante) | integridade do que foi trazido (o que já prova hoje) |
| Política de dados intacta | ✗ — WINDI vê conteúdo em trânsito | ✓ |
| Moldura verbal atual sobrevive | ✗ — exige reescrever a promessa pública | ✓ |
| Superfície de ataque / responsabilidade | alta | mínima |
| Diferenciação de mercado | alta | média |
| Relação com PROTOCOL-001 | exige componente adicional (passthrough) **não especificado**; viola P-1 tal como escrito | **integralmente servida** pelo §3 do contrato |

**Decisão:** Human Dragon, e só. Registar em `CLAUDE-HISTORY.md` com data. Sem esta linha no HISTORY,
nenhum capítulo de código arranca.

### G-B · ~~`[BLOQUEADO até caminho de leitura verde]`~~ → **`[SATISFEITO para âmbito só-leitura · relato CCode CAP 0/1 · 2026-09-06]`** Sequência protegida

> Estado após CAP 0/1: `/api/v1/hios-open/<hash>` (200/404 JSON) e `/api/receipts/{id}` (200/404 JSON)
> respondem de forma observável e estável; `llms.txt` + espelhos 200. O caminho de **leitura** está verde por
> relato on-origin. O gate continua **fechado para escrita** (Portão 2). Ressalva: o serviço hios-open corre via
> nohup sem systemd (HIOS-OPEN-NOHUP-001) — "verde hoje" não é "verde após reboot".

Connectors são **amplificadores**: amplificam uma experiência que funciona, não substituem uma que não
fecha. O v0.1 do contrato é **só-leitura** (P-6), portanto o gate aplica-se ao **caminho de leitura**:
`/verify-public/` e `/api/v1/hios-open/<hash>` têm de responder de forma observável e estável (CAP 0
fornece a evidência). As operações de **escrita** ficam atrás do Portão 2 (`LEDGER-WRITE-SILENT-FAIL-001`
ainda `[A CONFIRMAR]`; "Registar no Ledger" `[BLOQUEADO ao fremder]`) e **não entram** neste handoff.

### G-C · Lei II — o connector nunca é o primeiro gesto

O degrau zero (colar texto → Provar → ver hash, sem conta, sem chave) continua a ser a fundação. O connector
aparece **depois**. Qualquer desenho que ponha o connector antes do primeiro hash está errado.

---

## 3 · Checklist obrigatório (responde-se ANTES de o CCode escrever código — não com ele aberto)

- [ ] L1 (moldura verbal, CAP3-ter `46fbe2a20`) foi testada com humano fresco? Resultado?
- [ ] Postura de prova decidida (A ou B)? Registada no HISTORY com data?
- [ ] Degrau zero funciona hoje, sem connector, na superfície pública?
- [ ] Qual a moldura verbal nova do connector, escrita **antes** do código? (Lei III)
- [ ] Onde entra a prova no fluxo, agora que deixa de ser o primeiro gesto?
- [ ] Que motores são admissíveis, e como se certificam? (`windi-certification`)

---

## 4 · CAP 0 — Evidence Request read-only (**pode correr JÁ; não depende de G-A/G-B**)

Este capítulo **não escreve nada**. Fornece a evidência que o observador cloud não consegue obter
(byte-cego: não vê `<head>`, status codes, JSON real). Sem isto o adaptador do connector seria construído
contra um esquema presumido — a cartola que o connector existe para eliminar.

```
=============== PRONTO-A-COLAR NO CCODE ===============

[CCODE] — HIOS-CONNECTOR · CAPÍTULO 0/4 (só este) — EVIDENCE REQUEST READ-ONLY

Objetivo único: obter a forma REAL (pedido + resposta) dos endpoints de leitura que o connector vai
mapear, mais três confirmações de superfície. Read-only. Não mudar ficheiros, serviços, nginx, Ledger,
receipts ou selos (só leitura salvo autorização I1).

Fazer:
1. HIOS-OPEN — hash conhecido e desconhecido:
   for H in ba4db3cda9b9efbd0f0bc78af31a8dd8a82a673b2d9fb7105e0e7c9deba47fab 0000000000000000000000000000000000000000000000000000000000000000; do
     URL="https://windi-domain.com/api/v1/hios-open/$H"
     curl -L -sS -D /tmp/hdr_$H.txt -o /tmp/body_$H.json -w "status=%{http_code}\nfinal_url=%{url_effective}\ntime_total=%{time_total}\nsize_download=%{size_download}\ncontent_type=%{content_type}\n" "$URL"
     sha256sum /tmp/body_$H.json; sed -n '1,40p' /tmp/hdr_$H.txt; cat /tmp/body_$H.json | head -c 4000; echo
   done
   Também: curl -sS -o /dev/null -w "root_status=%{http_code}\n" https://windi-domain.com/api/v1/hios-open/   (404 ESPERADO)
2. VERIFY-PUBLIC — descobrir a forma do pedido:
   URL="https://windi-domain.com/verify-public/"; curl -L -sS -D /tmp/hdr_vp.txt -o /tmp/body_vp.html -w "status=%{http_code}\ncontent_type=%{content_type}\nsize_download=%{size_download}\n" "$URL"; sha256sum /tmp/body_vp.html
   Extrair do HTML/JS: método (GET/POST), nome do parâmetro do hash, endpoint interno que a página chama, forma da resposta (JSON? campos?).
   grep -n -i -E "fetch\(|XMLHttpRequest|action=|/api/" /tmp/body_vp.html | head -40
   Na fonte: grep -rn -i -E "verify-public|hios-open|verify_public" /home/windi/w-workbench-001/ /opt/windi/ --include=*.py --include=*.js --include=*.html --include=*.conf 2>/dev/null | head -40
3. LLMS.TXT + espelhos:
   for P in llms.txt llms.pt.txt llms.de.txt; do curl -sS -o /tmp/$P -w "$P status=%{http_code} size=%{size_download}\n" "https://windi-domain.com/$P"; sha256sum /tmp/$P; done
   grep -c -F "Generated is not verified." /tmp/llms.txt; grep -c -F "Guide; do not verdict." /tmp/llms.txt
   Fonte on-origin do llms.txt (path + sha256sum + mtime).
4. ROTA /playground/ (possível link partido no degrau zero — llms.txt PART 5 aponta /playground/; o monitor vigia /artifacts/playground.html):
   curl -sS -o /dev/null -w "status=%{http_code}\nfinal_url=%{url_effective}\n" -L https://windi-domain.com/playground/
   Confirmar no nginx (read-only) se /playground/ redireciona, serve o mesmo HTML, ou 404.
5. W-TUBE-001 (MCP gateway — provável base de transporte): path, estado (systemctl status / porta), versão. Só reportar.
6. git status (read-only) em /home/windi/w-workbench-001 e /opt/windi/docs — não inferir diff se não houver histórico.

Definition of Done (único critério): colar aqui, verbatim, (a) os dois JSON de hios-open + status codes, (b) o método/parâmetro/endpoint real do verify-public, (c) status+sha256 dos três llms*.txt, (d) status+final_url de /playground/, (e) estado do W-TUBE-001. Cada item marcado OBSERVED / NOT FOUND / NOT CONFIRMABLE.

SCOPE LOCK: só isto. Achado fora deste caminho → uma linha no log e segue, não persegue. Sem refactor.

NÃO TOCAR: nenhum ficheiro, nginx, serviço, Ledger, receipt, selo. Não criar hashes de teste. Não escrever código de connector.

Ao terminar: responde só com "CAP0 OK + [a prova pedida]" e PÁRA. Eu envio o capítulo seguinte. Não avances sozinho.

=============== FIM ===============
```

---

## 5 · CAP 1–4 — esboço (só arrancam com G-A + G-B verdes; o humano envia UM de cada vez)

Cada um será redigido no esqueleto fixo no momento de envio. Aqui fica o **objetivo único** e a **DoD**
de cada, para o humano ver a rota inteira antes de dar o primeiro passo.

**CAP 1 — Colocar e ajustar o contrato** (só documento)
Objetivo: `/opt/windi/docs/WINDI-HIOS-PROTOCOL-001-CANDIDATE.md` no repositório, com o §5 ajustado ao
esquema real vindo do CAP 0.
DoD: ficheiro existe; sha256sum reportado; Human Dragon leu e disse "contrato OK" (ou anotou o que muda).
NÃO TOCAR: código, endpoints, llms.txt.

**CAP 2 — A peça de maior risco, isolada:** `hios.verify` + `hios.receipt` contra o backend real
Objetivo: servidor MCP mínimo (Python/FastMCP, o que o Strato já fala) com **só** estas duas tools,
hash-only (P-1), tecto semântico no schema (P-2), sem UI, sem polish.
DoD: três testes locais verdes — `FOUND` com o hash conhecido, `NOT_FOUND` com hash desconhecido
(com `scope` e frase fixa), `UNAVAILABLE` com backend inalcançável (nunca colapsado em NOT_FOUND).
Reutilizar, não reinventar: ~~verificar se o W-TUBE-001 serve de transporte~~ — **CAP 0 mostrou que o W-TUBE-001
é um git worktree, não um serviço** (sem systemd, sem porta, sem pyproject). O connector é serviço novo. O que se
reutiliza é o módulo que já responde em `/api/v1/hios-open/`: **`/opt/windi/w-hios-open-001/hios_open_api.py`
(porta 8202, nginx `upstream windi_hiosopen`)** — ler antes de escrever; os invariantes I9/I11/I14/I19 já lá estão.
`hios.verify` é **dois saltos** (hios-open → `anchor_info.receipt_id` → `/api/receipts/{id}.created_at`); testar
o caso em que o segundo salto falha (`registered_at_utc` omitido, nunca inventado). Acrescentar o 4.º teste:
`lineage_discovery.timestamp_utc` **nunca** aparece em `record`.
**Atenção (lição do CAP 0):** `/verify-public/api/intake-receipt` é POST de **escrita** — nunca o ligar a `hios.verify`.
NÃO TOCAR: escrita, selo, Ledger, nginx, VERA/MARIA, passthrough de conteúdo.

**CAP 3 — `hios.conduct` + `instructions` do connector**
Objetivo: o llms.txt vivo a chegar ao modelo pela fonte, com `canonical_lines_present` calculado.
DoD: tool devolve texto + versão + `maturity: CANDIDATE` + `canonical_lines_present: true` contra o llms.txt real.
NÃO TOCAR: as tools do CAP 2.

**CAP 4 — Capítulo de palavras (Lei III) + manifesto de instalação**
Objetivo: a moldura verbal do connector (o que o fremder lê ao instalar e ao usar) escrita e alinhada com
a postura decidida em G-A; manifesto instalável para Claude e equivalente para GPT.
DoD: Teste do Humano — janela anónima, alguém que nunca viu o projeto instala e obtém um `hios.verify`
com resultado + próximo passo em segundos, zero becos.
Nota: **nunca fechar um capítulo de arquitetura sem o capítulo de palavras.** Foi o erro que gerou o FREMDE-UX-001.

**Deferido (registar como [ABERTO] pós-gate, nunca "já agora"):** `hios.structure_intent`, `hios.register`,
`hios.seal`; spec publicada separada da implementação (§7 do contrato); segundo implementador.

---

## 6 · NÃO TOCAR — em nenhum capítulo deste handoff

- Operações de escrita no Ledger, selos, receipts, FORENSIC_PASS — nem reais nem "de exemplo".
- nginx, systemd, serviços — sem autorização I1 explícita.
- VERA / MARIA como motor de resposta ao fremder (anti-pattern 1 da doutrina).
- Qualquer caminho que passe **conteúdo** pelo WINDI antes de a Postura A/B estar decidida (anti-pattern 3:
  "porque era mais fácil" = decidir a Postura A sem gate humano).
- O degrau zero. Não "melhorar" o playground por arrasto.
- Declarar qualquer coisa "selada". Não inventar §.

---

## 7 · Itens para o Backlog Vivo (estado após CAP 1 — entrada 2026-09-06-f)

- `[CAP 0 OK · CAP 1 OK · 2026-09-06]` Evidência integrada no contrato v0.3 (§3, §4, §5). sha256 a bater em 3 pontos.
- `[BLOQUEADO até decisão I9]` HIOS-CONNECTOR-POSTURA-001 — Passante vs Testemunha. **Ainda sem linha no HISTORY. É o único gate que resta para o CAP 2.**
- `[A CONFIRMAR pelo humano]` "contrato OK" sobre a v0.3 (leitura do Human Dragon; DoD do CAP 1 do lado humano).
- `[BLOQUEADO até G-A]` HIOS-CONNECTOR-CAP2..4. (G-B satisfeito para só-leitura.)
- `[NOVO][ABERTO][I9]` HIOS-OPEN-SCHEMA-404-001 — `$schema` anunciado pela API devolve 404. Publicar ou retirar.
- `[NOVO][ABERTO][RISCO][I1]` HIOS-OPEN-NOHUP-001 — serviço hios-open (porta 8202) via nohup desde 05 Jul, sem systemd. Reboot = superfície 8 FAIL. Capítulo próprio, fora deste handoff.
- `[NOVO][VIGIAR]` RECEIPTS-PUBLIC-BY-ID — tags/metadata públicos por id; entra na moldura verbal do CAP 4.
- `[NOVO][ACHADO]` INTENT-LEXICON-SERVED — o backend já serve a conduta por verbo em JSON (15 intents, layer, ai_can); `hios.intents` acrescentado ao contrato.
- `[RESOLVIDO · relato CCode]` HIOS-OPEN-ANCHOR-INFO-001 — anchor_info é metadata da obra; timestamp vive em `/api/receipts/{id}.created_at`.
- `[RESOLVIDO · relato CCode]` HIOS-VERIFY-PUBLIC-SCHEMA-001 — é POST de escrita (`intake-receipt`); leitura por hash = `hios-open`, por id = `/api/receipts/{id}` (este último A CONFIRMAR).
- `[RESOLVIDO · relato CCode]` PLAYGROUND-ROUTE-001 — `/playground/` → 200 → `/artifacts/playground.html`.
- `[RESOLVIDO · relato CCode]` LLMS-MIRRORS-001 — `/llms.pt.txt` e `/llms.de.txt` existem (200).
- `[NOVO][ACHADO]` W-TUBE-001-NOT-A-SERVICE — worktree git, não serviço MCP; doutrina `windi-motor-fremde` a corrigir ("provável base do transporte" → não é).
- `[NOVO][ACHADO]` HIOS-OPEN-SPEC-EXISTS — o backend já fala `W-HIOS-OPEN-SPEC-001 v0.1.0` com `$schema` próprio; PROTOCOL-001 reposicionado como camada connector complementar, não rival.
- `[A CONFIRMAR]` HIOS-OPEN-ANCHOR-INFO-001 — conteúdo de `anchor_info` (timestamp?), 15 intents, existência de `/schemas/hios-open-v1.json`, schema real de `/api/receipts/{id}` (CAP 1).
- `[ABERTO][I9]` LLMS-TXT-TIGHTEN-001 — reduzido a **dois** apertos (PART 2↔6; lemas vs tecto). O item da rota caiu.

---

```
Boundary: sem SSH pelo observador cloud; relatos de executor = relato, não observação.
No receipt, no seal, no verdict. CANDIDATE stays CANDIDATE. I9 = humano.
Este handoff não decide a Postura A/B e não contém código de connector.
```
