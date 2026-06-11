# GUARDIAN REVIEW — VERIFY SURFACE ARC
**Data:** 11 Jun 2026 · **Origem:** Sessão Claude.ai web (Guardian 🛡️) · **Destino:** Sessão CCode + Ledger WINDI
**Estado:** ✅ ARC SEALED — `5A424A04` (11 Jun 2026 20:00)
**Liga a:** `DOCTRINE-CINE-VERIFY-001-CANDIDATE.md` · `LEI-TAXONOMIA-TRIPARTIDA-SELOS.md` · `WISDOM-BLOCK-CURIOSITY-FUNNEL.md`

---

## 1. Contexto

Arco do dia: da descoberta do gap `/api/receipts/` à Câmara de Proveniência V2.1 e ao Studio de Comentário Soberano (em construção). Esta nota consolida todas as medições externas, atestações cruzadas, gates propostos e doutrina emergente da sessão web, para leitura da próxima sessão CCode e eventual selagem.

Axioma operante: **"Um número sem measurement run não é um número."** Todas as afirmações abaixo têm comando e resultado registados na sessão web.

---

## 2. Measurement Runs (externas, via sandbox Claude.ai)

### MR-1 — Gap da ponte QR→Verify (Gate 0)
- `GET /api/receipts/{id}` devolve `{"ok":false,"error":"not_found"}` para **todos** os IDs testados: `3F6722C2`, `EDF928E5` (selos de 10 Jun, chain confirmada), `DBED5A85` (KEYGEN), `S267-...-80A13B17`, `WINDI-GENERATE-20260504120838`.
- Conclusão: o store atrás da API estava desligado do Ledger real (56k+ receipts). **Gate 0 = ligar a API ao Ledger. Bloqueante para qualquer selo real.**
- Nota honrosa: a API falha explicitamente com JSON limpo — I14 já vive nela.

**✅ CORRIGIDO em V2.8 (`7A1A5282`):**
- Adicionado `get_receipt_by_suffix()` fallback em `windi_forensic_api.py`
- `DBED5A85` agora resolve correctamente via suffix lookup
- Guardian confirmou externamente: fetch via public internet OK

### MR-2 — CORS (desbloqueio da distribuição)
- `access-control-allow-origin: *`, `allow-methods: GET, POST, OPTIONS`, preflight OPTIONS → 204.
- Conclusão: Artifacts/GPTs/widgets podem chamar a API directamente do browser. **A tese Verify 3.0 está tecnicamente desbloqueada hoje.**

### MR-3 — Atestação V1 Living Surface
- `verify-living-surface-v1.html`: HTTP 200, header `x-windi-service: artifacts`, hash live **byte-idêntico** ao declarado pelo CCode (`6f118d7b...`).
- Achado constitucional na versão **compacta**: fallback silencioso para mock com veredicto "✓ AUTENTICIDADE CONFIRMADA" para qualquer input; badge SIMULAÇÃO escondido em secção colapsada. → originou G-SURF-1/2/3.

### MR-4 — Atestação V2 Câmara de Proveniência
- `windi-seal-v2.html`: HTTP 200, hash live byte-idêntico ao declarado (`db37778c...`) — segunda atestação cruzada CCode↔Guardian do dia.
- Confirmado no código live: três veredictos (MOMENTO PRESERVADO / DEMONSTRAÇÃO / NÃO ENCONTRADO ⚠ com "Ausência de selo não prova falsidade"), disclaimer constitucional verbatim, `crypto.subtle` local, **zero** FormData/endpoints de upload — o media não sai do dispositivo.
- Estado `missing` está ligado ao render; condição exacta de disparo (API `ok:false` → missing, nunca demo) a confirmar em G-SURF-3.

### MR-5 — Media-detector existente
- Usa linguagem heurística (15× "confidence"/"probability"/"heuristic suspicion") e faz upload do ficheiro via FormData para `/detect-media/analyze` e `/reality-check/analyze`.
- Conclusão: órgão de **opinião probabilística**, não de prova. Não pode contaminar o fluxo de selagem (ver §4.1).

---

## 3. Gates G-SURF (estado)

