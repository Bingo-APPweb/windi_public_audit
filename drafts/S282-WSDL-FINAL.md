# §282 — WINDI Surface Design Language (WSDL v1.0)

```
Status:         SEALED
Data:           2026-05-19
Receipt:        WINDI-S282-WSDL-20260519140512
Hash (8):       BF367F0C
Autoridade:     Human Dragon (I9 formal)
Filtro:         Guardian (Trust by Calmness)
Construtor:     CCode (Opus 4.5)
Invariants:     I1, I9, I11, I12, I14
Lineage:        §281 (Léxico de Superfície) → §282 (WSDL)
doc_type:       constitutional
Fundamento:     §281 — "A superfície não expõe complexidade por padrão"
Horizonte:      2045+ (multigeneracional)
```

---

## Tese Central

> **"Trust by Calmness — A confiança institucional transmite-se pela calma visual,
> não pela efervescência gráfica. O que é sólido não precisa de gritar."**

Este § sela a linguagem visual canónica do WINDI-HIOS.
Não é style guide de startup. É infraestrutura cívica de longa duração.

---

## 1. O Princípio "Trust by Calmness"

### 1.1 Definição

A superfície WINDI comunica fiabilidade através de:

| Atributo | Manifestação |
|----------|--------------|
| **Silêncio visual** | Espaço negativo generoso, sem ruído decorativo |
| **Movimento contido** | Transições suaves (300-500ms), nunca frenéticas |
| **Tipografia sóbria** | Peso visual consistente, sem display fonts |
| **Cor funcional** | Cada cor tem função, não decoração |
| **Provas discretas** | Audit affordance presente mas não invasiva |

### 1.2 Anti-Patterns PROIBIDOS

```
❌ Gradientes vibrantes "tech startup"
❌ Animações de loading exuberantes
❌ Badges, ribbons, medalhas decorativas
❌ Confetti, sparkles, celebrações gráficas
❌ Dark patterns de urgência ("Última oportunidade!")
❌ Tipografia display ou experimental
❌ CDN externo para fontes (→ self-hosted obrigatório)
```

### 1.3 Horizonte Temporal

Este design system é projectado para **2045+**.
Decisões de curto prazo que comprometam longevidade são **violação constitucional**.

---

## 2. Parâmetros Cromáticos e Modos Universais

### 2.1 Dois Modos Únicos

| Modo | Contexto | Filosofia |
|------|----------|-----------|
| **NOIR** | Default, trabalho nocturno, foco | Fundo escuro, elementos claros |
| **KLAR** | Luz ambiente, acessibilidade, impressão | Fundo claro, elementos escuros |

**Regra:** Todo componente WINDI suporta ambos os modos. Sem excepções.

### 2.2 Paleta NOIR (Canónica)

```css
:root[data-theme="noir"] {
  --windi-bg:           #0A0A10;
  --windi-surface:      #12121A;
  --windi-border:       #1A1A24;
  --windi-text:         #E8E6E1;
  --windi-text-muted:   #8A8A8A;
  --windi-gold:         #C9A84C;
  --windi-gold-hover:   #D4B85A;

  /* Estados funcionais */
  --windi-green:        #2D5A3D;
  --windi-amber:        #8B6914;
  --windi-orange:       #A85C32;
  --windi-red:          #8B2D2D;
}
```

### 2.3 Paleta KLAR (Canónica)

```css
:root[data-theme="klar"] {
  --windi-bg:           #FAFAF8;
  --windi-surface:      #FFFFFF;
  --windi-border:       #E0DED8;
  --windi-text:         #1A1A1A;
  --windi-text-muted:   #6A6A6A;
  --windi-gold:         #8B7424;
  --windi-gold-hover:   #9A8230;

  /* Estados funcionais */
  --windi-green:        #1B7A3D;
  --windi-amber:        #A67C00;
  --windi-orange:       #C46A30;
  --windi-red:          #B33030;
}
```

### 2.4 Semântica das Cores de Estado

