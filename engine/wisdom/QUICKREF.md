# 🛡️ WINDI Wisdom Protocol v0.1 — Quick Reference

## Instalação no Strato

```bash
# 1. Copiar ficheiros para o servidor
scp schema.py wisdom_block_manager.py install_wisdom_v01.sh windi@87.106.29.233:/tmp/

# 2. No servidor
ssh windi@87.106.29.233
cd /tmp && bash install_wisdom_v01.sh
```

## Comandos Diários

```bash
WM="python3 /opt/windi/engine/wisdom/wisdom_block_manager.py"

# Criar candidato durante sessão
$WM create --session "sessao-XYZ" --chamber pattern \
    --essence "A frase destilada aqui" \
    --tags "tag1,tag2" --situation design --actors "guardian,architect"

# Ver dashboard
$WM list
$WM list --status candidate    # só pendentes

# Simular tempo (sem daemon)
$WM tick --minutes 360         # 6 horas

# Decisão I1 (soberania humana)
$WM decide <ficheiro.json> --action approve --category KNOW \
    --n1 governance --n2 principles --n4 validated --n5 internal
$WM decide <ficheiro.json> --action defer
$WM decide <ficheiro.json> --action reject --rejection-class noise

# Info do protocolo
$WM info
```

## Shelf Coordinates (N1-N5)

| N | Dimensão   | Valores |
|---|-----------|---------|
| 1 | Domain    | governance, infrastructure, legal-compliance, security-risk, operations, human-factors, philosophy-ethics, culture-language, manifest-ledger |
| 2 | SubDomain | (livre — ex: guiding-principles, architecture, ...) |
| 3 | Context   | crisis, audit, design, conflict, milestone, operational, strategic, discovery |
| 4 | Maturity  | seed → validated → canonical → legacy |
| 5 | Visibility| public, internal, restricted, guardian-only |

## TTL por Câmara

| Câmara    | TTL Default | Uso |
|-----------|------------|-----|
| echo      | 90 min     | Reacção imediata |
| pattern   | 6 horas    | Ciclo de trabalho |
| archetype | 24 horas   | Sedimentação profunda |

## Ledger

O manager tenta POST para `localhost:8101` (Ledger) → fallback `localhost:8106` (Vault).
Se ambos falharem, selagem local continua normalmente.

Para adaptar: `WISDOM_LEDGER_URL=http://... python3 wisdom_block_manager.py ...`

---
*"AI processes. Human decides. WINDI guarantees." 🐉🛡️*
