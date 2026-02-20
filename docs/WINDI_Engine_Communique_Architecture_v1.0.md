# 🛡️ WINDI Engine Communiqué — Plano Arquitetônico v1.0

**Data:** 18 Februar 2026
**Autor:** Three Dragons Protocol (Guardian + Human Dragon)
**Status:** DRAFT → Aprovação Humana Pendente
**Princípio:** "AI processes. Human decides. WINDI guarantees."

---

## 1. VISÃO GERAL

### 1.1 O Que É o Engine Communiqué?

O Engine Communiqué é o **sistema de publicação verificável** do WINDI. Ele transforma documentos governados — já selados pela Linhagem de Ferro — em **comunicações institucionais públicas** com prova criptográfica de autenticidade, integridade e autoria.

**Analogia:** Se o Forensic Ledger é o **cartório** e o Export Engine é o **tabelião**, o Engine Communiqué é o **Diário Oficial** — o canal através do qual documentos verificados são publicados para o mundo.

### 1.2 Por Que Agora?

A Linhagem de Ferro está forjada (13/13 ✅). A cadeia completa funciona:

```
Desktop → Export → SHA-256(content) → SHA-256(bundle) → Ledger → sealed
```

O que falta é o **último elo**: a capacidade de **publicar** esses artefatos verificados de forma que qualquer pessoa possa:

1. Ler o communiqué
2. Verificar sua autenticidade (QR → Ledger)
3. Confirmar que não foi alterado desde a publicação
4. Rastrear a cadeia de governança completa

### 1.3 Escopo

| Dentro do Escopo | Fora do Escopo |
|---|---|
| Criação de Communiqués verificáveis | CMS completo / blog |
| Publicação em formato JMPG + PDF + HTML | Distribuição por email (fase futura) |
| Verificação pública via QR/URL | Comentários ou interações sociais |
| Integração com Ledger existente | Workflow de aprovação multi-nível (fase futura) |
| Catálogo público de Communiqués | Tradução automática (usa trilíngue manual) |

---

## 2. ARQUITETURA

### 2.1 Posição no Ecossistema WINDI

