---
name: windi-mobile-canvas
description: >
  Estratégia mobile completa do WINDI e roadmap do Canvas Gen 7 — o Mobile Control Center
  institucional. Use quando o utilizador mencionar: mobile, touch, Canvas Gen 7, pointer events,
  windi-touch.js, Smart Zones, bottom bar, gestures, breakpoints mobile, redirect /desktop/,
  MAMUT mobile, touch grammar, verify-public mobile, responsivo, iOS Safari, Android Chrome,
  "Mobile Audit", "programa de mudanças mobile", ou qualquer tarefa envolvendo a experiência
  touch do WINDI. Ativar também para: decisões sobre /desktop/ vs /app/, implementação de
  bottom sheets, touch targets, Smart Zones G1-G4, ou evolução pós-Canvas Gen 7.
---

# WINDI Mobile Strategy & Canvas Gen 7

## Contexto

**Data do audit:** 13 Março 2026
**Relatório Gêmeo:** `/opt/windi/docs/MOBILE-AUDIT-REPORT-2026-03-13.md`
**Estado:** Canvas Gen 7 em execução — estratégia mobile completa gravada para uso **pós-Gen 7**

---

## Filosofia Mobile WINDI

Sistemas complexos cometem o erro de:
```
desktop → adaptar para mobile   ❌
```

O WINDI tem duas naturezas distintas:

### Ferramentas de Criação Profunda → Desktop Only
| Rota | Ferramenta | Decisão |
|---|---|---|
| `/desktop/` | Tiptap editor | Desktop-only + redirect |
| `/a4desk-editor/` | A4Desk editor | Desktop-only |

### Ferramentas Operacionais Rápidas → Mobile First
| Rota | Ferramenta |
|---|---|
| `/app/` | Canvas / Palette — **Mobile Control Center** |
| `/verify-public/` | Verificação de documentos |
| `/wallet/` | Carteira institucional |
| `/dashboard/` | Painel operacional |
| `/communique/` | Communiqué |
| `/library/` | Biblioteca |

---

## Decisões Arquitecturais Seladas

### ✅ DECISÃO 1: `/desktop/` = Desktop-Only

```
Mobile user → abre /desktop/ → redirect → /app/
```

**Implementação — injetar no `<head>` de `/opt/windi/desktop/frontend/index.html`:**
```javascript
// Primeiro script no <head>, sem dependências
if (/Mobi|Android|iPhone|iPad|iPod|Touch/i.test(navigator.userAgent)
    || window.innerWidth < 768) {
  window.location.replace('https://windi-domain.com/app/?from=desktop');
}
```

O parâmetro `?from=desktop` permite ao Canvas Gen 7 mostrar mensagem contextual:
> *"Estás no Canvas Mobile. Para edição avançada, usa o Desktop."*

**Razão:** Tiptap + interface de edição densa em mobile = batalha cara que o utilizador não quer.

---

### ✅ DECISÃO 2: Canvas Gen 7 = Mobile Control Center

O `/app/` não é apenas um editor de slides. É o **WINDI Mobile OS**.

Visão final:
```
DESKTOP        MOBILE
editor         interface
profundo       operacional

(como Figma, Notion, Linear funcionam)
```

---

## Audit Summary — 13 Mar 2026

| Métrica | Valor |
|---|---|
| Total rotas públicas | 24 |
| 🟢 Mobile-Ready | 7 |
| 🟡 Precisa Ajustes | 16 |
| 🔴 Crítico | 1 (`/verify-public/`) |

### 🟢 GREEN (já mobile-ready)
`/` (Landing), `/pioneer/`, `/manifesto/`, `/a4desk/`, `/clone/`, `/wallet/`, `/communique/`

### 🟡 YELLOW principais
| Rota | Problema | Esforço |
|---|---|---|
| `/app/` | 1 breakpoint, icons 18px | Médio |
| `/desktop/` | Tiptap não touch | Alto → **Desktop-only** |
| `/certification/` | Sem media queries | Médio |
| `/verify-public/` (foi RED) | canvas+mouse events | Médio (Fase 3) |

### 🔴 RED → Fase 3
`/verify-public/` — Canvas QR com mouse events, drag-drop não funciona em touch

---

## Touch Grammar (Standard WINDI)

Definida uma vez, usada em todo o sistema:

| Gesto | Ação |
|---|---|
| **Tap** | Selecionar layer |
| **Double Tap** | Editar texto |
| **Pinch** | Zoom canvas |
| **Drag** | Mover layer |
| **Long Press** | Menu contextual |

### Regra de Ouro
```
Touch targets: mínimo 44px  |  ideal 48px
```
*(padrão Apple HIG + Google Material)*

---

## `windi-touch.js` — Ficheiro Global

**Path:** `/opt/windi/static/windi-touch.js`
**Propósito:** Toda a lógica touch centralizada — todo o sistema usa a mesma fundação.