| Cor | Função | Aplicação |
|-----|--------|-----------|
| **Verde** | Presença confirmada | "WINDI presente" (silencioso) |
| **Âmbar** | Verificação em curso | "WINDI a verificar" |
| **Laranja** | Atenção requerida | Degradação parcial |
| **Vermelho** | Acção bloqueada | "WINDI suspenso" |
| **Ouro** | Interacção primária | Botões, links, CTAs |

---

## 3. Tipografia Soberana

### 3.1 Stack Tipográfico

| Uso | Família | Peso | Fallback |
|-----|---------|------|----------|
| **Títulos** | Bricolage Grotesque | 700-800 | system-ui, sans-serif |
| **Corpo** | Inter | 400-600 | system-ui, sans-serif |
| **Código/Hashes** | JetBrains Mono | 400 | monospace |

### 3.2 Regra de Self-Hosting (IRREMEDIÁVEL)

```
❌ PROIBIDO: <link href="https://fonts.googleapis.com/...">
❌ PROIBIDO: @import url('https://fonts.gstatic.com/...');
✅ OBRIGATÓRIO: Ficheiros .woff2 em /assets/fonts/
✅ OBRIGATÓRIO: @font-face local com font-display: swap
```

**Razão:** Soberania sobre dependências externas.
Se Google Fonts cair, WINDI continua a funcionar.

### 3.3 Escala Tipográfica

```css
--windi-text-xs:    0.75rem;   /* 12px */
--windi-text-sm:    0.875rem;  /* 14px */
--windi-text-base:  1rem;      /* 16px */
--windi-text-lg:    1.125rem;  /* 18px */
--windi-text-xl:    1.25rem;   /* 20px */
--windi-text-2xl:   1.5rem;    /* 24px */
--windi-text-3xl:   1.875rem;  /* 30px */
```

---

## 4. Comportamento da Camada de Prova (Audit Affordance)

### 4.1 Princípio

> **"A prova está sempre lá. O utilizador decide quando a ver."**

### 4.2 Gradiente de Exposição

| Camada | Visibilidade | Conteúdo |
|--------|--------------|----------|
| **L0 — Superfície** | Sempre visível | Estado (cor), acção ("Verificar") |
| **L1 — Resumo** | Clique/hover | Receipt ID, timestamp, estado |
| **L2 — Técnico** | Segundo clique | Hash completo, lineage, raw JSON |
| **L3 — Forense** | Exportação | Ledger query, Merkle proof |

### 4.3 Affordances Visuais

```css
/* Indicador de prova disponível */
.windi-has-proof::after {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--windi-gold);
  opacity: 0.6;
}

/* Hover revela mais */
.windi-has-proof:hover::after {
  opacity: 1;
}
```

### 4.4 Colapso Discreto

Painéis de prova técnica usam `<details>` nativo:

```html
<details class="windi-proof-panel">
  <summary>Verificar</summary>
  <div class="proof-content">
    <!-- L1/L2 content -->
  </div>
</details>
```

---

## 5. Copy de Estado e Orientação de Ação

### 5.1 Estados de Re-entry (§281 Aplicado)

| Score | Cor | Copy Primário | Copy Secundário |
|-------|-----|---------------|-----------------|
| **90-100** | Verde | *silêncio* | "WINDI presente" (hover) |
| **70-89** | Âmbar | "WINDI a verificar" | "Aguarde antes de selar trabalho novo" |
| **50-69** | Laranja | "Atenção requerida" | "WINDI em modo verificação. Aguarde antes de selar trabalho novo." |
| **<50** | Vermelho | "WINDI suspenso" | "Continuidade não verificável. Contacte suporte." |

### 5.2 Regra do Silêncio no Verde

> **"O estado perfeito não anuncia que é perfeito."**

Score 90-100 = nenhum banner, nenhuma notificação, nenhum indicador explícito.
Apenas o dot discreto (6px) que diz "há prova disponível se quiseres".

### 5.3 Copy de Acção

| Acção | Verbo | Anti-pattern |
|-------|-------|--------------|
| Submeter trabalho | "Selar" | ~~"Enviar"~~ |
| Ver prova | "Verificar" | ~~"Ver detalhes"~~ |
| Cancelar | "Descartar" | ~~"Cancelar"~~ |
| Confirmar | "Confirmar" | ~~"OK"~~, ~~"Sim"~~ |