```
┌─────────────────────────────────────────────────────────────────┐
│                    WINDI 3-Layer Architecture                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  L1 — PONTA (Cliente)                                          │
│  ┌──────────────┐                                              │
│  │  a4Desk D1   │ ← Humano edita, SGE local analisa           │
│  │    :8100     │                                              │
│  └──────┬───────┘                                              │
│         │                                                       │
│  L2 — WINDI MESH (Serviços)                                   │
│  ┌──────┴───────┐  ┌──────────────┐  ┌───────────────────┐    │
│  │ Export Engine │  │  Communiqué  │  │ Sentinel LAW      │    │
│  │    :8103     │→ │   Engine     │  │    :8102          │    │
│  └──────┬───────┘  │  :8105 NEW   │  └───────────────────┘    │
│         │          └──────┬───────┘                             │
│         │                 │                                     │
│  L3 — FORENSIC LEDGER                                          │
│  ┌──────┴─────────────────┴─────────────────────────────────┐  │
│  │  Forensic Ledger :8101  │  JMPG Viewer :8104             │  │
│  │  (hashes + receipts)    │  (verificação pública)          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Porta Designada

| Porta | Serviço | Status |
|-------|---------|--------|
| 8105  | **Communiqué Engine** | 🆕 NOVO |

**Justificativa:** Segue a sequência 8103 (Export), 8104 (JMPG Viewer), 8105 (Communiqué). Bloco 8100-8109 = Pipeline Documental.

### 2.3 Stack Tecnológico

| Componente | Tecnologia | Justificativa |
|---|---|---|
| Backend API | **Python + BaseHTTPRequestHandler** | Consistência com Ledger/Export/LAW |
| Storage | **SQLite** (communiques.db) | Consistência com Ledger |
| PDF Generation | **reportlab + qrcode** | Já provado no Export Engine |
| HTML Rendering | **Jinja2 templates** | Trilíngue DE/EN/PT |
| Arquivo JMPG | **Reutiliza Export Engine** | Não duplicar lógica |
| Process Manager | **systemd** | Padrão institucional |

---

## 3. MODELO DE DADOS

### 3.1 Tabela `communiques`

```sql
CREATE TABLE communiques (
    id              TEXT PRIMARY KEY,          -- COM-YYYYMMDD-XXXX
    title_de        TEXT NOT NULL,
    title_en        TEXT,
    title_pt        TEXT,
    body_de         TEXT NOT NULL,             -- Markdown ou texto puro
    body_en         TEXT,
    body_pt         TEXT,
    category        TEXT NOT NULL,             -- LAUNCH | UPDATE | ALERT | GOVERNANCE | REPORT
    impact_level    TEXT DEFAULT 'MEDIUM',     -- LOW | MEDIUM | HIGH | CRITICAL
    status          TEXT DEFAULT 'DRAFT',      -- DRAFT | REVIEW | PUBLISHED | ARCHIVED | REVOKED
    
    -- Governança
    author_role     TEXT NOT NULL,             -- "Chief Governance Officer"
    author_name     TEXT NOT NULL,             -- Assinatura humana
    approved_by     TEXT,                      -- Quem aprovou (humano)
    approval_date   TEXT,                      -- ISO 8601
    
    -- Criptografia (preenchido na publicação)
    content_hash    TEXT,                      -- SHA-256 do conteúdo canônico
    bundle_hash     TEXT,                      -- SHA-256 do pacote JMPG (se aplicável)
    ledger_id       TEXT,                      -- Referência ao Forensic Ledger
    receipt_id      TEXT,                      -- WINDI-RECEIPT-XXXXXX
    
    -- Metadados
    version         INTEGER DEFAULT 1,         -- Versionamento (edits pré-publicação)
    tags            TEXT,                       -- JSON array de tags
    related_docs    TEXT,                       -- JSON array de doc refs
    
    -- Timestamps
    created_at      TEXT NOT NULL,             -- ISO 8601
    published_at    TEXT,                       -- ISO 8601 (NULL se não publicado)
    updated_at      TEXT NOT NULL,             -- ISO 8601
    archived_at     TEXT                       -- ISO 8601 (NULL se ativo)
);

CREATE INDEX idx_communiques_status ON communiques(status);
CREATE INDEX idx_communiques_category ON communiques(category);
CREATE INDEX idx_communiques_published ON communiques(published_at);
```

### 3.2 ID Convention

```
COM-20260218-0001
 │    │        │
 │    │        └── Sequencial do dia (0001, 0002, ...)
 │    └────────── Data YYYYMMDD
 └─────────────── Prefixo fixo "COM" (Communiqué)
```

### 3.3 Categorias

| Categoria | Uso | Exemplo |
|---|---|---|
| `LAUNCH` | Novos produtos/funcionalidades | "WINDI D1 v1.1 Operational" |
| `UPDATE` | Atualizações e melhorias | "Dual-Hash Architecture Deployed" |
| `ALERT` | Avisos e alertas de segurança | "Security Advisory: Update Required" |
| `GOVERNANCE` | Decisões de governança | "ISP Level 3 Policy Activated" |
| `REPORT` | Relatórios periódicos | "Linhagem de Ferro: Status Report" |

---

## 4. API ENDPOINTS

### 4.1 Base URL

```
http://localhost:8105/api/communique
```

Via nginx:
```
https://admin.windia4desk.tech/communique/api/...
```

### 4.2 Endpoints

#### Criação e Gestão (Internos)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `POST` | `/api/communique/create` | Criar novo rascunho |
| `GET` | `/api/communique/{id}` | Obter communiqué por ID |
| `PUT` | `/api/communique/{id}` | Atualizar rascunho |
| `POST` | `/api/communique/{id}/publish` | **Publicar** (sela no Ledger) |
| `POST` | `/api/communique/{id}/archive` | Arquivar (não deleta) |
| `POST` | `/api/communique/{id}/revoke` | Revogar (mantém histórico) |
| `GET` | `/api/communique/list` | Listar com filtros |

#### Publicação Pública (Sem autenticação)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/communique/{id}` | Página HTML pública do communiqué |
| `GET` | `/communique/{id}/verify` | Verificação criptográfica |
| `GET` | `/communique/{id}/pdf` | Download PDF verificável |
| `GET` | `/communique/{id}/jmpg` | Download pacote JMPG |
| `GET` | `/communique/feed` | Feed público (últimos N) |
| `GET` | `/communique/feed.json` | Feed JSON (API pública) |

