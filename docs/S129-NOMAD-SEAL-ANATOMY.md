# §129 — Anatomia do Produto

**WINDI Nomad Seal** — PWA + Voice + Workspace Retention Layer
**Data:** 05 Abril 2026
**Commit:** `054091e`
**Tag:** `W-VD-CUT-001-S129`

---

## DNA do Produto

```
Entrada: Voice (Telegram) | PWA (Browser) | API (Parceiro)
    ↓
Workspace: 30 dias editável (Tesoura, MARIA, JOE)
    ↓
Decisão: Humano clica "Seal" (I9)
    ↓
Saída: Ledger (hash eterno) + Vault (ficheiro permanente)
```

---

## Componentes Construídos

| Componente | Path | Função |
|------------|------|--------|
| **PWA Upload** | `/opt/windi/nomad-pwa/` | Interface mobile para upload directo |
| **Voice Handler** | `/opt/windi/nomad-bot/handlers/voice.py` | Whisper transcription → MARIA |
| **Vault Archive** | `/opt/windi/vd-cut/vd_cut_server.py` | `archive_to_vault()` após seal |
| **Nginx Route** | `/nomad-upload/` | Acesso público à PWA |
| **DID Chain** | PWA init() | URL → Travel → Law → Cookie → Auto |

---

## PWA — Ficheiros

```
/opt/windi/nomad-pwa/
├── index.html      (24KB)  Interface completa
├── manifest.json   (577B)  PWA manifest
├── sw.js           (1.2KB) Service worker
├── icon-192.png    (547B)  App icon
├── icon-512.png    (1.9KB) App icon
└── icon.svg        (301B)  Source vector
```

**URL:** `https://windi-domain.com/nomad-upload/`

---

## Voice Flow

```
Telegram Voice → NOMAD-BOT → Whisper API → Texto → MARIA
                    ↓
              (áudio nunca persiste — §122.4)
```

---

## Retention Layer

| Fase | Local | Retenção | Editável |
|------|-------|----------|----------|
| Intake | `/media/vd-cut/incoming/` | 30 dias | ✅ |
| Export | `/media/vd-cut/exports/` | 30 dias | ✅ |
| Sealed | `/forensic-vault/vd-cut/` | ∞ | ❌ |

```python
ORIGINAL_RETENTION_HOURS = 720   # 30 dias
SEALED_RETENTION_DAYS = 30
```

---

## Invariantes Respeitados

| Invariante | Aplicação |
|------------|-----------|
| **I9** | Humano clica "Seal" — nunca auto |
| **I11** | Hash no Ledger + Ficheiro no Vault |
| **G3** | Upload ≠ Compromisso (30 dias para decidir) |

---

## Endpoints Afectados

| Endpoint | Serviço | Alteração |
|----------|---------|-----------|
| `POST /vd-cut/intake` | VD-CUT | Campos: `video`, `did` |
| `POST /vd-cut/job/create` | VD-CUT | Campos: `source_asset`, `in_point`, `out_point` |
| `POST /vd-cut/seal` | VD-CUT | +`archive_to_vault()` |
| `GET /nomad-upload/*` | Nginx | Nova rota PWA |

---

## Impacto Estratégico

| Antes | Depois |
|-------|--------|
| Upload = Compromisso | Upload = Exploração |
| Seal imediato | 30 dias de decisão |
| Sistema notarial | Sistema criativo + soberano |
| Telegram = ficheiro | Telegram = interface |

---

## Integração Ecossistema

```
NOMAD-BOT ──┬── Voice → MARIA
            └── Link → PWA → VD-CUT → Ledger
                              ↓
                           Vault
                              ↓
                    Verify Public
```

---

## Git

```
Commits:
  nomad-bot:  7305aac  (voice handler)
  main:       054091e  (PWA + VD-CUT + Retention)

Tag: W-VD-CUT-001-S129

Push: ✅ GitHub
```

---

## Interpretação Canónica

> **"Entre criação e verdade, existe um espaço onde o humano decide."**

§129 introduz a **camada de soberania temporal** — o primeiro buffer entre input e compromisso imutável no ecossistema WINDI.

---

**Liga IA+H · Kempten, Bavaria · 05 Abril 2026**

*"AI processes. Human decides. WINDI guarantees."*