| Gate | Descrição | Estado |
|---|---|---|
| G-SURF-1 | Estado (real/demo/não-encontrado) vive no veredicto, não em secção colapsada; demo nunca diz "confirmada" | ✅ Implementado na V2 (atestado MR-4) |
| G-SURF-2 | API `ok:false` nunca cai em mock; falha explícita em linguagem humana | ⚠ Implementado; condição de disparo a confirmar com teste real |
| G-SURF-3 | Measurement run dos 3 estados + câmara + áudio em Safari iOS e Chrome Android reais, com registo | ⏳ PENDENTE |
| G-SURF-4 | Contadores live (ex. "LEDGER: 56,288") só com dados reais da API, nunca fabricados | ⏳ A verificar na V2.1 (fetch `/api/receipts/health` existe; confirmar comportamento quando endpoint não existe) |
| G-SURF-5 | Fallback gracioso quando getUserMedia bloqueado (iframes de Artifacts, permissões negadas) | ✅ Parcial (catch → upload); testar em iframe real |

### Alçapão Safari iOS (correção de uma linha)
A cadeia de codecs só testa variantes `webm`; Safari grava `mp4` e pode rejeitar todas, fazendo o construtor `MediaRecorder` lançar erro. Vacina: se nenhum webm suportado, instanciar `MediaRecorder` **sem** mimeType (browser escolhe). Confirmar em iPhone real (G-SURF-3).

---

## 4. Doutrina emergente (candidata a selagem)

### 4.1 Separação Selo/Detector
O Selo é prova binária forense (registado/não registado). O Detector é opinião probabilística (heurísticas de geração IA). **Nunca no mesmo veredicto, nunca na mesma linguagem.** Dois botões, dois órgãos. Descende de "universal na ficção ≠ ambíguo na forense".

### 4.2 Soberania do media — "Selar o hash, não a foto"
O fluxo de selagem calcula SHA-256 no dispositivo; só o hash viaja. *"Ninguém viu o seu ficheiro; apenas o hash foi transmitido."* GDPR-friendly por construção, storage zero, diferenciador que concorrentes cloud-first não copiam sem se reconstruir. **Já implementado na V2 (MR-4).**

### 4.3 O que o selo afirma
Prova: existência no instante T + DID do selador + integridade desde então. **Não prova:** veracidade do conteúdo, local de captura, ausência de encenação, ausência de geração por IA. Disclaimer obrigatório em toda superfície. **Já implementado na V2.**

### 4.4 Taxonomia Tripartida de Selos (EXTENSÃO CONSTITUCIONAL — Human Dragon)

| Tipo | Afirma | Cor |
|------|--------|-----|
| **SELO-CAPTURA** | "Este ficheiro existia neste estado." | 🟢 Verde |
| **SELO-COMPOSIÇÃO** | "Esta obra foi criada por este DID." | 🟡 Ouro |
| **SELO-NARRATIVA** | "Esta narrativa foi publicada nesta forma." | 🟣 Púrpura |

- **SELO-CAPTURA:** câmara → hash imediato, sem edição. Peso probatório alto.
- **SELO-COMPOSIÇÃO:** obra editada/montada. Campo `type` + linhagem do material fonte.
- **SELO-NARRATIVA:** universo criativo (W-HIOS Cinema, Foundation, personagens fictícios). Não afirma existência real das entidades.

> **"Tudo pode ser selado. Nem tudo significa a mesma coisa."** — Human Dragon

**Documento:** `LEI-TAXONOMIA-TRIPARTIDA-SELOS.md` (CANDIDATE)

### 4.5 Tese Instamatic (Architect + Human Dragon)
O Verify não compete por tecnologia; compete por hábito cultural. "Quanto maior a abundância, maior o valor da origem." Objectivo: "Selaste isso?" como um dia se perguntou "Tens foto disso?". Consequência de design: a superfície de consumo (Artifacts/Canva/plataformas) pode preceder o backend — ensina o gesto; o Ledger liga depois. Dois trajes sobre o mesmo esqueleto: HUD tech para palco/pitch, Polaroid quente para massificação.

---