---

## 6. Espaçamento e Grid

### 6.1 Escala de Espaçamento

```css
--windi-space-1:   0.25rem;  /* 4px */
--windi-space-2:   0.5rem;   /* 8px */
--windi-space-3:   0.75rem;  /* 12px */
--windi-space-4:   1rem;     /* 16px */
--windi-space-6:   1.5rem;   /* 24px */
--windi-space-8:   2rem;     /* 32px */
--windi-space-12:  3rem;     /* 48px */
--windi-space-16:  4rem;     /* 64px */
```

### 6.2 Breakpoints

```css
--windi-bp-sm:   640px;
--windi-bp-md:   768px;
--windi-bp-lg:   1024px;
--windi-bp-xl:   1280px;
```

### 6.3 Touch Targets (Acessibilidade)

```css
.windi-touch-target {
  min-width: 44px;
  min-height: 44px;
}
```

---

## 7. Componentes Base (Primitivos)

### 7.1 Botão Primário

```css
.windi-btn-primary {
  background: var(--windi-gold);
  color: var(--windi-bg);
  padding: var(--windi-space-3) var(--windi-space-6);
  border-radius: 6px;
  font-weight: 600;
  transition: background 300ms ease;
}

.windi-btn-primary:hover {
  background: var(--windi-gold-hover);
}
```

### 7.2 Card de Prova

```css
.windi-proof-card {
  background: var(--windi-surface);
  border: 1px solid var(--windi-border);
  border-radius: 8px;
  padding: var(--windi-space-4);
}
```

### 7.3 Badge de Estado

```css
.windi-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--windi-space-2);
  padding: var(--windi-space-1) var(--windi-space-3);
  border-radius: 9999px;
  font-size: var(--windi-text-sm);
  font-weight: 500;
}

.windi-badge--green { background: var(--windi-green); }
.windi-badge--amber { background: var(--windi-amber); }
.windi-badge--red   { background: var(--windi-red); }
```

---

## 8. Movimento e Transições

### 8.1 Timing Functions

```css
--windi-ease-default: cubic-bezier(0.4, 0, 0.2, 1);
--windi-ease-in:      cubic-bezier(0.4, 0, 1, 1);
--windi-ease-out:     cubic-bezier(0, 0, 0.2, 1);
```

### 8.2 Durações

| Tipo | Duração | Uso |
|------|---------|-----|
| **Rápido** | 150ms | Hover states, micro-interactions |
| **Normal** | 300ms | Transições de cor, opacidade |
| **Lento** | 500ms | Entrada/saída de painéis |

### 8.3 Regra: Movimento Contido

```
❌ PROIBIDO: Animações > 1000ms
❌ PROIBIDO: Bounce, elastic, spring exagerado
❌ PROIBIDO: Animações em loop infinito (excepto loading)
✅ PERMITIDO: Ease suave, transições funcionais
```

---

## 9. O Que Este Design System NÃO Decide

- ❌ Arquitectura de componentes (React/Vue/Svelte)
- ❌ Build tools (Vite/Webpack/esbuild)
- ❌ CSS methodology (BEM/Tailwind/CSS Modules)
- ❌ Layout específico de páginas

Este design system decide **apenas** a linguagem visual canónica.
Implementação técnica é responsabilidade de cada produto.

---

## 10. Genealogia

```
§273 Direito Memorial (fundamento)
    │
    └── §281 Léxico de Superfície (vocabulário)
            │
            └── §282 WSDL v1.0 (forma visual) ← ESTE
                    │
                    └── §283 UI Berçário (implementação) [PENDING]
```

---

## 11. Frase Canónica (Citável)

> **"Trust by Calmness — A confiança institucional transmite-se pela calma visual,
> não pela efervescência gráfica. O que é sólido não precisa de gritar."**

Esta frase pode ser citada como princípio fundador do design WINDI.

---

*Liga IA+H · Kempten, Bavaria · 19 Mai 2026*
*"O utilizador não vê complexidade. Sente que o sistema é de confiança."*

OM SHANTI