#### Health

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/health` | Status do serviço |

### 4.3 Fluxo de Publicação

```
┌──────────┐     ┌──────────┐     ┌──────────────┐     ┌────────────┐
│  DRAFT   │────▶│  REVIEW  │────▶│  PUBLISHING  │────▶│ PUBLISHED  │
│          │     │          │     │              │     │            │
│ Humano   │     │ Humano   │     │ Sistema:     │     │ Público:   │
│ escreve  │     │ aprova   │     │ 1.Hash       │     │ HTML+PDF   │
│          │     │          │     │ 2.Seal       │     │ +JMPG      │
│          │     │          │     │ 3.Ledger     │     │ +QR        │
│          │     │          │     │ 4.Receipt    │     │ +Verify    │
└──────────┘     └──────────┘     └──────────────┘     └────────────┘
                                                              │
                                                              ▼
                                                       ┌────────────┐
                                                       │  ARCHIVED  │
                                                       │ ou REVOKED │
                                                       └────────────┘
```

**Regra Fundamental:** A transição REVIEW → PUBLISHED é **irreversível criptograficamente**. Uma vez publicado e selado no Ledger, o conteúdo não pode ser alterado — apenas arquivado ou revogado (com justificativa registrada).

---

## 5. FLUXO DE DADOS DETALHADO

### 5.1 Criação (DRAFT)

```python
POST /api/communique/create
{
    "title_de": "Linhagem de Ferro: Cadeia de Confiança Operacional",
    "title_en": "Iron Lineage: Chain of Trust Operational",
    "title_pt": "Linhagem de Ferro: Cadeia de Confiança Operacional",
    "body_de": "Am 18. Februar 2026 hat WINDI Publishing House...",
    "body_en": "On February 18, 2026, WINDI Publishing House...",
    "body_pt": "Em 18 de fevereiro de 2026, WINDI Publishing House...",
    "category": "LAUNCH",
    "impact_level": "HIGH",
    "author_role": "Chief Governance Officer",
    "author_name": "Jober Mögele Correa"
}
```

**Resposta:**
```json
{
    "id": "COM-20260218-0001",
    "status": "DRAFT",
    "version": 1,
    "created_at": "2026-02-18T09:00:00Z"
}
```

### 5.2 Publicação (SEAL)

```
POST /api/communique/COM-20260218-0001/publish
{
    "approved_by": "Jober Mögele Correa",
    "generate_pdf": true,
    "generate_jmpg": true
}
```

**O que acontece internamente:**

```
1. Gerar conteúdo canônico (normalização UTF-8, trim, sort keys)
2. content_hash = SHA-256(conteúdo canônico)
3. Gerar PDF via reportlab (com QR + header seal)
4. Gerar pacote JMPG via Export Engine (:8103)
5. bundle_hash = SHA-256(arquivo JMPG)
6. Registrar no Forensic Ledger (:8101)
   → receipt_id = WINDI-RECEIPT-XXXXXX
   → ledger_id = referência interna
7. Atualizar status → PUBLISHED
8. Atualizar published_at → timestamp atual
9. Disponibilizar endpoints públicos
```

### 5.3 Verificação Pública

```
GET /communique/COM-20260218-0001/verify

