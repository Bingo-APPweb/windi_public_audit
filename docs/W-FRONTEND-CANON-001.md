# W-FRONTEND-CANON-001 — Frontend Constitutional Canon

**Status:** CANDIDATE
**Version:** 0.1.0
**Created:** 2026-06-23
**Author:** Liga IA+H
**Invariants:** I12, I17, §247, §248

---

## 1. Propósito

> *"Os sites que o curioso pode descobrir através da Foundation precisam parecer parte da mesma civilização."*
> — Guardian, 23 Jun 2026

Este documento define as regras canónicas para **toda página HTML** que faça parte do ecossistema WINDI visível ao público.

**Aplica-se a:**
- Playground, Workbench, Editor
- Foundation portals (Identity, Memory, Verify)
- Tier pages (Personal, Organization, Governance, Enterprise)
- Produtos futuros (W-SITES, W-MAIL, W-CINEMA)

---

## 2. Idiomas Suportados

| Código | Nome | Prioridade |
|--------|------|------------|
| `pt` | Português (Brasil) | Default para PT speakers |
| `en` | English | Default fallback |
| `de` | Deutsch | Default para DE speakers |

**Regra:** Toda página pública DEVE suportar os três idiomas.

**Detecção inicial:**
```javascript
const savedLang = localStorage.getItem('windi-lang');
const browserLang = navigator.language.slice(0, 2);
const supportedLangs = ['pt', 'en', 'de'];
const initialLang = savedLang || (supportedLangs.includes(browserLang) ? browserLang : 'en');
```

---

## 3. Language Storage

| Key | Value | Scope |
|-----|-------|-------|
| `windi-lang` | `pt` \| `en` \| `de` | `localStorage` |

**Anti-patterns:**
- ❌ `windi_lang` (underscore)
- ❌ `windi-language` (verbose)
- ❌ `sessionStorage` (não persiste)
- ❌ Sem persistência (perde escolha)

---

## 4. Theme System

### 4.1 Valores Canónicos

| Theme | Background | Gold | Text |
|-------|------------|------|------|
| `noir` | `#0A0A0B` | `#C9A84C` | `#EDEAE2` |
| `klar` | `#FAFAF8` | `#8B7424` | `#1A1A1A` |

### 4.2 Theme Storage

| Key | Value | Scope |
|-----|-------|-------|
| `windi-theme` | `noir` \| `klar` | `localStorage` |

**Anti-patterns:**
- ❌ `windi_theme` (underscore)
- ❌ `sessionStorage` (não persiste)
- ❌ Hardcoded sem toggle

### 4.3 HTML Attribute

```html
<html data-theme="noir">
```

### 4.4 CSS Variables (Obrigatórias)

```css
:root, [data-theme="noir"] {
  --bg: #0A0A0B;
  --gold: #C9A84C;
  --text: #EDEAE2;
  --border: rgba(255,255,255,0.07);
}

[data-theme="klar"] {
  --bg: #FAFAF8;
  --gold: #8B7424;
  --text: #1A1A1A;
  --border: rgba(0,0,0,0.08);
}
```

---

## 5. Toggle UI

### 5.1 Language Toggle

```html
<div class="lang-toggle">
  <button class="lang-btn" data-lang="de">DE</button>
  <button class="lang-btn" data-lang="en">EN</button>
  <button class="lang-btn" data-lang="pt">PT</button>
</div>
```

**Ordem:** `DE | EN | PT` (alfabética por código)

### 5.2 Theme Toggle

```html
<button class="theme-btn" id="themeBtn">KLAR</button>
```

**Label:** Mostra o tema OPOSTO (clicável para mudar)
- Se `noir` activo → botão mostra "KLAR"
- Se `klar` activo → botão mostra "NOIR"

---

## 6. i18n Pattern

### 6.1 Padrão Recomendado (Inline Spans)

```html
<h1 data-i18n>
  <span lang="pt">Título em português</span>
  <span lang="en">Title in English</span>
  <span lang="de">Titel auf Deutsch</span>
</h1>
```

```css
[data-i18n] > [lang] { display: none; }
[data-lang="pt"] [data-i18n] > [lang="pt"] { display: inline; }
[data-lang="en"] [data-i18n] > [lang="en"] { display: inline; }
[data-lang="de"] [data-i18n] > [lang="de"] { display: inline; }
```

