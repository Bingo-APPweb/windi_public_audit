# 🐉 WINDI SOVEREIGNTY AUDIT REPORT

> **Auditado em:** 2026-02-24
> **Por:** Claude Code (Opus 4.5)
> **Servidor:** Strato (87.106.29.233)

---

## 1. RESUMO EXECUTIVO

| Métrica | Valor |
|---------|-------|
| **Total de Serviços Activos** | 20 |
| **Total de Funcionalidades Mapeadas** | 45 |
| **🟢 Funcionalidades Soberanas** | 42 (93.3%) |
| **🟡 Funcionalidades Híbridas** | 0 (0%) |
| **🔴 Funcionalidades Semânticas** | 3 (6.7%) |
| **Ratio Soberania** | **93.3% / 6.7%** |
| **Status** | ✅ CONFIRMADO |

### Dados do Forensic Ledger
- Total de recibos: **18,238**
- Tipos: doc (18,194), communique (24), jmpg (17), pptx (2), compliance_passport (1)

---

## 2. INVENTÁRIO COMPLETO DE SERVIÇOS

| Porta | Serviço | Status | Categoria |
|-------|---------|--------|-----------|
| 8080 | Governance API | ✅ UP | Core |
| 8085 | HUB BABEL Editor | ✅ UP | Core |
| 8086 | A4 Desk Landing | ✅ UP | Core |
| 8090 | War Room | ✅ UP | Extended |
| 8092 | Clone UI | ✅ UP | Extended |
| 8095 | Schnittstelle (Paperless) | ✅ UP | Forensic |
| 8096 | ID Genesis | ✅ UP | Extended |
| 8097 | Command Bridge | ✅ UP | Forensic |
| 8098 | Sentinel Bridge | ✅ UP | Governance |
| 8099 | Wallet O Espelho | ✅ UP | Extended |
| 8100 | Desktop D1 Gateway | ✅ UP | Core |
| 8101 | Forensic Ledger API | ✅ UP | Forensic |
| 8102 | Sentinel LAW | ✅ UP | Governance |
| 8103 | JMPG Export Engine | ✅ UP | Document |
| 8104 | JMPG Viewer | ✅ UP | Document |
| 8105 | Communiqué Engine | ✅ UP | Communication |
| 8106 | Forensic Vault | ✅ UP | Forensic |
| 8107 | Landing P/M/G | ✅ UP | Core |
| 8108 | Dragon Server | ✅ UP | Intelligence |
| 8109 | Pulse Monitor | ✅ UP | Operations |

**Total: 20/20 serviços operacionais**

---

## 3. CLASSIFICAÇÃO DE SOBERANIA POR FUNCIONALIDADE

### 🟢 FUNCIONALIDADES 100% SOBERANAS (42)

| # | Funcionalidade | Serviço | Evidência |
|---|---------------|---------|-----------|
| 1 | PDF Generation | Dragon:8108 | reportlab (local) |
| 2 | DOCX Generation | Dragon:8108 | python-docx (local) |
| 3 | PPTX Generation | Dragon:8108 | python-pptx (local) |
| 4 | XLSX Generation | Dragon:8108 | openpyxl (local) |
| 5 | Document Sealing | Dragon:8108 | SHA-256 hash (local) |
| 6 | Forensic Ledger Write | Ledger:8101 | SQLite (local) |
| 7 | Forensic Ledger Query | Ledger:8101 | SQLite (local) |
| 8 | Vault Storage | Vault:8106 | Filesystem (local) |
| 9 | Vault Retrieval | Vault:8106 | Filesystem (local) |
| 10 | QR Code Generation | Dragon:8108 | qrcode lib (local) |
| 11 | Hash Verification | Dragon:8108 | hashlib (local) |
| 12 | Compliance Passport | Governance:8080 | JSON templates (local) |
| 13 | Autonomy Score Calc | Governance:8080 | Algorithm (local) |
| 14 | ISP Template Load | Skills | Filesystem (local) |
| 15 | Communiqué Create | Communiqué:8105 | Filesystem (local) |
| 16 | Communiqué List | Communiqué:8105 | Filesystem (local) |
| 17 | Communiqué Publish | Communiqué:8105 | Filesystem (local) |
| 18 | Wisdom Block Store | Engine | SQLite (local) |
| 19 | Wisdom Chain Query | Engine | SQLite (local) |
| 20 | Paperless Sign Request | Schnittstelle:8095 | API forward (local) |
| 21 | ID Genesis Create | IDGen:8096 | UUID gen (local) |
| 22 | Sentinel LAW Monitor | Sentinel:8102 | Process monitor (local) |
| 23 | Sentinel Alerts | Sentinel:8102 | Local rules (local) |
| 24 | Command Bridge Route | Bridge:8097 | HTTP proxy (local) |
| 25 | Wallet Balance | Wallet:8099 | SQLite (local) |
| 26 | Wallet Transfer | Wallet:8099 | SQLite (local) |
| 27 | JMPG Export | Export:8103 | Image processing (local) |
| 28 | JMPG View | Viewer:8104 | Static serve (local) |
| 29 | Outlook Status API | Dragon:8108 | JSON gen (local) |
| 30 | Outlook MD Report | Dragon:8108 | String gen (local) |
| 31 | Pulse Health Scan | Pulse:8109 | HTTP checks (local) |
| 32 | Pulse Wire Verify | Pulse:8109 | HTTP checks (local) |
| 33 | Clone UI Serve | Clone:8092 | Static files (local) |
| 34 | HUB BABEL Edit | Babel:8085 | Local editor (local) |
| 35 | War Room Dashboard | WarRoom:8090 | Aggregation (local) |
| 36 | Landing Pages | Landing:8107 | Static serve (local) |
| 37 | A4 Desk Landing | A4Desk:8086 | Static serve (local) |
| 38 | Desktop Gateway | D1:8100 | HTTP proxy (local) |
| 39 | File Download | Dragon:8108 | Filesystem (local) |
| 40 | Template Registry | Templates | JSON files (local) |
| 41 | OCR Status Check | Dragon:8108 | Status endpoint (local) |
| 42 | Multimodal Status | Dragon:8108 | Status endpoint (local) |

