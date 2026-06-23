# W-DID-CANON-001 — DID Gate Constitutional Canon

**Status:** CANDIDATE
**Version:** 0.1.0
**Created:** 2026-06-23
**Author:** Liga IA+H
**Invariants:** I1, I9, I11, I17, §194, §299

---

## 1. Princípio Fundamental

> *"A identidade soberana é única. Os portões podem ser muitos."*

Um utilizador possui **um único DID**. Este DID pode ser apresentado em múltiplos portões:

```
did:windi:dragon-001
        ↓
   ┌────┴────┬────────┬────────┐
   │         │        │        │
Enterprise Desktop  Travel   Farm
  Gate      Gate     Gate    Gate
```

Todos os portões reconhecem o mesmo DID. Nenhum portão cria identidade própria.

---

## 2. Evolução Constitucional — Playground

> *"WINDI é para todos. Playground: sem DID. Posse soberana: com DID."*

### 2.1 Modelo Anterior (pré-Playground)

```
Entrada → DID obrigatório → Uso
```

### 2.2 Modelo Actual (pós-23 Jun 2026)

```
Playground (sem DID)
        ↓
    Criação
        ↓
    Claim (ponte)
        ↓
DID Genesis (com DID)
        ↓
    Posse Soberana
```

**Regra:** O Playground é constitucional. Criar sem identidade é permitido. A identidade surge no momento da **Claim**, não antes.

### 2.3 Corolário

A frase:

> *"WINDI é para todos. Funciona apenas com DID."*

deve ser actualizada para:

> *"WINDI é para todos. Criar: livre. Possuir: com DID."*

---

## 3. Estados de Identidade

| Estado | Descrição | DID | Session |
|--------|-----------|-----|---------|
| `ANONYMOUS` | Utilizador sem rastro | ❌ | ❌ |
| `PLAYGROUND` | Criando no Workbench | ❌ | ⚠️ (efémera) |
| `CLAIM_ELIGIBLE` | 3+ edits, pode reivindicar | ❌ | ⚠️ |
| `DID_CREATED` | DID gerado, não autenticado | ✅ | ❌ |
| `AUTHENTICATED` | DID + passphrase verificados | ✅ | ✅ |
| `ACTIVE_SESSION` | Sessão válida, navegando | ✅ | ✅ |

**Transições válidas:**

```
ANONYMOUS → PLAYGROUND → CLAIM_ELIGIBLE → DID_CREATED → AUTHENTICATED → ACTIVE_SESSION
                                              ↑
                              (criação directa em /wallet/)
```

---

## 4. Vocabulário Canónico

### 4.1 Frases de Interface

| Conceito | PT-BR | EN | DE |
|----------|-------|----|----|
| **Título do Gate** | Tua identidade soberana | Your sovereign identity | Deine souveräne Identität |
| **Subtítulo** | Para aceder, precisas do teu WINDI DID | To access, you need your WINDI DID | Um zuzugreifen, benötigst du deine WINDI DID |
| **Campo DID** | Tua identidade | Your identity | Deine Identität |
| **Campo Passphrase** | Passphrase | Passphrase | Passphrase |
| **Botão Entrar** | ENTRAR | ENTER | EINTRETEN |
| **Link Criar** | Ainda não tens identidade? Cria uma → | No identity yet? Create one → | Noch keine Identität? Erstelle eine → |
| **Princípio** | WINDI é para todos. Criar: livre. Possuir: com DID. | WINDI is for everyone. Create: free. Own: with DID. | WINDI ist für alle. Erstellen: frei. Besitzen: mit DID. |

### 4.2 Frases Filosóficas (opcionais)

| PT-BR | EN | DE |
|-------|----|----|
| Um cérebro não funciona sem alma. A alma entra pelo DID. | A brain doesn't work without soul. The soul enters through DID. | Ein Gehirn funktioniert nicht ohne Seele. Die Seele tritt durch DID ein. |

---

## 5. Campos Canónicos

### 5.1 Ordem Visual (obrigatória)

```
┌─────────────────────────────────────┐
│  [Logo/Ícone do Serviço]            │
│                                     │
│  Título do Gate                     │
│  Subtítulo explicativo              │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ Tua identidade              │    │
│  │ did:windi:_______________   │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ Passphrase                  │    │
│  │ ••••••••••••••   [mostrar]  │    │
│  └─────────────────────────────┘    │
│                                     │
│  [ ENTRAR ↗ ]                       │
│                                     │
│  Ainda não tens identidade? →       │
│                                     │
│  ─────────────────────────────────  │
│  Como começar                       │
│  1. Cria tua identidade em /wallet/ │
│  2. Escolhe teu nome soberano       │
│  3. Insere nome e passphrase acima  │
│  4. VERA reconhece-te               │
└─────────────────────────────────────┘
```