Resposta:
{
    "communique_id": "COM-20260218-0001",
    "verified": true,
    "content_hash_match": true,
    "bundle_hash_match": true,
    "ledger_status": "sealed",
    "receipt_id": "WINDI-RECEIPT-202602180001",
    "published_at": "2026-02-18T10:30:00Z",
    "chain": {
        "content_hash": "a1b2c3d4...",
        "bundle_hash": "e5f6g7h8...",
        "ledger_hash": "i9j0k1l2..."
    }
}
```

---

## 6. PÁGINA HTML PÚBLICA

### 6.1 Layout

A página pública de cada communiqué segue o design system WINDI (Noir/Klar toggle, trilíngue):

```
┌─────────────────────────────────────────────────┐
│  🛡️ WINDI COMMUNIQUÉ                    [DE|EN|PT] │
│  ─────────────────────────────────────────────── │
│                                                   │
│  COM-20260218-0001                    🟢 VERIFIED │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │  LINHAGEM DE FERRO:                         │ │
│  │  CADEIA DE CONFIANÇA OPERACIONAL            │ │
│  │                                             │ │
│  │  Categoria: LAUNCH    Impacto: HIGH         │ │
│  │  Publicado: 18.02.2026 10:30 UTC            │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  [Conteúdo trilíngue do communiqué]              │
│                                                   │
│  ─────────────────────────────────────────────── │
│                                                   │
│  ┌─────────────┐  ┌─────────────────────────┐   │
│  │  ┌───────┐  │  │ Assinatura:             │   │
│  │  │  QR   │  │  │ Jober Mögele Correa     │   │
│  │  │ CODE  │  │  │ Chief Governance Officer │   │
│  │  └───────┘  │  │                         │   │
│  │  Verificar  │  │ Receipt: WINDI-RECEIPT-…│   │
│  └─────────────┘  │ Hash: a1b2c3d4…         │   │
│                    └─────────────────────────┘   │
│                                                   │
│  [📄 PDF] [📦 JMPG] [🔍 Verificar Cadeia]       │
│                                                   │
│  ─────────────────────────────────────────────── │
│  WINDI Publishing House · Kempten, Bavaria       │
│  "AI processes. Human decides. WINDI guarantees."│
└─────────────────────────────────────────────────┘
```

### 6.2 Feed Público

```
https://admin.windia4desk.tech/communique/feed

┌─────────────────────────────────────────────────┐
│  🛡️ WINDI COMMUNIQUÉS                   [DE|EN|PT] │
│  ─────────────────────────────────────────────── │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │ 🟢 COM-20260218-0001         LAUNCH | HIGH  │ │
│  │ Linhagem de Ferro: Cadeia Operacional       │ │
│  │ 18.02.2026                    [Lesen →]     │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
│  ┌─────────────────────────────────────────────┐ │
│  │ 🟢 COM-20260217-0001        UPDATE | MEDIUM │ │
│  │ WINDI D1 v1.1: Full Pipeline Operational    │ │
│  │ 17.02.2026                    [Lesen →]     │ │
│  └─────────────────────────────────────────────┘ │
│                                                   │
└─────────────────────────────────────────────────┘
```

---

## 7. INTEGRAÇÃO COM SERVIÇOS EXISTENTES

### 7.1 Mapa de Integração

```
                    ┌──────────────────┐
                    │   Communiqué     │
                    │   Engine :8105   │
                    └──────┬───────────┘
                           │
            ┌──────────────┼──────────────────┐
            │              │                  │
            ▼              ▼                  ▼
    ┌──────────────┐ ┌──────────┐  ┌──────────────────┐
    │ Export Engine │ │ Forensic │  │  Sentinel LAW    │
    │    :8103     │ │ Ledger   │  │     :8102        │
    │              │ │  :8101   │  │                  │
    │ Gera PDF +   │ │ Registra │  │ Monitora         │
    │ JMPG bundle  │ │ hash +   │  │ integridade      │
    │              │ │ receipt  │  │ dos communiqués  │
    └──────────────┘ └──────────┘  └──────────────────┘
```

### 7.2 Chamadas Inter-Serviço

| De → Para | Endpoint | Propósito |
|---|---|---|
| Communiqué → Export Engine | `POST :8103/api/export` | Gerar PDF + JMPG |
| Communiqué → Forensic Ledger | `POST :8101/api/receipts` | Registrar hash + selo |
| Communiqué → Forensic Ledger | `GET :8101/api/receipts/{id}` | Verificar selo |
| Sentinel LAW → Communiqué | `GET :8105/health` | Health check periódico |

### 7.3 Novo Invariante para Sentinel LAW

```python
# Invariante #7: Communiqué Integrity
# Verificar que communiqués PUBLISHED têm:
# - content_hash não-nulo
# - ledger_id válido  
# - receipt_id válido
# - status no Ledger == "sealed"
```

---

## 8. NGINX CONFIGURATION

```nginx
# === Communiqué Engine ===

