# WINDI Mobile Audit Report
**Data:** 13 Março 2026
**Versão:** 1.0
**Autor:** Gêmeo (Claude Code)
**Propósito:** Base para Programa de Mudanças Mobile

---

## Resumo Executivo

| Métrica | Valor |
|---------|-------|
| **Total de Rotas Públicas** | 24 |
| **Com viewport meta** | 100% (24/24) |
| **Com media queries** | 67% (16/24) |
| **Mobile-Ready** | 7 páginas |
| **Precisa Ajustes** | 16 páginas |
| **Crítico (reescrita)** | 1 página |

---

## Classificação por Estado

### GREEN — Já Mobile-Ready (7 páginas)

| Rota | Ficheiro Fonte | Tech Stack | Breakpoints | Notas |
|------|----------------|------------|-------------|-------|
| `/` (Landing) | `/opt/windi/landing-pmg/static/index.html` | HTML+CSS | 900px, 480px | Pronto |
| `/pioneer/` | `/opt/windi/pioneer-landing/index.html` | HTML+CSS+JS | 768px, 600px | Pronto |
| `/manifesto/` | `/opt/windi/manifesto/index.html` | HTML+CSS | Múltiplos | Multi-idioma |
| `/a4desk/` | `/opt/windi/a4desk-landing/index.html` | HTML+CSS | Múltiplos | Layout centrado |
| `/clone/` | `/opt/windi/clone-landing/index.html` | HTML+CSS | Múltiplos | Klar+Noir themes |
| `/wallet/` | `/opt/windi/wallet/static/wallet_login.html` | HTML+CSS+JS | CSS Grid/Flex | ⚠️ Remover `user-scalable=no` |
| `/communique/` | Proxy 8105 | HTML | Responsivo | Pronto |

---

### YELLOW — Precisa Ajustes (16 páginas)

#### Alta Prioridade

| Rota | Ficheiro Fonte | Tech Stack | Problema Principal | Esforço |
|------|----------------|------------|---------------------|---------|
| `/app/` (Palette) | `/opt/windi/agent-palette/ui/index.html` | React 18 + DragonEngine | Só 1 breakpoint (768px), icons 18px, Canvas mouse events | **Médio-Alto** |
| `/certification/` | `/opt/windi/certification/templates/*.html` | HTML+Flask | Sem media queries responsivas, form 600px fixo | **Médio** |
| `/dashboard/` | `/opt/windi/dashboard/src/` | React 19 + Vite | Análise React pendente | **Médio** |
| `/desktop/` | `/opt/windi/desktop/frontend/src/` | React 18 + Tiptap | Editor WYSIWYG não otimizado p/ touch | **Alto** |

#### Média Prioridade

| Rota | Backend Port | Problema | Esforço |
|------|--------------|----------|---------|
| `/desk/` (A4 Hub) | 8085 | React - análise pendente | Médio |
| `/governance/` | 8080 | Análise pendente | Médio |
| `/war-room/` | 8090 | WebSocket - análise pendente | Médio |
| `/bridge/` | 8097 | Análise pendente | Médio |
| `/vault/` | 8106 | Análise pendente | Médio |
| `/library/` | 8091 | Análise pendente | Médio |
| `/builder/` | 8115 | Análise pendente | Médio |
| `/distribute/` | 8116 | Análise pendente | Médio |

#### Baixa Prioridade

| Rota | Backend Port | Esforço |
|------|--------------|---------|
| `/legal/` | 8091 | Baixo |
| `/accounting/` | 8091 | Baixo |
| `/audit/` | 8091 | Baixo |
| `/vpr/` | 8091 | Baixo |

---

### RED — Crítico (1 página)

| Rota | Ficheiro Fonte | Tech Stack |
|------|----------------|------------|
| `/verify-public/` | `/opt/windi/verify-public/web/index.html` | HTML+JS+Canvas |

#### Problemas Identificados:
1. **Canvas QR Scanning** — 7 referências a canvas com mouse events
2. **Drag-and-Drop PDF** — `ondragover`, `ondrop` não funcionam em touch
3. **Webcam iOS** — Acesso limitado em Safari mobile
4. **Touch Targets** — 19 onclick handlers, alguns com targets pequenos

#### Ações Necessárias:
```
1. Migrar canvas para MediaDevices.getUserMedia() com fallback mobile
2. Substituir drag-drop por <input type="file" accept=".pdf">
3. Implementar touch-friendly interface para upload
4. Testar em iOS Safari (acesso webcam restrito)
5. Aumentar hit targets para mínimo 48px
```

---

## Análise Detalhada por Rota

### 1. Landing Page (`/`)

**Ficheiro:** `/opt/windi/landing-pmg/static/index.html` (912 linhas)
**Backend:** Python Flask (port 8107)

