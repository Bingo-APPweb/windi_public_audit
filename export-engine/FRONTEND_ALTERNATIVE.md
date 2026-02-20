# ═══════════════════════════════════════════════════════════
# ALTERNATIVA RÁPIDA: Fix no Frontend (D1 React)
# ═══════════════════════════════════════════════════════════
#
# Se o frontend está a enviar editor.getJSON() para o Export Engine,
# a forma MAIS SIMPLES de corrigir pode ser enviar editor.getHTML()
# ou editor.getText() em vez disso.
#
# ═══════════════════════════════════════════════════════════

## Opção A: Frontend envia HTML em vez de JSON para export

Procurar no código React do D1 (provavelmente em src/ ou components/)
a chamada de export ao port 8103.

```bash
# Encontrar a chamada de export no frontend:
cd /opt/windi/desktop/  # ou onde estiver o D1 source
grep -rn "8103\|export\|Exportieren\|governance.*pdf\|M3" src/ --include="*.jsx" --include="*.tsx" --include="*.js" --include="*.ts" | head -20
```

Deve haver algo como:

```javascript
// ANTES (envia JSON bruto):
const content = editor.getJSON();
// ou
const content = JSON.stringify(editor.getJSON());

fetch('/export/api/generate-pdf', {
  method: 'POST',
  body: JSON.stringify({ content: content, ... })
})
```

Mudar para:

```javascript
// DEPOIS (envia HTML renderizado):
const contentHtml = editor.getHTML();
const contentText = editor.getText();

fetch('/export/api/generate-pdf', {
  method: 'POST',
  body: JSON.stringify({ 
    content: contentHtml,      // para renderização visual
    content_text: contentText,  // texto puro como fallback
    content_json: editor.getJSON(), // manter para hash/integridade
    ...rest
  })
})
```

## Opção B: Backend parser (RECOMENDADO ✅)

Usar o tiptap_parser.py no Export Engine é mais robusto porque:
1. O hash SHA-256 é calculado sobre o JSON canônico (não muda)
2. O Export Engine controla a renderização de forma centralizada
3. Não precisa rebuild do frontend React

## DECISÃO RECOMENDADA

→ **Opção B (backend parser)** para produção
→ **Opção A (frontend getHTML)** se quiser fix em 2 minutos

Ambas funcionam. A Opção B é mais "WINDI way" — separação de concerns:
- Frontend: edição + hash + integridade
- Export Engine: renderização + selo + PDF

═══════════════════════════════════════════════════════════