```javascript
// windi-touch.js — WINDI Touch Engine v1.0
// Fundação global para pointer events unificados

const WindiTouch = {

  // Detecta se é dispositivo touch
  detectTouch() {
    return ('ontouchstart' in window)
        || (navigator.maxTouchPoints > 0)
        || (navigator.msMaxTouchPoints > 0);
  },

  // Normaliza pointer events (mouse + touch + pen)
  normalizePointer(e) {
    if (e.touches) {
      return {
        x: e.touches[0].clientX,
        y: e.touches[0].clientY,
        type: 'touch'
      };
    }
    return { x: e.clientX, y: e.clientY, type: 'mouse' };
  },

  // Detecta gesto básico (tap vs drag vs long press)
  detectGesture(startEvent, endEvent, durationMs) {
    const dx = Math.abs(endEvent.x - startEvent.x);
    const dy = Math.abs(endEvent.y - startEvent.y);
    const dist = Math.sqrt(dx*dx + dy*dy);

    if (durationMs > 500 && dist < 10) return 'longpress';
    if (dist < 10) return 'tap';
    if (dist > 10) return 'drag';
    return 'unknown';
  },

  // Expande zona de tap para garantir mínimo 44px
  tapZoneExpand(element, minSize = 44) {
    const rect = element.getBoundingClientRect();
    const padH = Math.max(0, (minSize - rect.height) / 2);
    const padW = Math.max(0, (minSize - rect.width) / 2);
    element.style.padding = `${padH}px ${padW}px`;
    element.style.margin = `-${padH}px -${padW}px`;
  }
};

export default WindiTouch;
```

---

## Breakpoints WINDI Mobile

```css
/* Breakpoints canónicos WINDI */

/* Desktop — full experience */
@media (min-width: 1200px) { }

/* Tablet — toolbar colapsável */
@media (min-width: 768px) and (max-width: 1199px) { }

/* Mobile — bottom bar + canvas full-width */
@media (max-width: 767px) { }
```

---

## Canvas Gen 7 — Layout Mobile

```
┌─────────────────────┐
│                     │
│       CANVAS        │
│   (full viewport)   │
│                     │
│                     │
├─────────────────────┤
│  +   layers   tools │  ← Bottom Bar (zona do polegar)
└─────────────────────┘
```

**Princípio:** Toolbar sempre em bottom bar em mobile. O polegar vive aqui.

---

## Roadmap de Execução (pós-Canvas Gen 7)

### FASE 1 — Fundação Touch `/app/`
```
□ Pointer Events unificados (windi-touch.js)
□ Touch targets ≥44px em todas as Smart Zones
□ Pinch-to-zoom no canvas
□ Smart Zones G1 + G2 mobile-ready
□ Breakpoints 3 níveis implementados
□ Redirect /desktop/ → /app/ ativado
```

### FASE 2 — Smart Zones Completas
```
□ G3 + G4 com comportamento mobile-first
□ Bottom sheet para propriedades de layer
□ Swipe para alternar zonas
□ Layer inspector em bottom sheet
□ Toolbar lateral colapsável (tablet 768-1199px)
```

### FASE 3 — Verify-Public Mobile (paralelo)
```
□ Migrar canvas+mouse → pointer events
□ Substituir drag-drop → <input type="file"> touch-friendly
□ MediaDevices.getUserMedia() com fallback mobile
□ Testar iOS Safari (câmara restrita)
□ Testar Android Chrome
□ QR scan via câmara em mobile
```

---

## Smart Zones G1→G4

*(Definidas na sessão de 13 Mar 2026)*

| Zone | Nome | Função | Prioridade Mobile |
|---|---|---|---|
| G1 | Canvas Core | Área de criação principal | Fase 1 — full viewport |
| G2 | Toolbar | Ferramentas de edição | Fase 1 — bottom bar |
| G3 | Layer Inspector | Propriedades de camadas | Fase 2 — bottom sheet |
| G4 | Document Controls | Gestão do documento | Fase 2 — swipe panel |

---

## Referências

- **Audit completo:** `/opt/windi/docs/MOBILE-AUDIT-REPORT-2026-03-13.md`
- **Touch engine:** `/opt/windi/static/windi-touch.js`
- **Canvas Gen 7:** `/opt/windi/agent-palette/ui/index.html`
- **Desktop frontend:** `/opt/windi/desktop/frontend/index.html`
- **nginx ONE TREE:** `/etc/nginx/sites-enabled/one-tree-windi-domain.com`

---

## Nota Arquitectural

> O Canvas Gen 7 não é apenas um upgrade de editor.
> É o **WINDI Mobile OS** — o ponto de entrada operacional
> para toda a infraestrutura institucional num dispositivo touch.
>
> Depois do Gen 7, o WINDI terá a mesma separação que
> Figma, Notion e Linear: **desktop para criação profunda,
> mobile para operações rápidas e decisões institucionais.**

---

*Skill criado em 13 Mar 2026 — Human Dragon + Architect*
*Ativar quando o tema for mobile, touch, Canvas Gen 7 ou pós-Gen 7 evolution*