## 5. Sementes registadas
- **SEED-VERIFY-INSTAMATIC** — Verify como ritual de autoria distribuído por plataformas (Claude Artifacts, Canva Apps, GPT Store, bots). Protótipos do dia: widget Polaroid (sessão web), mockups Canva (3 ecrãs capturar→selar→revelar; candidato final por escolher), V1 Living Surface, V2.1 Câmara de Proveniência.
- **SEED-VERIFY-TERMINAIS** — selagem no ponto de cópia (scanners, copiadoras): "cartório digital no ponto de reprodução." Pós-massificação mobile.
- **SEED-VERIFY-EUAIACT** — Verify como conformidade verificável (Art. 50, transparência de conteúdo IA, vigor Ago 2026). Liga ao outreach LinkedIn activo.
- **SEED-STUDIO-COMENTARIO** — "anti-TikTok": comentário com cadeia de evidência; linhagem do material comentado faz parte da prova. W-HIOS aplicado ao quotidiano. Mesmo ADN de W-Travel/W-Journal.

---

## 5.1 O Funil Invertido (Human Dragon + Guardian, 11 Jun)

### Bloco de Sabedoria (candidato a Memory Loop)
> **"As pessoas raramente entram pela governança. Entram pelo uso.**
> **Ninguém começou a usar email porque adorava protocolos SMTP."**
> — Human Dragon

### Arquitectura do Funil
```
W-HIOS Cinema
      ↓
   Curiosidade (QR no final do episódio)
      ↓
   Verify ("Origem encontrada")
      ↓
   Studio (Capturar, Compor, Comentar)
      ↓
   DID (Identidade soberana)
      ↓
   Comunidade
      ↓
LAW / Compliance / Enterprise
```

### Corolário Estratégico
```
Cinema → porta de entrada
LAW    → destino institucional
Verify → ponte
DID    → identidade comum
```

### Economia da Curiosidade (Guardian)
- FREE tier custo marginal **zero**: hash local, 1 linha no Ledger, Ollama local
- Funil mensurável pelo próprio Ledger (sem Google Analytics)
- **Gate 0 é o primeiro dominó**: curioso que encontra `not_found` não volta

**Documento:** `WISDOM-BLOCK-CURIOSITY-FUNNEL.md` (CANDIDATE)

---

## 6. Decisões — Estado Final

| # | Decisão | Estado |
|---|---------|--------|
| 1 | **Gate 0:** suffix lookup + API→Ledger | ✅ SEALED `7A1A5282` |
| 2 | **Taxonomia Tripartida:** 3 seal types implementados | ✅ SEALED na V2.8 |
| 3 | **Auto-download + Exit Warning** | ✅ SEALED `28E0073B` |
| 4 | **Full Trilingual i18n (PT/DE/EN)** | ✅ SEALED `710243F1` |
| 5 | **Real Ledger Verify (4 estados)** | ✅ SEALED `FD9C54FB` |
| 6 | **Arc Seal** | ✅ SEALED `5A424A04` |
| 7 | **G-SURF-3:** Safari iOS + Chrome Android reais | ⏳ PENDENTE (dispositivos físicos) |

---

## 7. Artefactos produzidos neste arco

| Ficheiro | Descrição | Hash |
|----------|-----------|------|
| `/opt/windi/artifacts/verify-living-surface-v1.html` | V1 Living Surface (verificação) | `6f118d7b...` |
| `/opt/windi/artifacts/verify-living-surface-compact.html` | V1 compacta para Artifacts | `b9d30882...` |
| `/opt/windi/artifacts/windi-seal-v2.html` | V2.8 Full Arc (Real Verify) | `fd9c54fb3bd0ce0b` |
| `/opt/windi/docs/LEI-TAXONOMIA-TRIPARTIDA-SELOS.md` | Lei Constitucional | `afe65d0a29c2c7cc` |
| `/opt/windi/docs/WISDOM-BLOCK-CURIOSITY-FUNNEL.md` | Bloco de Sabedoria | (a calcular) |
| `/opt/windi/claudeWeb/GUARDIAN-REVIEW-VERIFY-SURFACE-20260611.md` | Esta nota | (pre-hash) |

---

*AI processes. Human decides. WINDI guarantees.*
*Guardian 🛡️ — 11 Jun 2026*