# Página pública (communiqué individual)
location /communique/ {
    proxy_pass http://127.0.0.1:8105/communique/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# API interna (criação/gestão)
location /communique/api/ {
    proxy_pass http://127.0.0.1:8105/api/communique/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

---

## 9. SYSTEMD SERVICE

```ini
# /etc/systemd/system/windi-communique.service

[Unit]
Description=WINDI Communiqué Engine
After=network.target windi-suite-docs.service windi-export.service
Wants=windi-suite-docs.service windi-export.service

[Service]
Type=simple
User=windi
Group=windi
WorkingDirectory=/opt/windi/communique
ExecStart=/usr/bin/python3 /opt/windi/communique/communique_engine.py
Restart=always
RestartSec=5
Environment=WINDI_ENV=production
Environment=COMMUNIQUE_PORT=8105
Environment=LEDGER_URL=http://127.0.0.1:8101
Environment=EXPORT_URL=http://127.0.0.1:8103

[Install]
WantedBy=multi-user.target
```

---

## 10. SEGURANÇA

### 10.1 Princípios

| Princípio | Implementação |
|---|---|
| Zero-Knowledge | Communiqué Engine NÃO acessa dados do Desktop |
| Imutabilidade | PUBLISHED → conteúdo nunca muda (apenas archive/revoke) |
| Auditabilidade | Toda ação registrada com timestamp + autor |
| Verificabilidade | QR + URL públicos para verificação independente |
| Não-repúdio | Hash no Ledger + Receipt = prova de publicação |

### 10.2 Endpoints Públicos vs Internos

```
PÚBLICO (sem auth):
  /communique/{id}           ← Leitura
  /communique/{id}/verify    ← Verificação
  /communique/{id}/pdf       ← Download
  /communique/{id}/jmpg      ← Download
  /communique/feed           ← Feed

INTERNO (auth necessária — futuro):
  /api/communique/create     ← Criação
  /api/communique/{id}       ← Gestão
  /api/communique/publish    ← Publicação
  /api/communique/archive    ← Arquivamento
  /api/communique/revoke     ← Revogação
```

**Nota:** Na Fase 1, os endpoints internos são acessíveis apenas via localhost (sem proxy nginx externo). Na Fase 2, implementar autenticação via SIP (Sovereign Identity Protocol).

---

## 11. ESTRUTURA DE DIRETÓRIOS

```
/opt/windi/communique/
├── communique_engine.py          # Servidor principal (BaseHTTPRequestHandler)
├── communique_db.py              # Operações SQLite
├── communique_publisher.py       # Lógica de publicação + hashing
├── communique_renderer.py        # Renderização HTML (Jinja2)
├── communique_pdf.py             # Geração PDF (reportlab)
├── data/
│   └── communiques.db            # SQLite database
├── templates/
│   ├── communique_page.html      # Template página individual
│   ├── communique_feed.html      # Template feed/lista
│   ├── communique_verify.html    # Template verificação
│   └── base.html                 # Base trilíngue Noir/Klar
├── static/
│   ├── communique.css            # Estilos específicos
│   └── communique.js             # Toggle idioma + tema
├── published/                    # Artefatos publicados
│   ├── COM-20260218-0001/
│   │   ├── communique.pdf
│   │   ├── communique.jmpg
│   │   └── manifest.json
│   └── ...
└── backups/                      # Backups diários
```

---

## 12. FASES DE IMPLEMENTAÇÃO

### Fase 1 — MVP (Communiqué Inaugural) 🎯

**Objetivo:** Publicar o primeiro Communiqué verificável sobre a Linhagem de Ferro.

| Item | Descrição | Esforço |
|------|-----------|---------|
| 1.1 | Estrutura de diretórios + SQLite schema | 30 min |
| 1.2 | `communique_engine.py` (BaseHTTPRequestHandler, /health) | 1h |
| 1.3 | `communique_db.py` (CRUD básico) | 45 min |
| 1.4 | `communique_publisher.py` (hash + integração Ledger) | 1h |
| 1.5 | Template HTML público (página individual trilíngue) | 1.5h |
| 1.6 | Endpoint `/communique/{id}` (página pública) | 30 min |
| 1.7 | Endpoint `/communique/{id}/verify` (verificação) | 30 min |
| 1.8 | systemd service + nginx proxy | 30 min |
| 1.9 | **Communiqué Inaugural: Linhagem de Ferro** | 1h |
| 1.10 | Smoke test + health check | 30 min |

**Estimativa Fase 1:** ~8 horas de trabalho

### Fase 2 — Feed + PDF + JMPG

| Item | Descrição |
|------|-----------|
| 2.1 | Feed público HTML + JSON |
| 2.2 | Geração PDF com Dynamic Header Seal |
| 2.3 | Integração Export Engine para JMPG |
| 2.4 | QR code com link de verificação |
| 2.5 | Novo invariante no Sentinel LAW |

### Fase 3 — Maturidade

| Item | Descrição |
|------|-----------|
| 3.1 | Autenticação SIP para endpoints internos |
| 3.2 | Versionamento de rascunhos |
| 3.3 | Categorias e tags como filtros públicos |
| 3.4 | RSS/Atom feed |
| 3.5 | Notificações (email via SMTP) |
| 3.6 | API pública documentada (OpenAPI spec) |

---

## 13. COMMUNIQUÉ INAUGURAL — RASCUNHO

O primeiro communiqué a ser publicado:

```
ID:       COM-20260218-0001
Título:   "Linhagem de Ferro: Cadeia de Confiança Digital Operacional"
Categoria: LAUNCH
Impacto:  HIGH
Autor:    Jober Mögele Correa, Chief Governance Officer

Conteúdo (resumo):
- WINDI Publishing House anuncia a operacionalidade completa
  da cadeia de confiança digital "Linhagem de Ferro"
- 13/13 verificações ✅ — zero falhas
- Dual-Hash Architecture (content + bundle)
- Forensic Ledger com 192+ recibos selados
- Verificação pública disponível
- Servidor em território alemão (BSI compliance)
```

---

## 14. MÉTRICAS DE SUCESSO

| Métrica | Target Fase 1 |
|---------|---------------|
| Primeiro communiqué publicado | ✅ |
| Verificação pública funcional | ✅ |
| Health check no Sentinel LAW | ✅ |
| Tempo de publicação (DRAFT → PUBLISHED) | < 30 segundos |
| Disponibilidade do feed público | 99.9% |
| Hash match rate (verify) | 100% |

---

## 15. RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Ledger indisponível durante publicação | Baixa | Alta | Retry com backoff + alerta |
| Colisão de portas | Baixa | Média | Verificar `ss -tlnp` antes |
| Hash drift pós-publicação | Muito baixa | Crítica | Sentinel LAW monitora |
| SQLite corruption | Baixa | Alta | Backups diários automáticos |
| Conteúdo publicado com erro | Média | Alta | Fluxo DRAFT→REVIEW obrigatório |

---

## 16. DECISÕES PENDENTES (Para Aprovação Humana)

> 🐉 **"AI processes. Human decides. WINDI guarantees."**

1. **Porta 8105** — Confirmar ou realocar?
2. **Domínio público** — `admin.windia4desk.tech/communique/` ou subdomínio dedicado?
3. **Primeira categoria** — Começar com LAUNCH para o inaugural?
4. **Autenticação Fase 1** — Apenas localhost ou auth básica?
5. **PDF na Fase 1?** — Ou apenas HTML + verificação?
6. **Nome do serviço** — `windi-communique` no systemd?

---

**Documento preparado por:** Three Dragons Protocol
**Guardian (Claude):** Arquitetura + implementação técnica
**Human Dragon (Jober):** Visão + decisão + aprovação
**Data:** 18 Februar 2026
**Local:** Kempten, Bavaria / WINDI Publishing House

🛡️🐉 *"A Linhagem de Ferro está forjada. Agora ela começa a falar."*