| Critério | Status | Detalhes |
|----------|--------|----------|
| Viewport Meta | ✅ | `width=device-width, initial-scale=1.0` |
| Media Queries | ✅ | `@media (max-width: 900px)` e `480px` |
| Touch Support | ✅ | CSS pointer-events |
| Canvas/Mouse | ✅ | Nenhum |
| Min Touch Size | ✅ | Buttons ~44px |
| Horizontal Scroll | ✅ | `overflow-x: hidden` |

**Estado:** PRONTO

---

### 2. Palette Agent Workspace (`/app/`)

**Ficheiro:** `/opt/windi/agent-palette/ui/index.html` (7819 linhas)
**Backend:** Node.js/Express (port 8108) — Dragon Server
**Tech:** React 18 via CDN, Babel standalone, DragonEngine v2.0

| Critério | Status | Detalhes |
|----------|--------|----------|
| Viewport Meta | ✅ | `width=device-width, initial-scale=1.0` |
| Media Queries | ⚠️ | Apenas `@media (max-width: 768px)` |
| Touch Support | ⚠️ | Parcial — touchstart/touchend presentes |
| Canvas/Mouse | ❌ | **Canvas Desk usa mouse events** |
| Min Touch Size | ⚠️ | Icons 18px (pequeno) |
| Horizontal Scroll | ⚠️ | Layout complexo pode ter overflow |

**Problemas:**
- Apenas 1 breakpoint (768px) — quebra entre 480px-767px
- Canvas usa `onMouseDown`, `mousemove`, `mouseup`
- Resize handles 8x8px (impossível tocar)
- Icons de 18px difíceis de tocar

**Solução Proposta:**
```javascript
// 1. Migrar mouse → Pointer Events
onMouseDown → onPointerDown + setPointerCapture
mousemove → pointermove
mouseup → pointerup

// 2. Handles touch-friendly
width: 44px, height: 44px (área invisível)
visual: 8x8px centrado

// 3. Adicionar breakpoints
@media (max-width: 480px) { ... }
@media (max-width: 375px) { ... }
```

---

### 3. Pioneer Program (`/pioneer/`)

**Ficheiro:** `/opt/windi/pioneer-landing/index.html` (1094 linhas)
**Backend:** Node.js (port 8120)

| Critério | Status |
|----------|--------|
| Viewport | ✅ |
| Media Queries | ✅ |
| Touch | ✅ |
| Canvas | ✅ Nenhum |

**Estado:** PRONTO

---

### 4. Verify-Public (`/verify-public/`) — CRÍTICO

**Ficheiro:** `/opt/windi/verify-public/web/index.html` (596 linhas)
**Backend:** Node.js (port 8114)

| Critério | Status | Detalhes |
|----------|--------|----------|
| Viewport Meta | ✅ | Presente |
| Media Queries | ⚠️ | Apenas 900px |
| Touch Support | ❌ | Drag-drop não funciona |
| Canvas/Mouse | ❌ | **7 referências canvas** |
| Min Touch Size | ⚠️ | Alguns buttons pequenos |

**Código Problemático:**
```javascript
// Linhas com canvas (QR scanning)
canvas.getContext('2d').drawImage()
// Drag-drop (não funciona em mobile)
ondragover, ondrop, ondragleave
```

**Refactor Necessário:**
```javascript
// 1. Substituir canvas QR por biblioteca mobile-friendly
// Opção: html5-qrcode ou @aspect/qr-code

// 2. Substituir drag-drop
<input type="file" accept=".pdf" capture="environment">

// 3. Fallback para câmera
navigator.mediaDevices.getUserMedia({
  video: { facingMode: 'environment' }
})
```

---

### 5. Certification (`/certification/`)

**Ficheiro:** `/opt/windi/certification/templates/register.html` (551 linhas)
**Backend:** Python Flask

| Critério | Status | Detalhes |
|----------|--------|----------|
| Viewport | ✅ | Presente |
| Media Queries | ❌ | Apenas print media |
| Touch | ✅ | Form inputs padrão |
| Layout | ❌ | 600px fixo, padding 30px |

**Solução:**
```css
@media (max-width: 768px) {
  .form-container { max-width: 100%; padding: 15px; }
  h1 { font-size: 1.5rem; }
}
@media (max-width: 480px) {
  .form-container { padding: 10px; }
  input, select { font-size: 16px; } /* Evita zoom iOS */
}
```

---

### 6. Desktop Editor (`/desktop/`)

**Ficheiro:** `/opt/windi/desktop/frontend/` (React SPA)
**Backend:** Node.js Vite (port 8100)
**Tech:** React 18 + Tiptap + ProseMirror