### 5.2 Funcionalidades Obrigatórias

- [ ] Toggle mostrar/ocultar passphrase
- [ ] Link para `/wallet/` (criação de DID)
- [ ] Validação de formato `did:windi:*`
- [ ] Feedback de erro trilíngue
- [ ] Menção a VERA (reconhecimento)

---

## 6. DID Session Layer

### 6.1 Keys Canónicas (localStorage)

| Key | Valor | Propósito |
|-----|-------|-----------|
| `windi-did` | `did:windi:xxx` | Identificador persistente |
| `windi-did-session` | JWT/token | Sessão autenticada |
| `windi-did-name` | `dragon-001` | Nome legível (opcional) |

### 6.2 Keys Canónicas (sessionStorage)

| Key | Valor | Propósito |
|-----|-------|-----------|
| `windi-did-temp` | `did:windi:xxx` | DID temporário (pre-auth) |

### 6.3 Anti-patterns

- ❌ `windi_did` (underscore)
- ❌ `did_session` (sem prefixo windi)
- ❌ `identity` (muito genérico)
- ❌ Armazenar passphrase em qualquer storage

### 6.4 Relação com W-FRONTEND-CANON-001

```
windi-lang     → Língua (FRONTEND)
windi-theme    → Tema (FRONTEND)
windi-did      → Identidade (DID)
windi-did-session → Sessão (DID)
```

Todas as keys seguem o padrão `windi-*` com hífen.

---

## 7. Relação Gate ↔ Serviço

### 7.1 Arquitectura

```
Vestíbulo (público)     →  /enterprise/
                              ↓
Gate (autenticação)     →  /enterprise/desk/ [DID Gate]
                              ↓
Serviço (protegido)     →  W-Enterprise-001 :8150
```

### 7.2 Regra de Separação

- **Vestíbulo:** Público, sem DID, explica o serviço
- **Gate:** Pede DID, valida, redireciona
- **Serviço:** Assume DID válido, opera

O Gate NUNCA é o serviço. O Gate é a **porta**.

---

## 8. Portões Conhecidos

| Serviço | Vestíbulo | Gate | Porta |
|---------|-----------|------|-------|
| W-Enterprise-001 | `/enterprise/` | `/enterprise/desk/` | :8150 |
| Desktop GEN7 | — | `/desktop/` | :8119 |
| W-Travel-001 | `/travel/` | `/travel/workspace/` | :8126 |
| W-Farm-001 | — | `/farm/` | :8201 |
| W-Wallet | — | `/wallet/` | (genesis) |

**Nota:** Esta tabela será actualizada após auditoria.

---

## 9. Playground ≠ DID

### 9.1 Regra Explícita

```
Playground (W-PLAYGROUND-001)
        ≠
DID Gate (W-DID-CANON-001)
```

O Playground opera em `ANONYMOUS` ou `PLAYGROUND` state. Não requer nem sugere DID até ao momento de Claim.

### 9.2 Claim = Ponte

```
Playground           Claim            DID
(criação livre)  →  (ponte)  →  (posse soberana)
```

A Claim é o momento constitucional onde criação transita para propriedade.

---

## 10. Checklist de Conformidade

Antes de deploy, todo DID Gate DEVE passar:

- [ ] Título trilíngue (PT/EN/DE)
- [ ] Campos na ordem canónica (DID → Passphrase → Entrar)
- [ ] Toggle mostrar/ocultar passphrase
- [ ] Link para `/wallet/`
- [ ] `localStorage('windi-did')` usado
- [ ] `localStorage('windi-did-session')` usado
- [ ] Validação `did:windi:*`
- [ ] Feedback de erro trilíngue
- [ ] Menção a VERA
- [ ] Nenhuma passphrase em storage

---

## 11. Migration Rule

> *"Gates legados podem existir temporariamente fora do Canon, mas qualquer alteração funcional obriga alinhamento com W-DID-CANON-001."*

**Gatilho de migração:**
- Qualquer commit que altere o gate
- Adição de novo serviço com gate
- Bug fix que toque na autenticação

---

## 12. Hierarquia

```
W-DID-CANON-001 (este documento)
        ↓
W-FRONTEND-CANON-001 (i18n, theme)
        ↓
§194 I17 Session/Identity Separation
        ↓
Gate específico
```

---

## 13. Frase de Guarda

> *"A identidade soberana é única. Os portões podem ser muitos."*

---

## 14. Referência Inicial

O gate `/enterprise/desk/` (screenshot 23 Jun 2026) serve como **referência visual**, não como padrão automático. O Canon define o padrão; a referência ilustra.

---

*WINDI Publishing House · Liga IA+H · 2026*