### 6.2 Padrão Alternativo (JS Object)

```javascript
const UI = {
  pt: { title: 'Título', btn: 'Começar' },
  en: { title: 'Title', btn: 'Start' },
  de: { title: 'Titel', btn: 'Starten' }
};

function t(key) {
  return UI[currentLang][key] || UI['en'][key] || key;
}
```

Ambos são válidos. Escolher UM por página e manter consistência.

---

## 7. Inicialização Canónica

```javascript
document.addEventListener('DOMContentLoaded', () => {
  // Theme
  const savedTheme = localStorage.getItem('windi-theme') || 'noir';
  document.documentElement.setAttribute('data-theme', savedTheme);

  // Language
  const savedLang = localStorage.getItem('windi-lang');
  const browserLang = navigator.language.slice(0, 2);
  const supportedLangs = ['pt', 'en', 'de'];
  const initialLang = savedLang || (supportedLangs.includes(browserLang) ? browserLang : 'en');
  document.documentElement.setAttribute('data-lang', initialLang);
  document.documentElement.lang = initialLang === 'pt' ? 'pt-BR' : initialLang;

  // Persist if auto-detected
  if (!savedLang) {
    localStorage.setItem('windi-lang', initialLang);
  }
});
```

---

## 8. Checklist de Conformidade

Antes de deploy, toda página DEVE passar:

- [ ] Toggle de língua visível (DE | EN | PT)
- [ ] Toggle de tema visível (NOIR/KLAR)
- [ ] `localStorage('windi-lang')` usado
- [ ] `localStorage('windi-theme')` usado
- [ ] CSS variables `--bg`, `--gold`, `--text`, `--border` definidas
- [ ] `data-theme` no `<html>`
- [ ] `data-lang` no `<html>`
- [ ] Nenhum texto hardcoded sem tradução

---

## 9. Hierarquia de Aplicação

```
W-FRONTEND-CANON-001 (este documento)
    ↓
§11.2 Frontend Invariants (CLAUDE.md)
    ↓
Página específica
```

Se houver conflito, este documento prevalece sobre implementações anteriores.

---

## 10. Migration Rule

> *"Sistemas legados podem existir temporariamente fora do Canon, mas qualquer alteração funcional obriga alinhamento com W-FRONTEND-CANON-001."*

**Regra:** Nenhuma página está isenta permanentemente. A exceção é temporal, não estrutural.

**Gatilho de migração:**
- Qualquer commit que altere funcionalidade da página
- Qualquer novo feature adicionado
- Qualquer bug fix que toque no frontend

**Anti-pattern:**
- ❌ "Mas esta página é antiga..." (não é justificação válida)

---

## 11. Frontend Identity Layer

### 11.1 Keys Canónicas (Activas)

| Key | Propósito | Status |
|-----|-----------|--------|
| `windi-lang` | Preferência de idioma | ✅ ACTIVE |
| `windi-theme` | Preferência de tema | ✅ ACTIVE |

### 11.2 Keys Reservadas (Futuro)

| Key | Propósito | Status |
|-----|-----------|--------|
| `windi-region` | Região/fuso horário | 🔒 RESERVED |
| `windi-accessibility` | Preferências de acessibilidade | 🔒 RESERVED |

**Regra:** Estas keys estão reservadas para uso futuro. Nenhuma implementação deve usar variantes como `region_pref`, `country`, `locale`, `access`.

**Anti-patterns futuros bloqueados:**
- ❌ `region_pref`
- ❌ `country`
- ❌ `locale`
- ❌ `access`
- ❌ `accessibility_mode`

---

## 12. Páginas Auditadas (23 Jun 2026)

| Página | Conforme | Notas |
|--------|----------|-------|
| `playground.html` | ✅ | Modelo de referência |
| `editor.html` | ✅ | Modelo de referência |
| `/personal/` | ✅ | Conforme |
| `/org/` | ✅ | Conforme |
| `/identity/` | ⚠️ | sessionStorage → localStorage |
| `/memory/` | ⚠️ | sessionStorage → localStorage |
| `/governance/` | ❌ | Falta i18n, underscore em key |
| `/enterprise/` | ❌ | Falta i18n e theme toggle |

---

## 13. Frase de Guarda

> *"Uma mesma casa, com quartos diferentes."*

---

*WINDI Publishing House · Liga IA+H · 2026*