| Critério | Status |
|----------|--------|
| Touch | ❌ |
| Editor WYSIWYG | ❌ Não otimizado |
| Toolbar | ❌ Buttons pequenos |

**Decisão Necessária:**
```
Opção A: Mobile-ready (esforço ALTO)
  - Reescrever toolbar para touch
  - Implementar gestos para formatação
  - Testar ProseMirror em iOS

Opção B: Desktop-only (RECOMENDADO)
  - Redirect mobile → /app/ (Palette)
  - Mostrar mensagem "Use desktop para edição"
```

---

### 7. Dashboard (`/dashboard/`)

**Ficheiro:** `/opt/windi/dashboard/src/` (React 19)
**Backend:** Node.js Vite (port 8118)

**Estado:** Análise pendente — requer auditoria de componentes React

---

### 8. Wallet (`/wallet/`)

**Ficheiro:** `/opt/windi/wallet/static/wallet_login.html` (331 linhas)

| Critério | Status |
|----------|--------|
| Viewport | ⚠️ `user-scalable=no` |
| Layout | ✅ CSS Grid/Flex responsivo |
| Touch | ✅ `min-height: 100dvh` |

**Fix Necessário:**
```html
<!-- ANTES -->
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">

<!-- DEPOIS (acessibilidade) -->
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

---

## Mapa de Prioridades

```
SEMANA 1-2 (Crítico):
├── /verify-public/ → Refactor Canvas + Touch upload
└── /app/ (Palette) → Pointer Events migration

SEMANA 3-4 (Importante):
├── /certification/ → Adicionar media queries
├── /wallet/ → Remover user-scalable=no
└── /dashboard/ → Auditoria React

SEMANA 5-6 (Médio):
├── /desktop/ → Decisão: mobile ou redirect
├── /desk/ → Auditoria
└── Rotas 8091 (legal, audit, etc.)

BACKLOG:
├── /war-room/ → WebSocket mobile
├── /bridge/, /vault/ → Análise
└── Touch gestures avançados (pinch-to-zoom)
```

---

## Decisões Arquitecturais Pendentes

| # | Questão | Opções | Recomendação |
|---|---------|--------|--------------|
| 1 | Desktop Editor mobile? | A) Mobile-ready / B) Desktop-only | **B** — Redirect para Palette |
| 2 | Verify-Public refactor | A) Canvas fix / B) App nativa | **A** — Usar html5-qrcode lib |
| 3 | Palette structure | A) Monolito / B) Separar mobile view | **A** — Manter monolito com breakpoints |
| 4 | Touch engine | A) Custom / B) Hammer.js | **A** — WindiTouch.js (já criado) |

---

## Ficheiros Chave

### Para Auditoria Futura
```bash
/opt/windi/desktop/frontend/src/components/
/opt/windi/dashboard/src/
/opt/windi/agent-palette/ui/modules/
```

### CSS Principal
```bash
/opt/windi/desktop/frontend/src/styles/d1.css
/opt/windi/desktop/frontend/src/a4-page.css
/opt/windi/static/windi-design-system.css
```

### Canvas Problemático
```bash
/opt/windi/verify-public/web/index.html
# Linhas: grep -n "canvas" para localizar
```

### Touch Engine (já criado)
```bash
/opt/windi/desktop/static/windi-touch.js
/opt/windi/windi-touch/windi-touch.js
```

---

## Implementações Já Realizadas (13 Mar 2026)

| Item | Status | Ficheiro |
|------|--------|----------|
| WindiTouch.js v1.0.0 | ✅ Criado | `/opt/windi/desktop/static/windi-touch.js` |
| Swipe gestures | ✅ Implementado | sidebar open/close, tab navigation |
| Haptic feedback | ✅ Implementado | iOS + Android vibration |
| Breakpoint detection | ✅ Implementado | `WindiTouch.breakpoints` |
| Body classes | ✅ Implementado | `.windi-mobile`, `.windi-tablet`, `.windi-desktop` |
| __windiBridge | ✅ Injetado | React state ↔ touch engine |
| Pointer Events Canvas | ⏸️ Rollback | Causou blank screen — investigar |

---

## Próximos Passos

1. **Revisar este documento** com stakeholders
2. **Priorizar** baseado em impacto de utilizadores
3. **Criar tickets** para cada item YELLOW/RED
4. **Definir** se Desktop Editor será mobile ou desktop-only
5. **Testar** WindiTouch.js em dispositivos reais
6. **Investigar** porque Pointer Events causou blank screen

---

## Contacto

**Gerado por:** Gêmeo (Claude Code)
**Para:** Human Dragon
**Projecto:** WINDI Mobile Transformation Program

---

*"AI processes. Human decides. WINDI guarantees."*