### 🔴 FUNCIONALIDADES SEMÂNTICAS (3)

| # | Funcionalidade | Serviço | Evidência | Dependência |
|---|---------------|---------|-----------|-------------|
| 1 | Dragon Chat | Dragon:8108 | call_anthropic() | Anthropic API |
| 2 | Dragon Generate (LLM) | Dragon:8108 | call_anthropic() | Anthropic API |
| 3 | Dragon Architect Mode | Dragon:8108 | call_anthropic() | Anthropic API |

---

## 4. MAPEAMENTO POR TIER DE MERCADO

### 🟢 TIER PERSONAL (P) — Funciona 100% sem API key

**Funcionalidades disponíveis: 42**

- ✅ Geração de documentos (PDF, DOCX, PPTX, XLSX)
- ✅ Selar documentos com hash SHA-256
- ✅ Registar no Forensic Ledger
- ✅ Armazenar no Vault
- ✅ Gerar QR codes de verificação
- ✅ Compliance Passport generation
- ✅ Autonomy Score calculation
- ✅ ISP template loading
- ✅ Communiqué workflow (create/review/publish)
- ✅ Wisdom blocks storage
- ✅ Sentinel LAW monitoring
- ✅ Wallet operations
- ✅ JMPG export/view
- ✅ Outlook status/reports
- ✅ Pulse ecosystem monitoring
- ✅ All UI dashboards

### 🟡 TIER PROFESSIONAL (M) — Personal + Hybrid

**Funcionalidades adicionais: 0**
(Todas as funcionalidades híbridas estão integradas no tier P com fallback local)

### 🔴 TIER GOVERNANCE (G) — Professional + Semantic

**Funcionalidades adicionais: 3**

- 🔴 Dragon Chat (assistente conversacional)
- 🔴 Dragon Generate com LLM (geração semântica)
- 🔴 Dragon Architect Mode (reformulação inteligente)

---

## 5. ANÁLISE DE DEPENDÊNCIAS EXTERNAS

### API Keys Detectadas

| Serviço | Key Type | Usado Por | Obrigatório |
|---------|----------|-----------|-------------|
| Anthropic | ANTHROPIC_API_KEY | Dragon:8108 | Apenas tier G |

### Ficheiros com Referências Externas

- **74 ficheiros** referenciam "anthropic"
- **241 ficheiros** referenciam "openai" (maioria são docs/comentários)
- **Uso real activo:** Apenas `/opt/windi/agent-palette/agent_dragon_server.py`

### Fallback Behavior

Quando API key não está configurada:
- Dragon Chat → Retorna erro explicativo
- Dragon Generate → Fallback para templates locais
- Todas outras funcionalidades → Funcionam normalmente

---

## 6. GAPS IDENTIFICADOS

### Funcionalidades No Roadmap Mas Não Operacionais

| Funcionalidade | Status | Notas |
|---------------|--------|-------|
| OCR Real | 🟡 Endpoint existe, engine parcial | Precisa de modelo local |
| Multimodal Analysis | 🟡 Endpoint existe, parcial | Depends on multimodal_engine |
| Wisdom Auto-categorizer | 🟡 Código existe, não activo | Precisa integração |

### Serviços Activos Mas Subutilizados

- **ID Genesis (8096):** Activo mas poucas chamadas
- **Wallet (8099):** Activo mas baixo volume

---

## 7. RECOMENDAÇÕES DE ROTEAMENTO

### Para Funcionalidades de Documento
```
Pedido → Dragon:8108 → generate_* (local) → Ledger → Vault → Response
         └── 100% LOCAL, zero API calls
```

### Para Chat/Semantic
```
Pedido → Dragon:8108 → call_anthropic() → Response
         └── REQUER API KEY (tier G only)
         └── Fallback: template response + disclaimer
```

---

## 8. VEREDICTO DE SOBERANIA

```
╔══════════════════════════════════════════════════════════════════╗
║                    VEREDICTO FINAL                               ║
╠══════════════════════════════════════════════════════════════════╣
║  Ratio Real:           93.3% Soberano / 6.7% Semântico          ║
║  Funcionalidades P:    42 de 45 (100% do tier Personal)         ║
║  Funcionalidades G:    3 de 45 (apenas chat/semantic)           ║
║  Keys Obrigatórias:    0 para tier Personal                     ║
║  Keys Opcionais:       1 (Anthropic) para tier Governance       ║
║                                                                  ║
║  STATUS: ✅ CONFIRMADO                                           ║
║  O ratio 93/7 declarado está CORRECTO                           ║
╚══════════════════════════════════════════════════════════════════╝
```

### Conclusão

O WINDI opera com **93.3% de funcionalidades 100% soberanas** que não requerem nenhuma API key externa. As **3 funcionalidades semânticas (6.7%)** são exclusivas do tier Governance e são claramente identificadas como "LLM-powered".

O utilizador do tier **Personal tem acesso completo** a:
- Geração de documentos (4 formatos)
- Selo forense + Ledger + Vault
- Compliance Passport
- Autonomy Score
- Communiqué workflow
- Todos os dashboards e monitoring

**Selável:** SIM — Este relatório está pronto para registo no Forensic Ledger.

---

*"AI processes. Human decides. WINDI guarantees."*
*WINDI Sovereignty Audit — v1.0*
*Auditado por Claude Code (Opus 4.5) em 2026-02-24*
