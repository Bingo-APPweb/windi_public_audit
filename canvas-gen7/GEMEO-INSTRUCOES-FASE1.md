# CANVAS GEN 7 — FASE 1: INSTRUÇÕES PARA O GÊMEO
# Execução cirúrgica no Strato (windi@87.106.29.233)
# Data: 13 Mar 2026

## FICHEIROS DESTA ENTREGA
```
windi-touch.js          → /opt/windi/static/windi-touch.js
canvas-gen7-mobile.css  → inline em index.html (ver passo 2)
canvas-gen7-mobile.js   → inline em index.html (ver passo 3)
desktop-redirect.html   → fragmento para /desktop/ (ver passo 4)
```

---

## PASSO 0 — Backup obrigatório

```bash
# SEMPRE antes de qualquer edit
cp /opt/windi/agent-palette/ui/index.html \
   /opt/windi/backups/canvas-gen6-backup-$(date +%Y%m%d_%H%M%S).html

cp /opt/windi/desktop/frontend/index.html \
   /opt/windi/backups/desktop-gen6-backup-$(date +%Y%m%d_%H%M%S).html

echo "Backups criados"
```

---

## PASSO 1 — Instalar windi-touch.js

```bash
# Já instalado em /opt/windi/static/windi-touch.js
ls -la /opt/windi/static/windi-touch.js
```

---

## PASSO 2 — Injetar CSS mobile no Canvas index.html

Adicionar DENTRO da tag `<style>` existente do index.html,
OU adicionar um novo bloco `<style>` no `<head>`, DEPOIS dos
estilos existentes:

```html
<!-- Canvas Gen 7 — Mobile Fase 1 -->
<style>
[CONTEÚDO COMPLETO DE canvas-gen7-mobile.css AQUI]
</style>
```

**Comando para verificar onde injetar:**
```bash
grep -n "</style>" /opt/windi/agent-palette/ui/index.html | tail -5
# Injetar antes do último </style> do <head>
```

---

## PASSO 3 — Injetar JS mobile no Canvas index.html

Adicionar o conteúdo de `canvas-gen7-mobile.js` ANTES do
`</body>` tag no index.html:

```html
<!-- Canvas Gen 7 — Mobile Fase 1 -->
<script>
[CONTEÚDO COMPLETO DE canvas-gen7-mobile.js AQUI]
</script>
</body>
```

**Verificar ID real do canvas no Gen 6:**
```bash
grep -n 'id="canvas' /opt/windi/agent-palette/ui/index.html | head -10
grep -n 'data-zone' /opt/windi/agent-palette/ui/index.html | head -10
grep -n 'class="canvas' /opt/windi/agent-palette/ui/index.html | head -10
```

⚠️  Se o ID for diferente de `canvas-area`, actualizar em
    canvas-gen7-mobile.js linha ~12 (getElementById).

---

## PASSO 4 — Redirect /desktop/ → /app/

Adicionar como **PRIMEIRO elemento do `<head>`** em
`/opt/windi/desktop/frontend/index.html`:

```html
<script>
(function() {
  var ua = navigator.userAgent;
  var isMobile = /Mobi|Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(ua)
              || window.innerWidth < 768
              || ('ontouchstart' in window && window.innerWidth < 1024);
  if (isMobile) {
    window.location.replace('https://windi-domain.com/app/?from=desktop');
  }
})();
</script>
```

**Verificar posição actual do head:**
```bash
head -5 /opt/windi/desktop/frontend/index.html
```

---

## PASSO 5 — Adicionar data-zone attributes (se não existirem)

```bash
# Verificar se já existem
grep -c 'data-zone' /opt/windi/agent-palette/ui/index.html
```

Se 0 resultados, o Gêmeo deve identificar os elementos
e adicionar os atributos:
- Canvas principal → `data-zone="G1"`
- Toolbar → `data-zone="G2"`

---

## PASSO 6 — Verificação (READ FIRST protocol)

```bash
# 1. Serviço ainda running?
ss -tlnp | grep 8108

# 2. Status
curl -s -o /dev/null -w "%{http_code}" http://localhost:8108/app/

# 3. Verificar que HTML contém os novos blocos
grep -c "Gen 7" /opt/windi/agent-palette/ui/index.html

# 4. Se Dragon :8108 precisa restart (só se necessário)
# systemctl restart windi-dragon  ← ou o nome do serviço correto
```

---

## PASSO 7 — Teste no browser

1. **Desktop Chrome** (≥1200px) — comportamento Gen 6 preservado
2. **Chrome DevTools → Mobile (375px)** — bottom bar visível
3. **Pinch simulado** (DevTools touch simulation) — zoom funciona
4. **Navegar para /desktop/ no mobile** → redirect para /app/?from=desktop
5. **Mensagem contextual** aparece por 4 segundos

---

## CHECKLIST FASE 1

```
□ windi-touch.js copiado para /opt/windi/static/
□ CSS mobile injetado no Canvas index.html
□ JS mobile injetado no Canvas index.html
□ data-zone G1/G2 presentes no HTML
□ Redirect /desktop/ activo
□ :8108/app/ retorna 200
□ Desktop: comportamento Gen 6 intacto
□ Mobile: bottom bar visível em 375px
□ Pinch-to-zoom funcional (DevTools)
□ Double-tap → reset zoom
□ Long press → (a implementar na Fase 2)
□ /desktop/ → redirect para /app/ em mobile
```

---

## NOTAS ARQUITECTURAIS

- O CSS usa `windi-touch` class (adicionada pelo WindiTouch.init())
  para separar regras touch vs mouse.
- `env(safe-area-inset-bottom)` garante compatibilidade com
  iPhone com notch/Dynamic Island.
- `overscroll-behavior: none` previne o pull-to-refresh do browser
  que conflituaria com o drag do canvas.
- A Fase 2 (G3+G4 bottom sheets) é INDEPENDENTE desta Fase 1.
  Fase 1 pode ir a produção imediatamente.

---

*Canvas Gen 7 — Fase 1 — Human Dragon + Architect — 13 Mar 2026*
