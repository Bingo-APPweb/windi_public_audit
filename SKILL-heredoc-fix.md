# SKILL — Heredoc Fix para JS/Python no Strato

## O Problema
```bash
# ❌ FALHA — bash interpreta ${} e Math.floor como variáveis
cat >> app.js << 'WALLETJS'
const trust = Math.floor(trust/20)+1;  # Bad substitution!
WALLETJS
```

## A Solução WINDI — sempre python3 r-string
```bash
# ✅ CORRECTO — raw string ignora tudo, zero interferência do shell
python3 -c "
import sys
js = r'''
// JS aqui — Math.floor(), \${template}, tudo literal
const trust = Math.floor(score/20)+1;
const label = \`T\${trust}\`;
'''
sys.stdout.buffer.write(js.encode('utf-8'))
" >> /opt/windi/target/app.js
```

## Regra de Ouro

| Conteúdo a escrever | Método |
|---|---|
| Texto simples, SQL, config | `heredoc << 'EOF'` ✅ |
| JavaScript com `${}` ou Math | `python3 r-string` ✅ |
| Python com f-strings | `python3 r-string` ✅ |
| Qualquer dúvida | `python3 r-string` ✅ |

## Verificação após escrita
```bash
# Confirmar que o JS chegou íntegro
tail -20 /opt/windi/target/app.js
grep -c "Math.floor\|walletLogin\|WM\." /opt/windi/target/app.js
```

## Origem
Descoberto em 17 Mar 2026 durante CORTE 3 do Wallet Gate GEN7.
`Math.floor(trust/20)+1` causou `Bad substitution` no heredoc.
Fix: python3 r-string. Smoke test: 6/3 funções JS detectadas. ✅

---
*WINDI Publishing House — Kempten, Bavaria*
