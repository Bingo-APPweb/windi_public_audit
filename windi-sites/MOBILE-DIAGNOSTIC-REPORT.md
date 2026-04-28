# WINDI-SITES Mobile Diagnostic Report
## §120.5 — Mobile Functionality Compromised

**Date:** 04 April 2026
**Severity:** CRITICAL
**Status:** Desktop ✅ FUNCTIONAL · Mobile ❌ COMPROMISED
**Author:** Guardian Dragon (Claude) · Liga IA+H

---

## Executive Summary

O WINDI-SITES workspace funciona correctamente em desktop mas apresenta falhas críticas em dispositivos móveis. A análise revela que o código foi construído com arquitectura **desktop-first** sem adaptação responsiva, ao contrário do WINDI-Travel que utiliza arquitectura **mobile-first**.

---

## 1. Root Cause Analysis

### 1.1 CSS Architecture

| Aspecto | WINDI-SITES | WINDI-Travel | Impacto |
|---------|-----------|--------------|---------|
| Responsive breakpoints | ❌ **0 @media queries** | ✅ `@media (min-width: 768px)` | Layout quebrado |
| Sidebar | **192px fixo** | Mobile-first collapse | Ocupa ~50% do ecrã mobile |
| Layout base | `display: flex` desktop | Column mobile-first | Overflow horizontal |
| Touch targets | ~10px | ~44px | Difícil de clicar |

### 1.2 Viewport Meta Tags

**WINDI-SITES (Actual):**
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

**WINDI-Travel (Correcto):**
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
```

**Missing:**
- `user-scalable=no` — previne zoom acidental
- `viewport-fit=cover` — iPhone X+ notch handling
- Apple PWA meta tags — instalação como app

### 1.3 Safe Area Handling

**WINDI-SITES:** ❌ Não suporta
```css
/* MISSING */
--safe-b: env(safe-area-inset-bottom, 0px);
```

**WINDI-Travel:** ✅ Implementado
```css
--safe-b: env(safe-area-inset-bottom, 0px);
padding-bottom: calc(var(--safe-b) + 8px);
```

### 1.4 Font Loading

**WINDI-SITES:** Google Fonts external (delay em conexões lentas)
```html
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque...">
```

**WINDI-Travel:** System fonts (render imediato)
```css
--font: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

---

## 2. Symptom Matrix

| Sintoma | Causa | Severidade |
|---------|-------|------------|
| Sidebar ocupa todo o ecrã | `.sl { width: 192px; }` sem collapse | 🔴 CRITICAL |
| Texto cortado horizontalmente | Sem `overflow-x: hidden` no body | 🔴 CRITICAL |
| Botões difíceis de pressionar | Touch targets < 44px | 🟠 HIGH |
| Scroll horizontal indesejado | Fixed widths sem max-width mobile | 🟠 HIGH |
| Input focus zoom | Falta `user-scalable=no` | 🟡 MEDIUM |
| Notch overlap (iPhone X+) | Falta `viewport-fit=cover` | 🟡 MEDIUM |
| Fonts flash | Google Fonts blocking render | 🟡 MEDIUM |

---

## 3. Affected Files

```
/opt/windi/windi-sites/workspace/index.html
├── Lines 62-68: Sidebar CSS (NEEDS RESPONSIVE)
├── Lines 132-153: Layout structure (NEEDS MOBILE-FIRST)
├── Lines 180-210: Prompt box (NEEDS MOBILE WIDTH)
├── Lines 1520-1650: AI Draft modal (NEEDS TOUCH SIZE)
└── Line 5: Viewport meta (NEEDS ENHANCEMENT)

/opt/windi/windi-sites/identity-gate/templates/gate.html
├── Lines 1-10: Viewport meta (NEEDS ENHANCEMENT)
└── Lines 45-55: Body layout (NEEDS MOBILE PADDING)
```

---

## 4. Recommended Solution

### Phase 1: Emergency Mobile Fix (4h effort)

1. **Add responsive breakpoints:**
```css
/* Mobile-first base */
.app { flex-direction: column; }
.sl { display: none; }

/* Desktop enhancement */
@media (min-width: 768px) {
  .app { flex-direction: row; }
  .sl { display: flex; width: 192px; }
}
```

2. **Add hamburger menu for mobile:**
```html
<button class="mobile-menu-btn" onclick="toggleSidebar()">☰</button>
```

3. **Fix viewport meta:**
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
```

4. **Add safe area CSS:**
```css
:root {
  --safe-t: env(safe-area-inset-top, 0px);
  --safe-b: env(safe-area-inset-bottom, 0px);
}
body {
  padding-top: var(--safe-t);
  padding-bottom: var(--safe-b);
}
```

### Phase 2: Full Mobile-First Rewrite (2-3 days)

- Rewrite entire CSS mobile-first (like WINDI-Travel)
- Add touch event handlers
- Implement gesture navigation
- PWA manifest and service worker

---

## 5. Risk Assessment

| Opção | Risco | Benefício |
|-------|-------|-----------|
| **Não fazer nada** | Perda de utilizadores mobile | — |
| **Phase 1 Emergency Fix** | Baixo (CSS only) | 80% funcionalidade mobile |
| **Phase 2 Full Rewrite** | Médio (breaking changes) | 100% paridade mobile |

---

## 6. Comparison: LAW vs Travel

| Métrica | WINDI-SITES | WINDI-Travel |
|---------|-----------|--------------|
| Lines of code | 1,679 | 5,237 |
| @media queries | 0 | 2+ |
| Mobile-first | ❌ | ✅ |
| PWA ready | ❌ | ✅ |
| Touch optimized | ❌ | ✅ |
| Safe area support | ❌ | ✅ |
| System fonts | ❌ | ✅ |

---

## 7. Recommendation

**Immediate Action:** Implement Phase 1 Emergency Fix to restore basic mobile functionality.

**Long-term:** Schedule Phase 2 rewrite following WINDI-Travel architecture patterns.

---

## 8. Test Protocol

After implementing fix, test on:
- [ ] iPhone SE (smallest iOS)
- [ ] iPhone 14 Pro (notch)
- [ ] Samsung Galaxy S22 (Android)
- [ ] Chrome DevTools mobile emulator

---

*Guardian Dragon · Liga IA+H · 04 April 2026*
*"AI processes. Human decides. WINDI guarantees."*
